#!/usr/bin/env python3
"""Create Zenodo (Zenodo Sandbox by default) deposits for every CHIPS dataset listed in urls_data.tsv.

Examples
--------
Create drafts for all datasets (recommended first run):
    python3 chips_to_zenodo.py

Create and publish all datasets:
    python3 chips_to_zenodo.py --publish
    
Process selected TSV row indices only (1 dataset):
    python3 chips_to_zenodo.py --rows 1 --publish

Process selected TSV row indices only (3 datasets):
    python3 chips_to_zenodo.py --rows 1 4 7 --publish

Retry a dataset that is already recorded in the state file:
    python3 chips_to_zenodo.py --rows 4 --force
"""

from __future__ import annotations

import argparse
import html
import io
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


ZENODO_API = "https://sandbox.zenodo.org/api/deposit/depositions"
# TODO: switch to production Zenodo API when ready:
# ZENODO_API = "https://zenodo.org/api/deposit/depositions"
DEFAULT_CREDENTIALS = Path("/home/ubuntu/zenodo/credentials/zn_sandbox_credentials.json")
DEFAULT_STATE_FILE = Path("/home/ubuntu/zenodo/chips_zenodo_state.json")
DEFAULT_URLS_DATA = (
    "https://raw.githubusercontent.com/iramat/chips/"
    "refs/heads/hugo-files/static/data/urls_data.tsv"
)

BASE_KEYWORDS = [
    "archaeometallurgy",
    "iron archaeometallurgy",
    "archaeomaterials",
    "geochemistry",
    "chemical analysis",
    "elemental composition",
    "analytical metadata",
    "measurement uncertainty",
    "FAIR data",
    "Linked Open Data",
]

SUBJECTS = [
    {
        "term": "Archaeology",
        "identifier": "http://data.europa.eu/bkc/005.05.01.0050",
    },
    {
        "term": "Archaeometry",
        "identifier": (
            "http://data.europa.eu/8mn/euroscivoc/"
            "0b7ef923-ea48-47bd-a5f1-2c5b18f53d20"
        ),
    },
    {
        "term": "Materials science",
        "identifier": "http://data.europa.eu/bkc/018.01.00.0950",
    },
    {
        "term": "Analytical chemistry",
        "identifier": (
            "http://data.europa.eu/8mn/euroscivoc/"
            "dc1b3723-476f-453c-a596-c7ccfde9b4b1"
        ),
    },
    {"term": "Metals", "identifier": "https://id.nlm.nih.gov/mesh/D008670"},
    {"term": "Iron", "identifier": "https://id.nlm.nih.gov/mesh/D007501"},
    {
        "term": "Spectroscopy",
        "identifier": "https://id.nlm.nih.gov/mesh/D013057",
    },
]

REQUIRED_TSV_COLUMNS = {
    "url_data",
    "dataset_name",
    "dataset_num",
    "description_txt",
}


