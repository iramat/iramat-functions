import html
import requests
import pandas as pd
import networkx as nx
from pyvis.network import Network

BASE = "https://entrepot.recherche.data.gouv.fr"
DATAVERSE = "ndame_GTMetal_fer"

OUTPUT_CSV = "./ndame/ndame_GTMetal_fer_titles_authors_keywords.csv"
OUTPUT_HTML = "./ndame/ndame_GTMetal_fer_3mode_network.html"


def get_citation_fields(item):
    return (
        item.get("metadataBlocks", {})
        .get("citation", {})
        .get("fields", [])
    )


def extract_keywords(item):
    keywords = []

    for field in get_citation_fields(item):
        if field.get("typeName") == "keyword":
            for kw in field.get("value", []):
                value = kw.get("keywordValue", {}).get("value")
                if value:
                    keywords.append(value.strip())

    return keywords


def extract_authors(item):
    authors = []

    for field in get_citation_fields(item):
        if field.get("typeName") == "author":
            for author in field.get("value", []):
                name = author.get("authorName", {}).get("value")
                if name:
                    authors.append(name.strip())

    return authors

def clean_title(title):
    title = title.replace("Données archéométriques ", "").strip()
    title = title.replace("du ", "").strip()
    title = title.replace("de l’", "").strip()
    title = title.replace("de l'", "").strip()
    title = title.replace("de la ", "").strip()
    return title.replace(" de Notre-Dame de Paris", "").strip()


def wrap_label(text, max_chars=14):
    words = str(text).split()
    lines = []
    current = ""

    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current = f"{current} {word}".strip()
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return "\n".join(lines)

def fetch_datasets():
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

        r = requests.get(f"{BASE}/api/search", params=params, timeout=60)
        r.raise_for_status()
        data = r.json()["data"]

        for item in data["items"]:
            title = clean_title(item.get("name", "").strip())
            doi = item.get("global_id", "")
            url = item.get("url", "")

            authors = extract_authors(item)
            keywords = extract_keywords(item)

            rows.append({
                "title": title,
                "doi": doi,
                "url": url,
                "authors": "; ".join(authors),
                "keywords": "; ".join(keywords),
            })

        start += per_page
        if start >= data["total_count"]:
            break

    return pd.DataFrame(rows)


def split_semicolon(value):
    if pd.isna(value) or not value:
        return []

    return [
        x.strip()
        for x in str(value).split(";")
        if x.strip()
    ]


def build_graph(df):
    G = nx.Graph()

    for _, row in df.iterrows():
        title = row["title"]
        url = row["url"]
        doi = row["doi"]

        title_id = f"title::{title}"

        G.add_node(
            title_id,
            label=title,
            node_type="title",
            url=url,
            title=f"""
            <b>{html.escape(title)}</b><br>
            DOI: {html.escape(doi)}<br>
            <a href="{html.escape(url)}" target="_blank">Open dataset</a>
            """
        )

        for author in split_semicolon(row["authors"]):
            author_id = f"author::{author}"
            G.add_node(
                author_id,
                label=author,
                node_type="author",
                title=f"Author: {html.escape(author)}"
            )
            G.add_edge(author_id, title_id, relation="authored")

        for keyword in split_semicolon(row["keywords"]):
            keyword_id = f"keyword::{keyword}"
            G.add_node(
                keyword_id,
                label=keyword,
                node_type="keyword",
                title=f"Keyword: {html.escape(keyword)}"
            )
            G.add_edge(title_id, keyword_id, relation="has keyword")

    return G


def export_html(G):
    net = Network(
        height="900px",
        width="100%",
        bgcolor="#ffffff",
        font_color="#222222",
        notebook=False,
        cdn_resources="in_line"
    )

    # net.force_atlas_2based(
    #     gravity=-50,
    #     central_gravity=0.01,
    #     spring_length=120,
    #     spring_strength=0.08,
    #     damping=0.4
    # )

    colors = {
        "author": "#8ecae6",
        "title": "#ffb703",
        "keyword": "#90be6d",
    }

    shapes = {
        "author": "dot",
        "title": "box",
        "keyword": "ellipse",
    }

    for node_id, attrs in G.nodes(data=True):
        node_type = attrs.get("node_type", "unknown")

        net.add_node(
            node_id,
            label=wrap_label(attrs.get("label", node_id), 14),
            title=attrs.get("title", ""),
            color=colors.get(node_type, "#cccccc"),
            shape=shapes.get(node_type, "dot"),
            url=attrs.get("url", ""),
            size=18 if node_type == "title" else 12,
        )

    for source, target, attrs in G.edges(data=True):
        net.add_edge(
            source,
            target,
            title=attrs.get("relation", ""),
        )

    net.set_options("""
	{
	"nodes": {
		"font": {
		"size": 14,
		"face": "Arial",
		"multi": true
		}
	},
	"edges": {
		"smooth": false,
		"width": 0.5
	},
	"interaction": {
		"hover": true,
		"navigationButtons": true,
		"keyboard": true
	},
	"physics": {
		"enabled": true,
		"solver": "forceAtlas2Based",
		"forceAtlas2Based": {
		"gravitationalConstant": -120,
		"centralGravity": 0.01,
		"springLength": 180,
		"springConstant": 0.02,
		"damping": 0.85,
		"avoidOverlap": 1
		},
		"minVelocity": 0.75,
		"maxVelocity": 30,
		"stabilization": {
		"enabled": true,
		"iterations": 1500,
		"updateInterval": 50,
		"onlyDynamicEdges": false,
		"fit": true
		}
	}
	}
	""")

    html_content = net.generate_html(notebook=False)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
      f.write(html_content)

    # Add click behavior: title nodes open their dataset URL.
    with open(OUTPUT_HTML, "r", encoding="utf-8") as f:
        html_content = f.read()

    click_script = """
    <script>
    network.on("doubleClick", function(params) {
      if (params.nodes.length > 0) {
        var nodeId = params.nodes[0];
        var node = nodes.get(nodeId);
        if (node.url) {
          window.open(node.url, "_blank");
        }
      }
    });
    </script>
    """

    html_content = html_content.replace("</body>", click_script + "\n</body>")

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)


def main():
    df = fetch_datasets()
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    G = build_graph(df)
    export_html(G)

    print(f"Exported CSV: {OUTPUT_CSV}")
    print(f"Exported HTML graph: {OUTPUT_HTML}")
    print(f"Datasets: {len(df)}")
    print(f"Nodes: {G.number_of_nodes()}")
    print(f"Edges: {G.number_of_edges()}")


if __name__ == "__main__":
    main()