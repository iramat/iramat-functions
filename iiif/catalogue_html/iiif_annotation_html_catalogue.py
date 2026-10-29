#!/usr/bin/env python3
"""Build category-grouped HTML pages from OSD comparison viewers and IIIF annotations.

Requires: pip install requests
Example:
  python3 iiif_annotation_html_catalogue.py /home/ubuntu/iiif-data/viewer/_test/barre531_compare.html -o /home/ubuntu/web/catalogue
  python3 iiif_annotation_html_catalogue.py /home/ubuntu/iiif-data/viewer/_test/barre531_compare.html /home/ubuntu/iiif-data/viewer/_test/barre532_compare.html -o /home/ubuntu/web/catalogue
  python3 iiif_annotation_html_catalogue.py --directory /home/ubuntu/iiif-data/viewer/_test -o /home/ubuntu/web/catalogue
"""
import argparse
import hashlib
import html
import json
import logging
import math
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

import requests

LOG = logging.getLogger("iiif-catalogue")
DEFAULT_ORIGIN = "https://iramat-apps.cnrs.fr"


def js_value(text, variable):
    """Extract a JSON-compatible JS string or array literal from a const declaration."""
    m = re.search(r"\b(?:const|let|var)\s+" + re.escape(variable) + r"\s*=\s*", text)
    if not m:
        raise ValueError(f"Missing JavaScript variable: {variable}")
    pos = m.end()
    while pos < len(text) and text[pos].isspace():
        pos += 1
    if pos >= len(text) or text[pos] not in '[\"\'':
        raise ValueError(f"Unsupported {variable} literal; use a quoted string or array")
    if text[pos] in '\"\'':
        q = text[pos]
        match = re.match(r"([\"'])(.*?)(?<!\\)\1", text[pos:], re.S)
        if not match:
            raise ValueError(f"Malformed {variable} string")
        return match.group(2)
    depth, in_string, escape = 0, None, False
    for end in range(pos, len(text)):
        c = text[end]
        if in_string:
            if escape:
                escape = False
            elif c == '\\':
                escape = True
            elif c == in_string:
                in_string = None
        elif c in '\"\'':
            in_string = c
        elif c == '[':
            depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0:
                raw = text[pos:end + 1]
                raw = re.sub(r",\s*]", "]", raw)
                raw = re.sub(r"'([^'\\]*(?:\\.[^'\\]*)*)'", lambda m: json.dumps(m.group(1)), raw)
                return json.loads(raw)
    raise ValueError(f"Unterminated {variable} array")


def fetch_json(session, url, local_annotation_root=None):
    if local_annotation_root:
        parsed = urlsplit(url)
        prefix = '/iiif/annotation/'
        if parsed.path.startswith(prefix):
            local = Path(local_annotation_root) / unquote(parsed.path[len(prefix):])
            if local.is_file():
                return json.loads(local.read_text(encoding='utf-8'))
    r = session.get(url, timeout=45)
    r.raise_for_status()
    return r.json()


def body_text(annotation):
    bodies = annotation.get('body', [])
    if isinstance(bodies, dict):
        bodies = [bodies]
    parts = [str(b['value']) for b in bodies if isinstance(b, dict) and b.get('type') == 'TextualBody' and b.get('value')]
    return '\n'.join(parts).strip()


def plain_text(value):
    value = re.sub(r'<[^>]*>', ' ', value)
    return html.unescape(re.sub(r'\s+', ' ', value)).strip()


def annotation_region(annotation):
    target = annotation.get('target', {})
    if isinstance(target, str):
        raw = target.split('#', 1)[-1]
    else:
        selectors = target.get('selector', [])
        if isinstance(selectors, dict):
            selectors = [selectors]
        selector = next((s for s in selectors if s.get('type') == 'FragmentSelector'), None)
        if selector is None:
            raise ValueError('No FragmentSelector')
        raw = selector['value']
    m = re.search(r'(?:^|[&#])xywh=(?:pixel:)?([\d.]+),([\d.]+),([\d.]+),([\d.]+)', raw)
    if not m:
        raise ValueError(f'Unsupported xywh selector: {raw}')
    x, y, w, h = map(float, m.groups())
    if not all(math.isfinite(n) for n in (x, y, w, h)) or w <= 0 or h <= 0:
        raise ValueError('Invalid rectangle')
    return x, y, w, h


def service_url(info_url):
    parsed = urlsplit(info_url)
    if not parsed.path.endswith('/info.json'):
        raise ValueError(f'Not an IIIF info.json URL: {info_url}')
    return info_url.split('?', 1)[0][:-len('/info.json')]


def image_filename(info_url):
    return unquote(urlsplit(service_url(info_url)).path.rsplit('/', 1)[-1])


def make_region(xywh, base_size, target_size):
    x, y, w, h = xywh
    sx, sy = target_size[0] / base_size[0], target_size[1] / base_size[1]
    x0, y0 = max(0, math.floor(x * sx)), max(0, math.floor(y * sy))
    x1, y1 = min(target_size[0], math.ceil((x + w) * sx)), min(target_size[1], math.ceil((y + h) * sy))
    if x1 <= x0 or y1 <= y0:
        raise ValueError('Annotation lies outside the image')
    return f'{x0},{y0},{x1-x0},{y1-y0}'


def slug(text):
    import unicodedata
    normal = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', normal).strip('-')[:70] or 'untitled'


def esc(text):
    return html.escape(str(text), quote=True)


