import html
import json
import time
from pathlib import Path
from urllib.parse import urlencode

import networkx as nx
import requests
from pyvis.network import Network


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

BASE = "https://sandbox.zenodo.org"

# Same query as the Zenodo Sandbox search supplied by the user.
QUERY = 'metadata.contributors.person_or_org.name:"Disser, Alexandre"'

PAGE_SIZE = 25 # lmit max
# OUTPUT_HTML = Path("zenodo_diser_2mode_network.html")
OUTPUT_HTML = Path("./zenodo/read_chips_records_in_zenodo.html")



# ---------------------------------------------------------------------
# Zenodo metadata harvesting
# ---------------------------------------------------------------------

def fetch_records():
    """
    Retrieve all Zenodo Sandbox records matching QUERY.

    Zenodo Sandbox currently uses an InvenioRDM-style API response, but
    extract_hits() also accepts the older Zenodo 'hits.hits' representation.
    """
    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "User-Agent": "zenodo-pyvis-network/1.0",
    })

    records = []
    page = 1

    while True:
        params = {
            "q": QUERY,
            "page": page,
            "size": PAGE_SIZE,
            "sort": "newest",
        }

        response = session.get(
            f"{BASE}/api/records",
            params=params,
            timeout=60,
        )
        print(f"GET {response.url}")
        response.raise_for_status()

        payload = response.json()
        hits = extract_hits(payload)

        print(f"Page {page}: {len(hits)} records")
        records.extend(hits)

        if not hits or len(hits) < PAGE_SIZE:
            break

        page += 1
        time.sleep(0.25)

    return records


def extract_hits(payload):
    """Support current and legacy Zenodo search-response shapes."""
    hits = payload.get("hits", {})

    # Current InvenioRDM form:
    # {"hits": {"hits": [...]}}
    if isinstance(hits, dict):
        return hits.get("hits", [])

    # Defensive fallback in case an endpoint directly returns a list.
    if isinstance(hits, list):
        return hits

    return []


# ---------------------------------------------------------------------
# Metadata normalization
# ---------------------------------------------------------------------

def get_record_url(record):
    """Return the public landing-page URL for a Zenodo Sandbox record."""
    links = record.get("links") or {}

    for key in ("self_html", "record_html"):
        if links.get(key):
            return links[key]

    record_id = record.get("id")
    return f"{BASE}/records/{record_id}" if record_id else BASE


def get_doi(record):
    """Return DOI/persistent identifier when available."""
    pids = record.get("pids") or {}

    doi = pids.get("doi")
    if isinstance(doi, dict):
        return str(doi.get("identifier") or "")
    if doi:
        return str(doi)

    metadata = record.get("metadata") or {}
    return str(metadata.get("doi") or record.get("doi") or "")


def get_people(record):
    """
    Return creators/authors as dictionaries:
        {"name": ..., "orcid": ..., "affiliations": [...]}

    Supports both:
      - current InvenioRDM person_or_org metadata;
      - legacy Zenodo creators metadata.
    """
    metadata = record.get("metadata") or {}
    creators = metadata.get("creators") or []
    people = []

    for creator in creators:
        person = creator.get("person_or_org")

        # Current InvenioRDM representation.
        if isinstance(person, dict):
            name = (
                person.get("name")
                or " ".join(
                    x for x in [
                        str(person.get("given_name") or "").strip(),
                        str(person.get("family_name") or "").strip(),
                    ]
                    if x
                )
            ).strip()

            orcid = ""
            for identifier in person.get("identifiers") or []:
                if str(identifier.get("scheme") or "").lower() == "orcid":
                    orcid = str(identifier.get("identifier") or "").strip()
                    break

            affiliations = []
            for affiliation in creator.get("affiliations") or []:
                if isinstance(affiliation, dict):
                    value = affiliation.get("name") or affiliation.get("id")
                else:
                    value = affiliation
                if value:
                    affiliations.append(str(value).strip())

        # Legacy Zenodo representation.
        else:
            name = str(creator.get("name") or "").strip()
            orcid = str(creator.get("orcid") or "").strip()

            affiliation = creator.get("affiliation")
            if isinstance(affiliation, list):
                affiliations = [str(x).strip() for x in affiliation if x]
            elif affiliation:
                affiliations = [str(affiliation).strip()]
            else:
                affiliations = []

        if name:
            people.append({
                "name": name,
                "orcid": normalize_orcid(orcid),
                "affiliations": affiliations,
            })

    return people


def normalize_orcid(value):
    """Normalize either an ORCID ID or an ORCID URL to the bare identifier."""
    value = str(value or "").strip()
    value = value.removeprefix("https://orcid.org/")
    value = value.removeprefix("http://orcid.org/")
    return value.rstrip("/")


def orcid_url(orcid):
    return f"https://orcid.org/{orcid}" if orcid else ""


def zenodo_author_search_url(name):
    """Return the Zenodo Sandbox search page filtered on one creator name."""
    query = f'metadata.creators.person_or_org.name:"{name}"'
    params = {
        "q": query,
        "l": "list",
        "p": 1,
        "s": 10,
        "sort": "bestmatch",
    }
    return f"{BASE}/search?{urlencode(params)}"


# ---------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------

