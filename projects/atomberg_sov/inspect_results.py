# import json

# with open("overall_sov.json", "r", encoding="utf-8") as f:
#     overall = json.load(f)

# print("=== Overall SoV ===")
# for brand, m in overall["metrics"].items():
#     print(f"\nBrand: {brand.upper()}")
#     print(f"  Posts with brand:          {m['posts_with_brand']}")
#     print(f"  SoV (content):             {m['sov_content']:.2%}")
#     print(f"  SoV (engagement):          {m['sov_engagement']:.2%}")
#     print(f"  Share of positive voice:   {m['share_of_positive_voice']:.2%}")


import json
import pandas as pd


def load_overall_df(path: str = "overall_sov.json") -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        overall = json.load(f)

    rows = []
    for brand, m in overall["metrics"].items():
        rows.append({
            "brand": brand,
            "posts_with_brand": m["posts_with_brand"],
            "sov_content": m["sov_content"],
            "sov_engagement": m["sov_engagement"],
            "sov_comments": m["sov_comments"],
            "share_of_positive_voice": m["share_of_positive_voice"],
        })
    df = pd.DataFrame(rows)
    df["brand"] = df["brand"].str.capitalize()
    return df


if __name__ == "__main__":
    df = load_overall_df()
    print(df.to_string(index=False))
