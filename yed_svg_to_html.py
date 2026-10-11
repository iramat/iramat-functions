#!/usr/bin/env python3
"""Convert a yEd SVG export into a standalone interactive HTML page.

Usage:
    python yed_svg_to_html.py diagram.svg
    python yed_svg_to_html.py diagram.svg -o index.html --title 'CHIPS workflow'

The diagram and hyperlinks are embedded. The svg-pan-zoom JavaScript library
is loaded from a CDN (internet required for zoom/pan).
"""
import argparse
import html
import re
from pathlib import Path

LIBRARY = "https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.2/dist/svg-pan-zoom.min.js"


def convert(source: Path, destination: Path, title: str) -> int:
    svg = source.read_text(encoding="utf-8-sig")
    svg = re.sub(r"^\s*<\?xml[^>]*\?>", "", svg, count=1)
    svg = re.sub(r"<!DOCTYPE[^>]*>", "", svg, count=1)
    root = re.search(r"<svg\b[^>]*>", svg)
    if not root:
        raise ValueError("No SVG root element found")
    tag = root.group(0)
    width = re.search(r'\bwidth="([\d.]+)(?:px)?"', tag)
    height = re.search(r'\bheight="([\d.]+)(?:px)?"', tag)
    if not re.search(r'\bviewBox\s*=', tag):
        if not width or not height:
            raise ValueError("SVG needs a viewBox or numeric width and height")
        tag = tag[:-1] + f' viewBox="0 0 {width.group(1)} {height.group(1)}">'
    tag = re.sub(r'\bwidth="[^"]*"', 'width="100%"', tag, count=1)
    tag = re.sub(r'\bheight="[^"]*"', 'height="100%"', tag, count=1)
    tag = tag[:-1] + ' id="workflow-svg">'
    svg = svg[:root.start()] + tag + svg[root.end():]

    # Set the destination for each SVG anchor; preserve its original href.
    count = 0
    def fix_link(match):
        nonlocal count
        tag = match.group(0)
        if not re.search(r'(?:xlink:)?href\s*=', tag):
            return tag
        count += 1
        tag = re.sub(r'\s+target="[^"]*"', '', tag)
        tag = re.sub(r'\s+rel="[^"]*"', '', tag)
        return tag[:-1] + ' target="_blank" rel="noopener noreferrer">'
    svg = re.sub(r'<a\b[^>]*>', fix_link, svg)

    # Keep <defs> outside the viewport, so clip paths and gradients remain intact.
    opening_end = svg.index('>', svg.index('<svg')) + 1
    defs = re.match(r'\s*(?:<!--.*?-->\s*)?<defs\b[^>]*(?:/>|>.*?</defs>)',
                    svg[opening_end:], re.DOTALL)
    insert_at = opening_end + defs.end() if defs else opening_end
    svg = svg[:insert_at] + '\n<g class="svg-pan-zoom_viewport">' + svg[insert_at:]
    svg = re.sub(r'</svg>\s*$', '</g>\n</svg>', svg)

    page = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<script src="__LIBRARY__"></script>
<style>
html,body{margin:0;width:100%;height:100%;overflow:hidden;font-family:system-ui,Arial,sans-serif;background:#f6f7f9}
#diagram{width:100vw;height:100vh}
#workflow-svg{display:block;width:100%;height:100%}
#workflow-svg a{cursor:pointer}
#workflow-svg a:hover{opacity:.8}
.controls{position:fixed;top:16px;right:16px;z-index:10;display:flex;gap:6px;padding:8px;border-radius:10px;background:#fffffff0;box-shadow:0 2px 12px #0002}
button{padding:8px 12px;background:white;border:1px solid #ccd2d9;border-radius:6px;font:inherit;cursor:pointer}
button:hover{background:#e8f1ff}
.hint{position:fixed;bottom:12px;left:50%;transform:translateX(-50%);background:#fffffff0;padding:6px 12px;border-radius:8px;color:#4a5568;font-size:12px;pointer-events:none}
</style>
</head>
<body>
<nav class="controls" aria-label="Diagram controls">
<button id="zoom-in" title="Zoom in">+</button>
<button id="zoom-out" title="Zoom out">−</button>
<button id="reset" title="Fit entire diagram">Fit / reset</button>
</nav>
<div id="diagram">__SVG__</div>
<div class="hint">Scroll to zoom · Drag to pan · Click a component to open its link</div>
<script>
const viewer = svgPanZoom(document.getElementById('workflow-svg'), {
  viewportSelector: '.svg-pan-zoom_viewport',
  panEnabled: true, zoomEnabled: true, mouseWheelZoomEnabled: true,
  dblClickZoomEnabled: false, controlIconsEnabled: false,
  fit: true, center: true, minZoom: 0.15, maxZoom: 20,
  zoomScaleSensitivity: 0.22
});
function fitDiagram(){viewer.resize();viewer.fit();viewer.center();}
document.getElementById('zoom-in').addEventListener('click',()=>viewer.zoomIn());
document.getElementById('zoom-out').addEventListener('click',()=>viewer.zoomOut());
document.getElementById('reset').addEventListener('click',fitDiagram);
window.addEventListener('resize',fitDiagram);
</script>
</body>
</html>'''
    page = page.replace('__TITLE__', html.escape(title)).replace('__LIBRARY__', LIBRARY).replace('__SVG__', svg)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(page, encoding='utf-8')
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('svg', type=Path, help='SVG exported from yEd')
    parser.add_argument('-o', '--output', type=Path, help='HTML output path')
    parser.add_argument('--title', default='Interactive workflow', help='HTML page title')
    args = parser.parse_args()
    output = args.output or args.svg.with_suffix('.html')
    links = convert(args.svg, output, args.title)
    print(f'Created: {output} ({links} hyperlink elements)')


if __name__ == '__main__':
    main()
