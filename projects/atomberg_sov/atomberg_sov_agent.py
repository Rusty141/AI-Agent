import os
import re
import json
import asyncio
from collections import defaultdict
from typing import List, Dict, Any, Tuple

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# GitHub Models client from the course stack
from autogen_core.models import UserMessage, SystemMessage
from autogen_ext.models.azure import AzureAIChatCompletionClient
from azure.core.credentials import AzureKeyCredential


# =========================
# 1. Load environment vars
# =========================

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
if not YOUTUBE_API_KEY:
    raise RuntimeError("YOUTUBE_API_KEY not found in .env")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise RuntimeError("GITHUB_TOKEN not found in .env")


# =========================
# 2. LLM client (GitHub Models)
# =========================

gh_client = AzureAIChatCompletionClient(
    model="gpt-4o-mini",
    endpoint="https://models.inference.ai.azure.com",
    credential=AzureKeyCredential(GITHUB_TOKEN),
    model_info={
        "json_output": False,
        "function_calling": False,
        "vision": False,
        "family": "unknown",
    },
)


# =========================
# 3. Config
# =========================

# Keywords chosen to cover multiple intents around smart fans
KEYWORDS = [
    "smart fan",
    "bldc fan",
    "smart ceiling fan",
    "energy saving fan",
]

# Top N videos per keyword
N_YOUTUBE = 30

# Brand dictionary – extend if you want more competitors
BRANDS: Dict[str, List[str]] = {
    "atomberg": ["atomberg", "atom berg"],
    "havells": ["havells"],
    "crompton": ["crompton"],
    "orient": ["orient", "orient electric"],
    "usha": ["usha"],
    "bajaj": ["bajaj"],
    "luminous": ["luminous"],
}

# Simple lexicon-based sentiment (for comments)
POSITIVE_WORDS = [
    "good", "great", "love", "awesome", "amazing", "best", "excellent",
    "efficient", "silent", "quiet", "worth", "recommended", "happy",
    "satisfied", "energy saving", "saves electricity",
]
NEGATIVE_WORDS = [
    "bad", "worst", "hate", "problem", "issues", "noisy", "noise",
    "disappointed", "waste", "poor", "slow", "not good", "not worth",
]


# =========================
# 4. Tool 1 – YouTube ingestion
# =========================

class YouTubeTool:
    """
    Tool: fetch and structure YouTube data (videos + comments).
    """

    def __init__(self, api_key: str):
        self.youtube = build("youtube", "v3", developerKey=api_key)

    def fetch_comments(self, video_id: str, max_comments: int = 50) -> List[Dict[str, Any]]:
        comments: List[Dict[str, Any]] = []
        next_page_token = None

        while len(comments) < max_comments:
            try:
                response = self.youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=min(50, max_comments - len(comments)),
                    pageToken=next_page_token,
                    textFormat="plainText",
                    order="relevance",
                ).execute()
            except HttpError as e:
                # Comments disabled or restricted for some videos
                print(f"  Skipping comments for video {video_id}: {e}")
                break

            for item in response.get("items", []):
                top = item["snippet"]["topLevelComment"]["snippet"]
                comments.append(
                    {
                        "text": top.get("textDisplay", ""),
                        "like_count": int(top.get("likeCount", 0)),
                    }
                )

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        return comments

    def search_youtube(self, keyword: str, max_results: int = N_YOUTUBE) -> List[Dict[str, Any]]:
        """
        Search + hydrate YouTube videos with statistics and a sample of comments.
        Each returned dict is a self-contained "document" for later analysis.
        """
        # 1. Search for videos
        search_response = self.youtube.search().list(
            q=keyword,
            part="id",
            type="video",
            maxResults=max_results,
        ).execute()

        video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
        if not video_ids:
            return []

        # 2. Get video details
        videos_response = self.youtube.videos().list(
            id=",".join(video_ids),
            part="snippet,statistics",
        ).execute()

        records: List[Dict[str, Any]] = []

        for item in videos_response.get("items", []):
            vid = item["id"]
            snippet = item["snippet"]
            stats = item.get("statistics", {})

            title = snippet.get("title", "")
            description = snippet.get("description", "")
            channel = snippet.get("channelTitle", "")

            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments_count = int(stats.get("commentCount", 0))

            # 3. Fetch top-level comments (limited)
            comments = self.fetch_comments(vid, max_comments=50)

            records.append(
                {
                    "platform": "youtube",
                    "keyword": keyword,
                    "video_id": vid,
                    "title": title,
                    "description": description,
                    "channel": channel,
                    "views": views,
                    "likes": likes,
                    "comments_count": comments_count,
                    "comments": comments,
                }
            )

        return records


# =========================
# 5. Tool 2 – Brand detection + sentiment
# =========================