class DatasetError(RuntimeError):
    """Raised when one CHIPS dataset cannot be processed safely."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create Zenodo Sandbox deposits from every CHIPS API dataset."
    )
    parser.add_argument(
        "--credentials",
        type=Path,
        default=DEFAULT_CREDENTIALS,
        help=f"JSON credentials file (default: {DEFAULT_CREDENTIALS})",
    )
    parser.add_argument(
        "--urls-data",
        default=DEFAULT_URLS_DATA,
        help="Local path or URL of urls_data.tsv.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=DEFAULT_STATE_FILE,
        help="JSON file used to avoid creating duplicate deposits.",
    )
    parser.add_argument(
        "--rows",
        type=int,
        nargs="+",
        help="Process only these zero-based TSV row indices.",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Publish each deposit. Without this option, deposits remain drafts.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Process rows even if their dataset names are already in the state file.",
    )
    parser.add_argument(
        "--title-suffix",
        default="",
        help="Optional suffix appended to dataset names in titles and filenames.",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=1.0,
        help="Seconds to wait between datasets (default: 1).",
    )
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        default="INFO",
    )
    return parser.parse_args()


def build_session(token: str) -> requests.Session:
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        status=5,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "PUT", "DELETE"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "User-Agent": "CHIPS-Zenodo-Sandbox-Uploader/1.0",
        }
    )
    return session


def load_token(credentials_path: Path) -> str:
    try:
        with credentials_path.open("r", encoding="utf-8") as handle:
            credentials = json.load(handle)
    except FileNotFoundError as exc:
        raise SystemExit(f"Credentials file not found: {credentials_path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in credentials file: {credentials_path}") from exc

    token = credentials.get("token")
    if not isinstance(token, str) or not token.strip():
        raise SystemExit(
            f"Credentials file must contain a non-empty string field named 'token': "
            f"{credentials_path}"
        )
    return token.strip()


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            state = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read state file {path}: {exc}") from exc
    if not isinstance(state, dict):
        raise SystemExit(f"State file must contain a JSON object: {path}")
    return state


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    temporary.replace(path)


def response_json(response: requests.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError:
        payload = {"raw_response": response.text[:2000]}
    return payload if isinstance(payload, dict) else {"response": payload}


def raise_for_api_error(response: requests.Response, action: str) -> None:
    if response.ok:
        return
    payload = response_json(response)
    raise DatasetError(
        f"{action} failed with HTTP {response.status_code}: "
        f"{json.dumps(payload, ensure_ascii=False)}"
    )


def clean_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def extract_dataset_number(raw_value: Any) -> str:
    value = clean_text(raw_value)
    value = re.sub(r"^j\.id_dataset\s*=\s*", "", value)
    if not value:
        raise DatasetError("Missing dataset_num in urls_data.tsv.")
    return value


def extract_author_part(reference: str) -> str:
    match = re.match(r"^(.*?)\s*\(\d{4}[a-z]?\)", reference)
    if not match:
        raise DatasetError(
            "Could not identify an author list followed by a publication year in "
            f"reference: {reference!r}"
        )
    return match.group(1).strip().rstrip(",")


def split_person_name(full_name: str) -> tuple[str, str]:
    """Convert a simple 'Given Family' string to ('Family', 'Given').

    This preserves the behaviour of the original script. Compound unhyphenated family
    names cannot be inferred reliably from a plain reference string and should be
    corrected upstream if necessary.
    """
    parts = full_name.strip().split()
    if len(parts) < 2:
        raise DatasetError(f"Cannot split author name: {full_name!r}")
    return parts[-1], " ".join(parts[:-1])


def creators_from_reference(reference: str) -> list[dict[str, str]]:
    author_part = extract_author_part(reference)
    names = [name.strip() for name in author_part.split(",") if name.strip()]
    creators: list[dict[str, str]] = []
    for full_name in names:
        family_name, given_names = split_person_name(full_name)
        creators.append({"name": f"{family_name}, {given_names}"})
    if not creators:
        raise DatasetError("No creators could be extracted from the reference.")
    return creators


def unique_method_keywords(frame: pd.DataFrame) -> list[str]:
    columns = [column for column in ("trace_method", "major_method") if column in frame]
    if not columns:
        logging.warning("Neither trace_method nor major_method is present in the API data.")
        return []

    values: list[str] = []
    seen: set[str] = set()
    for value in frame[columns].stack().dropna().astype(str):
        method = value.strip()
        if method and method.casefold() not in seen:
            seen.add(method.casefold())
            if method not in ['Unknown']:
                values.append(method)
    return values


def deduplicate_case_insensitive(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = value.strip()
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def build_description(
    short_description: str,
    dataset_name: str,
    dataset_number: str,
    reference: str,
    publication_url: str,
    api_url: str,
    dashboard_url: str,
) -> str:
    safe_description = html.escape(short_description)
    safe_name = html.escape(dataset_name)
    safe_number = html.escape(dataset_number)
    safe_reference = html.escape(reference)
    safe_publication_url = html.escape(publication_url, quote=True)
    safe_api_url = html.escape(api_url, quote=True)
    safe_dashboard_url = html.escape(dashboard_url, quote=True)

    source_item = safe_reference
    if publication_url:
        source_item += (
            f', <a href="{safe_publication_url}" target="_blank">'
            f"{safe_publication_url}</a>"
        )

    return f"""
<p>{safe_description}</p>

<h2>Source</h2>

<p>The dataset <code>{safe_name}</code> (CHIPS dataset no. {safe_number}) was
first published in:</p>

<ul>
  <li>{source_item}.</li>
</ul>

<p>It was added to the CHIPS database following the
<a href="https://iramat.github.io/chips/docs/#data-entry" target="_blank">CHIPS data entry method</a>. Fields and values are desscribed on the <a href="https://iramat.github.io/chips/docs/#fields-descriptions" target="_blank">CHIPS webstite</a>.</p>


</p>

<h2>Reusability</h2>

<p>The dataset <code>{safe_name}</code> (CHIPS dataset no. {safe_number}) is
made interoperable through the IRAMAT web server:</p>

<ul>
  <li>CHIPS API: <a href="{safe_api_url}" target="_blank">{safe_api_url}</a></li>
  <li>CHIPS dashboard: <a href="{safe_dashboard_url}" target="_blank">{safe_dashboard_url}</a></li>