def document(title, contents):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><style>
:root {{ color-scheme: light; }} body {{font: 16px/1.55 system-ui,sans-serif;max-width:1200px;margin:2rem auto;padding:0 1rem;color:#20252b}}
a {{color:#075da6}} h1 {{line-height:1.2}} article {{border-top:1px solid #ddd;padding:1.5rem 0}}
.grid {{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem}}
figure {{margin:0;border:1px solid #ddd;border-radius:8px;padding:.75rem;min-width:0}}
figure img {{width:100%;height:240px;object-fit:contain;background:#f4f4f4}}
figcaption {{overflow-wrap:anywhere;font-size:.9rem}} .muted {{color:#626971}} code {{overflow-wrap:anywhere}}
</style></head><body>{contents}</body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('viewers', nargs='*', type=Path, help='HTML viewer paths')
    parser.add_argument('--directory', type=Path, help='Discover *_compare.html recursively')
    parser.add_argument('--annotation-root', type=Path, default=Path('/home/ubuntu/iiif-data/annotations'), help='Local annotation JSON root; HTTP fallback')
    parser.add_argument('--origin', default=DEFAULT_ORIGIN, help='Origin for relative annotation URLs')
    parser.add_argument('-o', '--output', type=Path, default=Path('iiif_annotation_catalogue_html'))
    parser.add_argument('--download', action='store_true', help='Save crop JPEGs locally instead of hotlinking IIIF URLs')
    args = parser.parse_args()
    paths = set(args.viewers)
    if args.directory:
        paths.update(args.directory.rglob('*_compare.html'))
    if not paths:
        parser.error('Supply viewer HTML files or --directory')
    args.output.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers['User-Agent'] = 'IRAMAT-IIIF-catalogue/1.0'
    groups = defaultdict(list)
    size_cache = {}
    for viewer in sorted(paths):
        try:
            source = viewer.read_text(encoding='utf-8')
            sources = js_value(source, 'imageSources')
            ann_url = urljoin(args.origin, js_value(source, 'annotationUrl'))
            if not isinstance(sources, list) or not sources:
                raise ValueError('imageSources must be a nonempty array')
            page = fetch_json(session, ann_url, args.annotation_root)
            if page.get('type') != 'AnnotationPage':
                raise ValueError('Annotation URL does not return an AnnotationPage')
            for url in sources:
                if url not in size_cache:
                    info = fetch_json(session, url)
                    size_cache[url] = (int(info['width']), int(info['height']))
            base_size = size_cache[sources[0]]
            for annotation in page.get('items', []):
                try:
                    xywh = annotation_region(annotation)
                    content = body_text(annotation)
                    category = plain_text(content) or 'Untitled annotation'
                    # A category is the complete plain-text annotation content by default.
                    crops = []
                    for layer_index, url in enumerate(sources, start=1):
                        region = make_region(xywh, base_size, size_cache[url])
                        crop_url = f'{service_url(url)}/{region}/full/0/default.jpg'
                        crops.append({'index': layer_index, 'filename': image_filename(url), 'url': crop_url, 'region': region})
                    groups[category].append({'viewer': viewer.name, 'id': annotation.get('id', ''), 'content': content, 'xywh': xywh, 'crops': crops})
                except (ValueError, KeyError, TypeError) as e:
                    LOG.warning('Skipping annotation %s in %s: %s', annotation.get('id'), viewer, e)
        except (OSError, ValueError, KeyError, requests.RequestException) as e:
            LOG.error('Skipping viewer %s: %s', viewer, e)
    links = []
    for category, records in sorted(groups.items()):
        filename = f'{slug(category)}-{hashlib.sha1(category.encode()).hexdigest()[:8]}.html'
        links.append((category, filename, len(records)))
        sections = [f'<p><a href="index.html">← All categories</a></p><h1>{esc(category)}</h1><p>{len(records)} annotation(s)</p>']
        for rec in records:
            figures = []
            for crop in rec['crops']:
                src = crop['url']
                if args.download:
                    folder = args.output / 'crops'
                    folder.mkdir(exist_ok=True)
                    local_name = hashlib.sha256(src.encode()).hexdigest()[:20] + '.jpg'
                    path = folder / local_name
                    try:
                        if not path.exists():
                            response = session.get(src, timeout=120)
                            response.raise_for_status()
                            path.write_bytes(response.content)
                        src = 'crops/' + local_name
                    except requests.RequestException as e:
                        LOG.warning('Crop download failed %s: %s', src, e)
                figures.append(f'<figure><a href="{esc(crop["url"])}" target="_blank" rel="noopener"><img loading="lazy" src="{esc(src)}" alt="Layer {crop["index"]} crop"></a><figcaption><b>Layer {crop["index"]}: {esc(crop["filename"])}</b><br><span class="muted">xywh={esc(crop["region"])}</span></figcaption></figure>')
            # Display content safely as text; do not inject annotation HTML into generated page.
            sections.append(f'<article><h2>{esc(rec["viewer"])}</h2><p>{esc(rec["content"])}</p><p class="muted">Annotation ID: <code>{esc(rec["id"])}</code><br>Base xywh: <code>{esc(",".join(map(str, rec["xywh"])))}</code></p><div class="grid">{"".join(figures)}</div></article>')
        (args.output / filename).write_text(document(category, '\n'.join(sections)), encoding='utf-8')
    index = '<h1>IIIF Annotation Catalogue</h1><p>Categories grouped by annotation text.</p><ul>' + ''.join(f'<li><a href="{esc(name)}">{esc(category)}</a> ({count})</li>' for category, name, count in links) + '</ul>'
    (args.output / 'index.html').write_text(document('IIIF Annotation Catalogue', index), encoding='utf-8')
    print(f'Created {len(links)} category page(s) in {args.output.resolve()}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    main()