class BrandSentimentTool:
    """
    Tool: detect brand mentions and compute a light sentiment score.
    """

    def __init__(self, brands: Dict[str, List[str]]):
        self.brands = brands
        self.brand_patterns: Dict[str, List[re.Pattern]] = self._compile_patterns(brands)

    @staticmethod
    def _compile_patterns(brands: Dict[str, List[str]]) -> Dict[str, List[re.Pattern]]:
        patterns: Dict[str, List[re.Pattern]] = {}
        for brand, aliases in brands.items():
            patterns[brand] = [
                re.compile(r"\b" + re.escape(alias.lower()) + r"\b", re.IGNORECASE)
                for alias in aliases
            ]
        return patterns

    def detect_brands(self, text: str) -> Dict[str, int]:
        """Count brand alias matches in the given text."""
        text_l = text.lower()
        counts = {b: 0 for b in self.brands}
        for brand, pats in self.brand_patterns.items():
            for pat in pats:
                matches = pat.findall(text_l)
                counts[brand] += len(matches)
        return counts

    @staticmethod
    def sentiment_score(text: str) -> float:
        """
        Simple lexicon-based sentiment.
        Returns a score between -1 (negative) and +1 (positive).
        """
        text_l = text.lower()
        pos = sum(text_l.count(w) for w in POSITIVE_WORDS)
        neg = sum(text_l.count(w) for w in NEGATIVE_WORDS)
        if pos == 0 and neg == 0:
            return 0.0
        return (pos - neg) / max(pos + neg, 1)


# =========================
# 6. Tool 3 – SoV computation (overall + per keyword)
# =========================

