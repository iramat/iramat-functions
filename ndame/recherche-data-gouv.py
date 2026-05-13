import requests
import pandas as pd

BASE = "https://entrepot.recherche.data.gouv.fr"
DATAVERSE = "ndame_GTMetal_fer"

def extract_keywords(item):
    fields = (
        item.get("metadataBlocks", {})
            .get("citation", {})
            .get("fields", [])
    )

    keywords = []

    for field in fields:
        if field.get("typeName") == "keyword":
            for kw in field.get("value", []):
                value = kw.get("keywordValue", {}).get("value")
                if value:
                    keywords.append(value)

    return keywords

rows = []
start = 0
per_page = 100

while True:
    params = {
        "q": "*",
        "type": "dataset",
        "subtree": DATAVERSE,
        "per_page": per_page,
        "start": start,
        "metadata_fields": "citation:*",
    }

    r = requests.get(f"{BASE}/api/search", params=params, timeout=30)
    r.raise_for_status()
    data = r.json()["data"]

    for item in data["items"]:
        rows.append({
            "title": item.get("name"),
            "doi": item.get("global_id"),
            "url": item.get("url"),
            "keywords": "; ".join(extract_keywords(item)),
        })

    start += per_page
    if start >= data["total_count"]:
        break

df = pd.DataFrame(rows)
df.to_csv("./ndame/ndame_GTMetal_fer_titles_keywords.csv", index=False, encoding="utf-8-sig")

print(df.head())
print(f"Exported {len(df)} datasets")