# import json

# with open("sov_by_keyword.json", "r", encoding="utf-8") as f:
#     by_kw = json.load(f)

# for kw, res in by_kw.items():
#     print(f"\n=== Keyword: {kw} ===")
#     for brand, m in res["metrics"].items():
#         if m["posts_with_brand"] == 0:
#             continue
#         print(
#             f"  {brand.upper():8s} | "
#             f"content: {m['sov_content']:.2%} | "
#             f"engagement: {m['sov_engagement']:.2%} | "
#             f"SoPV: {m['share_of_positive_voice']:.2%}"
#         )


import json
import pandas as pd


def load_sov_by_keyword_df(path: str = "sov_by_keyword.json") -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        by_kw = json.load(f)

    rows = []
    for kw, data in by_kw.items():
        for brand, m in data["metrics"].items():
            rows.append({
                "keyword": kw,
                "brand": brand.capitalize(),
                "posts_with_brand": m["posts_with_brand"],
                "sov_content": m["sov_content"],
                "sov_engagement": m["sov_engagement"],
                "sov_comments": m["sov_comments"],
                "share_of_positive_voice": m["share_of_positive_voice"],
            })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = load_sov_by_keyword_df()
    print(df.to_string(index=False))