class SOVTool:
    """
    Computes:
      - Content SoV (posts mentioning brand)
      - Engagement-weighted SoV
      - Comment-level SoV
      - Share of Positive Voice (SoPV)
    Both overall and per keyword.
    """

    @staticmethod
    def _compute_for_records(
        records: List[Dict[str, Any]],
        brand_tool: BrandSentimentTool,
    ) -> Dict[str, Any]:
        post_mentions = defaultdict(int)
        total_posts_with_any_brand = 0

        engagement_per_brand = defaultdict(float)
        engagement_total = 0.0

        comment_mentions = defaultdict(int)
        positive_voice = defaultdict(float)
        total_positive_voice = 0.0

        for rec in records:
            post_text = f"{rec['title']}\n{rec['description']}"
            brand_counts_post = brand_tool.detect_brands(post_text)

            any_brand_here = any(c > 0 for c in brand_counts_post.values())
            if any_brand_here:
                total_posts_with_any_brand += 1

            # engagement heuristic: views + 10*likes + 20*comment_count
            engagement = rec["views"] + 10 * rec["likes"] + 20 * rec["comments_count"]

            for brand, count in brand_counts_post.items():
                if count > 0:
                    post_mentions[brand] += 1
                    engagement_per_brand[brand] += engagement
                    engagement_total += engagement

            # comment analysis
            for c in rec["comments"]:
                text = c["text"]
                brand_counts_comment = brand_tool.detect_brands(text)
                s = brand_tool.sentiment_score(text)

                for brand, count in brand_counts_comment.items():
                    if count > 0:
                        comment_mentions[brand] += count
                        if s > 0:
                            positive_voice[brand] += s
                            total_positive_voice += s

        brands = list(BRANDS.keys())
        result = {"brands": brands, "metrics": {}}

        for brand in brands:
            # Content SoV
            if total_posts_with_any_brand > 0:
                sov_content = post_mentions[brand] / total_posts_with_any_brand
            else:
                sov_content = 0.0

            # Engagement SoV
            if engagement_total > 0:
                sov_engagement = engagement_per_brand[brand] / engagement_total
            else:
                sov_engagement = 0.0

            # Comment SoV
            total_comment_mentions = sum(comment_mentions.values())
            if total_comment_mentions > 0:
                sov_comments = comment_mentions[brand] / total_comment_mentions
            else:
                sov_comments = 0.0

            # Share of Positive Voice
            if total_positive_voice > 0:
                sopv = positive_voice[brand] / total_positive_voice
            else:
                sopv = 0.0

            result["metrics"][brand] = {
                "posts_with_brand": post_mentions[brand],
                "sov_content": sov_content,
                "sov_engagement": sov_engagement,
                "sov_comments": sov_comments,
                "share_of_positive_voice": sopv,
            }

        return result

    def compute_overall_and_by_keyword(
        self,
        all_records: List[Dict[str, Any]],
        brand_tool: BrandSentimentTool,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Return overall SoV and per-keyword SoV."""
        overall_sov = self._compute_for_records(all_records, brand_tool)

        records_by_keyword: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for rec in all_records:
            records_by_keyword[rec["keyword"]].append(rec)

        sov_by_keyword: Dict[str, Any] = {}
        for kw, recs in records_by_keyword.items():
            sov_by_keyword[kw] = self._compute_for_records(recs, brand_tool)

        return overall_sov, sov_by_keyword


# =========================
# 7. Insight agent – uses LLM
# =========================

class InsightAgent:
    """
    Uses GitHub Models (gpt-4o-mini) to turn SoV metrics into
    human-readable insights and recommendations for Atomberg.
    """

    def __init__(self, client: AzureAIChatCompletionClient):
        self.client = client

    async def generate_insights(
        self,
        overall_sov: Dict[str, Any],
        sov_by_keyword: Dict[str, Any],
    ) -> str:
        payload = {
            "overall": overall_sov,
            "by_keyword": sov_by_keyword,
        }
        metrics_json = json.dumps(payload, indent=2)

        system_text = """
You are a senior marketing analyst for Atomberg, a smart/BLDC fan brand in India.
You are given quantitative Share of Voice (SoV) metrics from YouTube search
results for smart-fan-related keywords.

Your job:
1. Explain what the numbers say about Atomberg vs competitors.
2. Highlight where Atomberg is strong vs weak (content, engagement, comments, sentiment).
3. Use the per-keyword breakdown to identify which search intents Atomberg is winning or losing.
4. Suggest 4–6 concrete content & marketing actions Atomberg should take,
   including at least one related to smart home / WiFi positioning.
        """

        user_text = f"""
Here are the computed metrics as JSON:

{metrics_json}

Fields:
- posts_with_brand: number of videos mentioning the brand in title/description
- sov_content: share of videos mentioning the brand vs other brands
- sov_engagement: share of engagement (views + 10*likes + 20*comments)
- sov_comments: share of comment-level brand mentions
- share_of_positive_voice: share of positive sentiment in comments among all brands

Please:
- Summarize Atomberg's position vs each key competitor.
- Call out differences between keywords (e.g., stronger on "BLDC fan" vs "WiFi ceiling fan").
- Give specific recommendations for YouTube content and broader digital marketing.
"""

        messages = [
            SystemMessage(content=system_text.strip(), source="system"),
            UserMessage(content=user_text.strip(), source="user"),
        ]

        response = await self.client.create(messages=messages)
        return response.content


# =========================
# 8. Orchestrator – the AI agent
# =========================

def main() -> None:
    # 1) Ingest data from YouTube
    yt_tool = YouTubeTool(api_key=YOUTUBE_API_KEY)
    all_records: List[Dict[str, Any]] = []

    for kw in KEYWORDS:
        print(f"\n=== Collecting for keyword: '{kw}' ===")
        recs = yt_tool.search_youtube(kw, max_results=N_YOUTUBE)
        print(f"  Found {len(recs)} videos.")
        all_records.extend(recs)

    print(f"\nTotal videos collected across keywords: {len(all_records)}")

    # Save raw data (useful to show in your submission)
    with open("raw_youtube_records.json", "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)

    # 2) Compute SoV metrics
    brand_tool = BrandSentimentTool(BRANDS)
    sov_tool = SOVTool()
    overall_sov, sov_by_keyword = sov_tool.compute_overall_and_by_keyword(all_records, brand_tool)

    # Save metrics
    with open("overall_sov.json", "w", encoding="utf-8") as f:
        json.dump(overall_sov, f, ensure_ascii=False, indent=2)
    with open("sov_by_keyword.json", "w", encoding="utf-8") as f:
        json.dump(sov_by_keyword, f, ensure_ascii=False, indent=2)

    # Print concise summary to console
    print("\n=== Overall Share of Voice Metrics ===")
    for brand, m in overall_sov["metrics"].items():
        print(f"\nBrand: {brand.upper()}")
        print(f"  Posts with brand:          {m['posts_with_brand']}")
        print(f"  SoV (content):             {m['sov_content']:.2%}")
        print(f"  SoV (engagement-weighted): {m['sov_engagement']:.2%}")
        print(f"  SoV (comments):            {m['sov_comments']:.2%}")
        print(f"  Share of positive voice:   {m['share_of_positive_voice']:.2%}")

    print("\n=== Per-keyword SoV (brownie points) ===")
    for kw, res in sov_by_keyword.items():
        print(f"\nKeyword: '{kw}'")
        for brand, m in res["metrics"].items():
            if m["posts_with_brand"] == 0:
                continue
            print(
                f"  {brand.upper():8s} | "
                f"content: {m['sov_content']:.2%} | "
                f"engagement: {m['sov_engagement']:.2%} | "
                f"SoPV: {m['share_of_positive_voice']:.2%}"
            )

    # 3) LLM-generated insights
    agent = InsightAgent(gh_client)
    print("\n=== AI-Generated Insights & Recommendations ===\n")
    insights = asyncio.run(agent.generate_insights(overall_sov, sov_by_keyword))
    print(insights)


if __name__ == "__main__":
    main()