def build_graph(records):
    """
    Build a bipartite / 2-mode graph:
      author <---- authored ----> publication
    """
    graph = nx.Graph()

    for record in records:
        metadata = record.get("metadata") or {}
        title = str(metadata.get("title") or "Untitled record").strip()
        record_id = str(record.get("id") or title)
        record_url = get_record_url(record)
        doi = get_doi(record)

        publication_id = f"publication::{record_id}"

        publication_tooltip = (
            f"<b>{html.escape(title)}</b><br>"
            f"Zenodo record: {html.escape(record_id)}"
        )
        if doi:
            publication_tooltip += f"<br>DOI: {html.escape(doi)}"
        publication_tooltip += (
            f'<br><a href="{html.escape(record_url)}" '
            f'target="_blank">Lien Zenodo</a>'
        )

        graph.add_node(
            publication_id,
            label=title,
            node_type="publication",
            url=record_url,
            title=publication_tooltip,
        )

        for person in get_people(record):
            name = person["name"]
            orcid = person["orcid"]

            # Prefer ORCID as the stable node identity when available.
            # Otherwise use the person's normalized name.
            person_key = f"orcid::{orcid}" if orcid else f"name::{name.casefold()}"
            author_id = f"author::{person_key}"
            author_url = orcid_url(orcid)
            author_zenodo_url = zenodo_author_search_url(name)

            tooltip = f"<b>{html.escape(name)}</b>"
            # if person["affiliations"]:
            #     tooltip += (
            #         "<br>Affiliation: "
            #         + html.escape("; ".join(person["affiliations"]))
            #     )
            # if orcid:
            #     tooltip += f"<br>ORCID: {html.escape(orcid)}"
            #     tooltip += (
            #         f'<br><a href="{html.escape(author_url)}" '
            #         f'target="_blank">Open ORCID</a>'
            #     )

            tooltip += (
                f'<br><a href="{html.escape(author_zenodo_url)}" '
                f'target="_blank">Lien Zenodo</a>'
            )

            graph.add_node(
                author_id,
                label=name,
                node_type="author",
                url=author_url,
                zenodo_url=author_zenodo_url,
                title=tooltip,
                orcid=orcid,
            )

            graph.add_edge(
                author_id,
                publication_id,
                relation="author of",
            )

    return graph


def wrap_label(text, max_chars=24):
    """Wrap long labels for a more compact network display."""
    words = str(text).split()
    lines = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > max_chars:
            lines.append(current)
            current = word
        else:
            current = candidate

    if current:
        lines.append(current)

    return "\n".join(lines)


# ---------------------------------------------------------------------
# PyVis HTML export
# ---------------------------------------------------------------------

def export_html(graph):
    net = Network(
        height="900px",
        width="100%",
        bgcolor="#ffffff",
        font_color="#222222",
        notebook=False,
        cdn_resources="in_line",
    )

    for node_id, attrs in graph.nodes(data=True):
        node_type = attrs["node_type"]

        if node_type == "author":
            color = "#8ecae6"
            shape = "dot"
            size = 18
        else:
            color = "#ffb703"
            shape = "box"
            size = 22

        net.add_node(
            node_id,
            label=wrap_label(attrs["label"]),
            title=attrs.get("title", ""),
            url=attrs.get("url", ""),
            color=color,
            shape=shape,
            size=size,
        )

    for source, target, attrs in graph.edges(data=True):
        net.add_edge(
            source,
            target,
            title=attrs.get("relation", ""),
            width=1,
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
        "color": {
          "inherit": true
        }
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
          "gravitationalConstant": -90,
          "centralGravity": 0.01,
          "springLength": 160,
          "springConstant": 0.03,
          "damping": 0.75,
          "avoidOverlap": 0.8
        },
        "stabilization": {
          "enabled": true,
          "iterations": 1200,
          "fit": true
        }
      }
    }
    """)

    html_content = net.generate_html(notebook=False)

    # PyVis/vis-network nodes carry a `url` property. Double-clicking:
    #   - a publication opens its Zenodo Sandbox record;
    #   - an author opens ORCID, when an ORCID exists.
    click_script = """
    <script>
    network.on("doubleClick", function(params) {
      if (params.nodes.length > 0) {
        var nodeId = params.nodes[0];
        var node = nodes.get(nodeId);
        if (node.url) {
          window.open(node.url, "_blank", "noopener,noreferrer");
        }
      }
    });
    </script>
    """

    html_content = html_content.replace(
        "</body>",
        click_script + "\n</body>",
    )

    OUTPUT_HTML.write_text(html_content, encoding="utf-8")


def main():
    records = fetch_records()

    if not records:
        print("No records matched the Zenodo query.")
        return

    graph = build_graph(records)
    export_html(graph)

    n_authors = sum(
        1 for _, attrs in graph.nodes(data=True)
        if attrs["node_type"] == "author"
    )
    n_publications = sum(
        1 for _, attrs in graph.nodes(data=True)
        if attrs["node_type"] == "publication"
    )

    print()
    print(f"Records retrieved: {len(records)}")
    print(f"Publication nodes: {n_publications}")
    print(f"Author nodes: {n_authors}")
    print(f"Edges: {graph.number_of_edges()}")
    print(f"HTML graph: {OUTPUT_HTML.resolve()}")


if __name__ == "__main__":
    main()
