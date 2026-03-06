# check the metadata with exiftool

import subprocess
import json
from pathlib import Path

def normalize_to_lang_map(value):
    if value is None or value == "":
        return None
    if isinstance(value, list):
        vals = [str(v) for v in value if v not in (None, "")]
        return {"en": vals} if vals else None
    return {"en": [str(value)]}

def exiftool_json(image_path: Path) -> dict:
    proc = subprocess.run(
        ["C:\\Program Files\\exiftool\\exiftool.exe", "-j", "-G1", "-a", "-s", str(image_path)],
        capture_output=True,
        text=True,
        check=True
    )
    print("STDERR:", proc.stderr)
    print("RAW STDOUT:", proc.stdout)
    data = json.loads(proc.stdout)
    return data[0] if data else {}

def build_metadata_block(image_path: Path) -> list[dict]:
    meta = exiftool_json(image_path)

    wanted = [
        ("dc:title", ["XMP-dc:Title", "IPTC:ObjectName", "Title", "EXIF:ImageDescription"]),
        ("dc:creator", ["XMP-dc:Creator", "Creator", "EXIF:Artist"]),
        ("dc:description", ["XMP-dc:Description", "Description", "EXIF:ImageDescription"]),
        ("xmpRights:Marked", ["XMP-xmpRights:Marked", "Marked"]),
        ("xmpRights:UsageTerms", ["XMP-xmpRights:UsageTerms", "UsageTerms"]),
        ("photoshop:Credit", ["XMP-photoshop:Credit", "IPTC:Credit", "Credit"]),
        ("dc:source", ["XMP-dc:Source", "Source"]),
    ]

    out = []
    for iiif_label, candidates in wanted:
        found = None
        for key in candidates:
            if key in meta and meta[key] not in (None, "", []):
                found = meta[key]
                break
        lang_map = normalize_to_lang_map(found)
        if lang_map:
            out.append({
                "label": {"en": [iiif_label]},
                "value": lang_map
            })
    return out

out = build_metadata_block(Path("C:/Users/TH282424/Rprojects/iramat-dev/doc/projects/_pci-archaeology_journal/BIB 3974/IMG_20191114_123131_th1.jpg"))
print(out)