</ul>
""".strip()


def fetch_dataset(session: requests.Session, api_url: str) -> pd.DataFrame:
    response = session.get(
        api_url,
        headers={"Authorization": None},
        timeout=30,
    )

    raise_for_api_error(response, f"Reading CHIPS API {api_url}")

    records = response.json()

    if not records:
        raise DatasetError(f"The CHIPS API returned no records: {api_url}")

    return pd.DataFrame.from_records(records)


def build_metadata(row: pd.Series, frame: pd.DataFrame, title_suffix: str) -> tuple[dict[str, Any], str]:
    dataset_name = clean_text(row["dataset_name"])
    api_url = clean_text(row["url_data"])
    dataset_number = extract_dataset_number(row["dataset_num"])
    short_description = clean_text(row["description_txt"])

    if not dataset_name or not api_url:
        raise DatasetError("A TSV row has an empty dataset_name or url_data.")

    first_record = frame.iloc[0].to_dict()
    reference = clean_text(first_record.get("reference"))
    publication_url = clean_text(first_record.get("url"))
    if not reference:
        raise DatasetError("The first API record has no usable 'reference' field.")

    creators = creators_from_reference(reference)
    dashboard_url = f"https://iramat-apps.cnrs.fr/dash/mapview?dataset={dataset_name}"

    clean_dataset_name = re.sub(r"^dataset_", "", dataset_name)
    suffixed_name = f"{clean_dataset_name}{title_suffix}"
    title = f"CHIPS dataset {dataset_number} ({suffixed_name})"

    description = build_description(
        short_description=short_description,
        dataset_name=dataset_name,
        dataset_number=dataset_number,
        reference=reference,
        publication_url=publication_url,
        api_url=api_url,
        dashboard_url=dashboard_url,
    )

    keywords = deduplicate_case_insensitive(
        BASE_KEYWORDS + unique_method_keywords(frame)
    )

    zenodo_metadata: dict[str, Any] = {
        "title": title,
        "description": description,
        "upload_type": "dataset",
        "license": "cc-by",
        "subjects": SUBJECTS,
        "creators": creators,
        "keywords": keywords,
    }

    if publication_url:
        zenodo_metadata["related_identifiers"] = [
            {
                "identifier": publication_url,
                "relation": "isSupplementTo",
                "resource_type": "publication-article",
            }
        ]

    filename = f"{suffixed_name}_chips{dataset_number}.csv"
    filename = re.sub(r"[^A-Za-z0-9._-]+", "_", filename)
    return {"metadata": zenodo_metadata}, filename


def create_deposition(session: requests.Session) -> dict[str, Any]:
    response = session.post(
        ZENODO_API,
        json={},
        headers={"Content-Type": "application/json"},
        timeout=(15, 120),
    )
    raise_for_api_error(response, "Creating Zenodo deposition")
    payload = response_json(response)
    if "id" not in payload or "links" not in payload:
        raise DatasetError(f"Unexpected creation response: {payload}")
    return payload


def upload_csv(
    session: requests.Session,
    bucket_url: str,
    filename: str,
    frame: pd.DataFrame,
) -> dict[str, Any]:
    export_frame = frame.drop(columns=["reference", "url"], errors="ignore")

    csv_buffer = io.BytesIO()
    export_frame.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    upload_url = f"{bucket_url.rstrip('/')}/{quote(filename, safe='')}"

    response = session.put(
        upload_url,
        data=csv_buffer,
        headers={"Content-Type": "application/octet-stream"},
        timeout=(15, 300),
    )

    raise_for_api_error(response, f"Uploading {filename}")
    return response_json(response)


def update_metadata(
    session: requests.Session,
    self_url: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    response = session.put(
        self_url,
        json=metadata,
        headers={"Content-Type": "application/json"},
        timeout=(15, 120),
    )
    raise_for_api_error(response, "Updating Zenodo metadata")
    return response_json(response)


def get_deposition(session: requests.Session, self_url: str) -> dict[str, Any]:
    response = session.get(self_url, timeout=(15, 120))
    raise_for_api_error(response, "Checking Zenodo deposition")
    return response_json(response)


def publish_deposition(
    session: requests.Session,
    publish_url: str,
    self_url: str,
) -> dict[str, Any]:
    # POST is not automatically retried: repeating a publish action blindly after a
    # timeout could be ambiguous. Check deposition state before one cautious retry.
    response = session.post(publish_url, timeout=(15, 300))
    if response.ok:
        return response_json(response)

    if response.status_code in {409, 500, 502, 503, 504}:
        logging.warning(
            "Publish returned HTTP %s; checking the deposition state before retrying.",
            response.status_code,
        )
        time.sleep(5)
        status = get_deposition(session, self_url)
        if status.get("submitted") is True or status.get("state") == "done":
            return status

        retry_response = session.post(publish_url, timeout=(15, 300))
        if retry_response.ok:
            return response_json(retry_response)
        response = retry_response

    raise_for_api_error(response, "Publishing Zenodo deposition")
    raise AssertionError("unreachable")


def discard_draft(session: requests.Session, discard_url: str | None) -> None:
    if not discard_url:
        return
    try:
        response = session.post(discard_url, timeout=(15, 120))
        if not response.ok:
            logging.warning(
                "Could not discard failed draft (%s): HTTP %s %s",
                discard_url,
                response.status_code,
                response.text[:500],
            )
    except requests.RequestException as exc:
        logging.warning("Could not discard failed draft %s: %s", discard_url, exc)


def process_dataset(
    session: requests.Session,
    row_index: int,
    row: pd.Series,
    title_suffix: str,
    publish: bool,
) -> dict[str, Any]:
    dataset_name = clean_text(row["dataset_name"])
    api_url = clean_text(row["url_data"])
    logging.info("[%s] Reading %s from %s", row_index, dataset_name, api_url)

    frame = fetch_dataset(session, api_url)
    metadata, filename = build_metadata(row, frame, title_suffix)

    logging.info(
        "[%s] Creating deposit: %s (%s records)",
        row_index,
        metadata["metadata"]["title"],
        len(frame),
    )
    deposition = create_deposition(session)
    links = deposition["links"]

    try:
        upload_csv(session, links["bucket"], filename, frame)
        logging.info("[%s] Uploaded %s", row_index, filename)

        updated = update_metadata(session, links["self"], metadata)
        logging.info("[%s] Metadata added", row_index)

        final = updated
        if publish:
            final = publish_deposition(session, links["publish"], links["self"])
            logging.info("[%s] Deposit published", row_index)
        else:
            logging.info("[%s] Deposit left as a draft", row_index)

        final_links = final.get("links", links)
        return {
            "row_index": row_index,
            "dataset_name": dataset_name,
            "deposition_id": deposition["id"],
            "record_id": final.get("record_id") or deposition.get("record_id"),
            "published": bool(final.get("submitted")) or final.get("state") == "done",
            "html": final_links.get("html") or final_links.get("latest_draft_html"),
            "filename": filename,
            "title": metadata["metadata"]["title"],
        }
    except Exception:
        # Keep failed drafts only when diagnosing manually would be useful. Here we
        # discard them to prevent the bulk loop from leaving incomplete deposits.
        discard_draft(session, links.get("discard"))
        raise


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    token = load_token(args.credentials)
    session = build_session(token)
    state = load_state(args.state_file)

    try:
        urls_data = pd.read_csv(args.urls_data, sep="\t", dtype=str)
    except Exception as exc:
        logging.error("Cannot read urls_data.tsv: %s", exc)
        return 2

    missing = REQUIRED_TSV_COLUMNS.difference(urls_data.columns)
    if missing:
        logging.error("urls_data.tsv is missing required columns: %s", sorted(missing))
        return 2

    if args.rows is not None:
        invalid = [index for index in args.rows if index not in urls_data.index]
        if invalid:
            logging.error("Invalid TSV row indices: %s", invalid)
            return 2
        selected = urls_data.loc[args.rows]
    else:
        selected = urls_data

    success_count = 0
    skipped_count = 0
    failure_count = 0

    for row_index, row in selected.iterrows():
        dataset_name = clean_text(row["dataset_name"])
        state_key = dataset_name or f"row_{row_index}"

        if state_key in state and not args.force:
            logging.info(
                "[%s] Skipping %s: already present in %s (use --force to retry)",
                row_index,
                dataset_name,
                args.state_file,
            )
            skipped_count += 1
            continue

        try:
            result = process_dataset(
                session=session,
                row_index=int(row_index),
                row=row,
                title_suffix=args.title_suffix,
                publish=args.publish,
            )
            state[state_key] = result
            save_state(args.state_file, state)
            success_count += 1
            logging.info("[%s] Zenodo page: %s", row_index, result.get("html"))
        except (DatasetError, requests.RequestException, KeyError, ValueError) as exc:
            failure_count += 1
            logging.exception("[%s] Failed %s: %s", row_index, dataset_name, exc)
        except Exception as exc:  # keep the remaining datasets running
            failure_count += 1
            logging.exception("[%s] Unexpected failure for %s: %s", row_index, dataset_name, exc)

        if args.pause > 0:
            time.sleep(args.pause)

    logging.info(
        "Finished: %s successful, %s skipped, %s failed. State file: %s",
        success_count,
        skipped_count,
        failure_count,
        args.state_file,
    )
    return 1 if failure_count else 0


if __name__ == "__main__":
    sys.exit(main())
