#!/usr/bin/env python3
"""Build the CHIPS bibliography HTML from urls_data.tsv and PostgreSQL.

The script:
1. downloads urls_data.tsv;
2. extracts bibliography IDs from the ``bibreference_num`` column;
3. reads matching rows from ``public.literature`` in PostgreSQL;
4. formats and sorts the references;
5. writes ``static/data/references_bib.html`` for inclusion by Hugo.

Run with:
    python3 chips_build_references_bib.py
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import re
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import requests


DEFAULT_TSV_URL = (
    "https://raw.githubusercontent.com/iramat/chips/refs/heads/"
    "hugo-files/static/data/urls_data.tsv"
)
DEFAULT_CREDENTIALS_PG = Path(
    r"C:\Users\TH282424\Rprojects\iramat-dev\credentials\pg_chips_d_credentials.json"
)
DEFAULT_OUTPUT = Path(
    r"C:\Users\TH282424\Rprojects\chips\static\data\references_bib.html"
)

# Accepted examples:
#   ch.bibreference = 1
#   ch.bibreference >= 20 AND ch.bibreference <= 71
SINGLE_ID_RE = re.compile(
    r"^\s*ch\.bibreference\s*=\s*(\d+)\s*$",
    flags=re.IGNORECASE,
)
RANGE_ID_RE = re.compile(
    r"^\s*ch\.bibreference\s*>=\s*(\d+)\s+AND\s+"
    r"ch\.bibreference\s*<=\s*(\d+)\s*$",
    flags=re.IGNORECASE,
)


class BibliographyError(RuntimeError):
    """Raised when bibliography generation cannot continue safely."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create references_bib.html from CHIPS TSV and PostgreSQL."
    )
    parser.add_argument(
        "--tsv-url",
        default=DEFAULT_TSV_URL,
        help=f"Source TSV URL (default: {DEFAULT_TSV_URL})",
    )
    parser.add_argument(
        "--pg-credentials",
        type=Path,
        default=DEFAULT_CREDENTIALS_PG,
        help=f"PostgreSQL credentials JSON (default: {DEFAULT_CREDENTIALS_PG})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output HTML file (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when a non-empty bibreference_num expression is unsupported.",
    )
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        default="INFO",
    )
    return parser.parse_args()


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def load_pg_credentials(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            credentials = json.load(handle)
    except FileNotFoundError as exc:
        raise BibliographyError(f"Credentials file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BibliographyError(f"Invalid JSON in credentials file: {path}") from exc
    except OSError as exc:
        raise BibliographyError(f"Cannot read credentials file {path}: {exc}") from exc

    required = {"dbname", "user", "password", "host", "port"}
    missing = sorted(key for key in required if credentials.get(key) in (None, ""))
    if missing:
        raise BibliographyError(
            f"Credentials file {path} is missing: {', '.join(missing)}"
        )

    try:
        credentials["port"] = int(credentials["port"])
    except (TypeError, ValueError) as exc:
        raise BibliographyError(
            f"The PostgreSQL port must be an integer: {credentials.get('port')!r}"
        ) from exc

    # Only pass known connection keys to psycopg2.
    return {key: credentials[key] for key in required}


def download_urls_data(tsv_url: str) -> pd.DataFrame:
    try:
        response = requests.get(tsv_url, timeout=(15, 120))
        response.raise_for_status()
    except requests.RequestException as exc:
        raise BibliographyError(f"Cannot download {tsv_url}: {exc}") from exc

    try:
        frame = pd.read_csv(
            pd.io.common.StringIO(response.text),
            sep="\t",
            dtype="string",
        )
    except Exception as exc:
        raise BibliographyError(f"Cannot parse TSV from {tsv_url}: {exc}") from exc

    if "bibreference_num" not in frame.columns:
        raise BibliographyError(
            "The TSV does not contain the required 'bibreference_num' column."
        )

    return frame


def ids_from_expression(expression: str) -> set[int]:
    """Extract IDs from one supported bibreference_num expression."""
    single_match = SINGLE_ID_RE.fullmatch(expression)
    if single_match:
        return {int(single_match.group(1))}

    range_match = RANGE_ID_RE.fullmatch(expression)
    if range_match:
        start = int(range_match.group(1))
        end = int(range_match.group(2))
        if start > end:
            raise BibliographyError(
                f"Invalid descending bibliography range: {expression!r}"
            )
        return set(range(start, end + 1))

    raise ValueError(f"Unsupported bibreference_num expression: {expression!r}")


def collect_bibliography_ids(
    values: Iterable[Any],
    *,
    strict: bool = False,
) -> list[int]:
    ids: set[int] = set()

    for raw_value in values:
        expression = clean_text(raw_value)
        if not expression or expression.casefold() in {"none", "null", "nan", "<na>"}:
            continue

        try:
            ids.update(ids_from_expression(expression))
        except ValueError as exc:
            if strict:
                raise BibliographyError(str(exc)) from exc
            logging.warning("%s; ignoring it", exc)

    if not ids:
        raise BibliographyError("No bibliography IDs were extracted from the TSV.")

    return sorted(ids)


def fetch_literature_rows(
    credentials: dict[str, Any],
    bibliography_ids: list[int],
) -> list[dict[str, Any]]:
    query = """
        SELECT
            id_lit,
            authors,
            pub_year,
            title,
            journal_book,
            volume,
            url
        FROM public.literature
        WHERE id_lit = ANY(%s)
        ORDER BY
            lower(COALESCE(authors::text, '')),
            pub_year NULLS LAST,
            lower(COALESCE(title::text, '')),
            id_lit
    """

    try:
        with psycopg2.connect(
            **credentials,
            connect_timeout=15,
            application_name="chips_bibliography_export",
        ) as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (bibliography_ids,))
                rows = [dict(row) for row in cursor.fetchall()]
    except psycopg2.Error as exc:
        detail = exc.diag.message_primary if exc.diag else str(exc)
        raise BibliographyError(f"PostgreSQL query failed: {detail}") from exc

    returned_ids = {int(row["id_lit"]) for row in rows}
    missing_ids = sorted(set(bibliography_ids) - returned_ids)
    if missing_ids:
        logging.warning(
            "%d requested id_lit value(s) were not found: %s",
            len(missing_ids),
            ", ".join(map(str, missing_ids)),
        )

    if not rows:
        raise BibliographyError("No matching rows were found in public.literature.")

    return rows


def ensure_terminal_punctuation(value: str) -> str:
    value = value.rstrip()
    if not value:
        return value
    if value[-1] in ".?!":
        return value
    return value + "."


def format_chicago_reference(row: dict[str, Any]) -> str:
    """Format available fields in a Chicago author-date-like bibliography entry."""
    authors = clean_text(row.get("authors")) or "Unknown author"
    year = clean_text(row.get("pub_year")) or "n.d."
    title = clean_text(row.get("title"))
    journal_book = clean_text(row.get("journal_book"))
    volume = clean_text(row.get("volume"))
    url = clean_text(row.get("url"))

    parts = [
        f"{html.escape(authors)}. {html.escape(year)}.",
    ]

    if title:
        parts.append(ensure_terminal_punctuation(f'“{html.escape(title)}”'))

    publication = ""
    if journal_book:
        publication = f"<em>{html.escape(journal_book)}</em>"
    if volume:
        publication += (" " if publication else "") + html.escape(volume)
    if publication:
        parts.append(ensure_terminal_punctuation(publication))

    if url:
        safe_url = html.escape(url, quote=True)
        parts.append(
            f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer">'
            f"{html.escape(url)}</a>."
        )

    return " ".join(parts)


def render_html(rows: list[dict[str, Any]]) -> str:
    entries = "\n".join(
        f'  <li class="chips-bibliography__entry" data-id-lit="{int(row["id_lit"])}">'
        f"{format_chicago_reference(row)}</li>"
        for row in rows
    )

    return f"""<!-- Generated automatically by build_references_bib.py. Do not edit manually. -->
<div class="chips-bibliography" data-citation-style="chicago-author-date">
<ol class="chips-bibliography__list">
{entries}
</ol>
</div>
"""


def write_html(output_path: Path, content: str) -> None:
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8", newline="\n")
    except OSError as exc:
        raise BibliographyError(f"Cannot write {output_path}: {exc}") from exc


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    try:
        urls_data = download_urls_data(args.tsv_url)
        bibliography_ids = collect_bibliography_ids(
            urls_data["bibreference_num"],
            strict=args.strict,
        )
        logging.info(
            "Extracted %d distinct bibliography IDs from the TSV",
            len(bibliography_ids),
        )

        credentials = load_pg_credentials(args.pg_credentials)
        rows = fetch_literature_rows(credentials, bibliography_ids)
        logging.info("Retrieved %d bibliography rows from PostgreSQL", len(rows))

        write_html(args.output, render_html(rows))
        logging.info("Wrote bibliography HTML to %s", args.output)
        return 0

    except BibliographyError as exc:
        logging.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
