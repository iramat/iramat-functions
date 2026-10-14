#!/usr/bin/env python3
"""Create a self-contained zoomable HTML landing page from a yEd SVG export.

Usage: 

python yed_svg_to_html_fixed.py diagram.svg -o index.html --title 'IRAMAT workflow'
python yed_svg_to_html.py C:\Users\TH282424\Rprojects\iramat-dev\img\erd_workflow_general.svg -o iramat_workflow_interactive.html --title 'IT workflow'  

No third-party dependencies or CDN needed.
"""
import argparse
import html
import re
from pathlib import Path
from xml.etree import ElementTree as ET

SVG_NS = 'http://www.w3.org/2000/svg'
XLINK_NS = 'http://www.w3.org/1999/xlink'


def convert(source: Path, destination: Path, title: str) -> int:
    svg = source.read_text(encoding='utf-8-sig')
    svg = re.sub(r'^\s*<\?xml[^>]*\?>', '', svg, count=1)
    svg = re.sub(r'<!DOCTYPE[^>]*(?:\[[\s\S]*?\]\s*)?>', '', svg, count=1)
    # Use an XML parser to validate, but preserve the original yEd SVG text,
    # including its namespace prefixes, scripts, and embedded images.
    root = ET.fromstring(svg)
    if root.tag != '{%s}svg' % SVG_NS:
        raise ValueError('Input must be an SVG file')
    links = sum(1 for e in root.iter() if e.tag == '{%s}a' % SVG_NS and (e.get('href') or e.get('{%s}href' % XLINK_NS)))
    match = re.search(r'<svg\b[^>]*>', svg)
    if not match:
        raise ValueError('SVG root tag not found')
    opening = match.group(0)
    vb = re.search(r'\bviewBox\s*=\s*["\']([^"\']+)', opening)
    if vb:
        vals = [float(v) for v in re.split(r'[\s,]+', vb.group(1).strip())]
    else:
        def dimension(name):
            m = re.search(r'\b' + name + r'\s*=\s*["\']([\d.]+)(?:px)?["\']', opening)
            if not m:
                raise ValueError('SVG needs viewBox or numeric width/height')
            return float(m.group(1))
        vals = [0., 0., dimension('width'), dimension('height')]
        opening = opening[:-1] + ' viewBox="{}">'.format(' '.join(map(str, vals)))
    if len(vals) != 4 or vals[2] <= 0 or vals[3] <= 0:
        raise ValueError('Invalid SVG viewBox')
    opening = re.sub(r'\bwidth\s*=\s*["\'][^"\']*["\']', 'width="100%"', opening, count=1)
    opening = re.sub(r'\bheight\s*=\s*["\'][^"\']*["\']', 'height="100%"', opening, count=1)
    opening = re.sub(r'\s+id\s*=\s*["\'][^"\']*["\']', '', opening)
    opening = opening[:-1] + ' id="workflow-svg" preserveAspectRatio="xMidYMid meet">'
    svg = svg[:match.start()] + opening + svg[match.end():]
    # Only change opening anchor tags; do not alter embedded image xlink:href.
    def link_target(m):
        tag = m.group(0)
        if not re.search(r'(?:xlink:)?href\s*=', tag):
            return tag
        tag = re.sub(r'\s+(?:target|rel)\s*=\s*(["\']).*?\1', '', tag)
        return tag[:-1] + ' target="_blank" rel="noopener noreferrer">'
    svg = re.sub(r'<a\b[^>]*>', link_target, svg)
    # Avoid a literal closing script tag within the HTML template JS.
    page = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
html,body{margin:0;width:100%;height:100%;overflow:hidden;font-family:system-ui,Arial,sans-serif;background:#f7f8fa}
#diagram{width:100vw;height:100dvh;overflow:hidden;touch-action:none}
#workflow-svg{display:block;width:100%;height:100%;user-select:none;touch-action:none}
#workflow-svg a{cursor:pointer}
.controls{position:fixed;top:16px;right:16px;z-index:10;display:flex;gap:6px;padding:8px;border-radius:10px;background:#ffffffed;box-shadow:0 2px 12px #0002}
button{padding:8px 12px;background:white;border:1px solid #ccd2d9;border-radius:6px;font:inherit;cursor:pointer}
button:hover{background:#e8f1ff}
.hint{position:fixed;bottom:12px;left:50%;transform:translateX(-50%);background:#fffffff0;padding:6px 12px;border-radius:8px;color:#4a5568;font-size:12px;pointer-events:none;text-align:center}
</style>
</head>
<body>
<nav class="controls" aria-label="Diagram controls">
<button type="button" id="zoom-in" title="Zoom in">+</button>
<button type="button" id="zoom-out" title="Zoom out">−</button>
<button type="button" id="reset" title="Fit entire diagram">Fit / reset</button>
</nav>
<div id="diagram">__SVG__</div>
<div class="hint">Wheel: zoom · Drag empty space: pan · Click linked components: open page</div>
<script>
(() => {
'use strict';
const svg = document.getElementById('workflow-svg');
const initial = svg.viewBox.baseVal;
const original = {x:initial.x, y:initial.y, width:initial.width, height:initial.height};
let view = {...original};
const MIN_FACTOR = 0.05, MAX_FACTOR = 20;
function render(){ svg.setAttribute('viewBox', `${view.x} ${view.y} ${view.width} ${view.height}`); }
function reset(){ view = {...original}; render(); }
function screenToSvg(clientX,clientY){
  const p = svg.createSVGPoint(); p.x=clientX; p.y=clientY;
  const matrix=svg.getScreenCTM();
  return matrix ? p.matrixTransform(matrix.inverse()) : {x:view.x+view.width/2,y:view.y+view.height/2};
}
function zoom(factor,clientX,clientY){
  const oldW=view.width, oldH=view.height;
  const newW=oldW/factor, newH=oldH/factor;
  const scale=original.width/newW;
  if(scale<MIN_FACTOR || scale>MAX_FACTOR) return;
  const before=screenToSvg(clientX,clientY);
  view.x=before.x-(before.x-view.x)*(newW/oldW);
  view.y=before.y-(before.y-view.y)*(newH/oldH);
  view.width=newW; view.height=newH; render();
}
function centerZoom(factor){const r=svg.getBoundingClientRect();zoom(factor,r.left+r.width/2,r.top+r.height/2);}
document.getElementById('zoom-in').addEventListener('click',()=>centerZoom(1.3));
document.getElementById('zoom-out').addEventListener('click',()=>centerZoom(1/1.3));
document.getElementById('reset').addEventListener('click',reset);
svg.addEventListener('wheel',e=>{
  e.preventDefault(); zoom(Math.exp(-e.deltaY*0.0015),e.clientX,e.clientY);
},{passive:false});
let drag=null, dragged=false;
svg.addEventListener('pointerdown',e=>{
  if(e.button!==0 || e.target.closest('a')) return;
  drag={id:e.pointerId,x:e.clientX,y:e.clientY,view:{...view}};
  dragged=false;
  svg.setPointerCapture(e.pointerId);
});
svg.addEventListener('pointermove',e=>{
  if(!drag || e.pointerId!==drag.id) return;
  const rect=svg.getBoundingClientRect();
  const aspect=view.width/view.height, boxAspect=rect.width/rect.height;
  const unitsPerPixel=aspect>boxAspect ? drag.view.width/rect.width : drag.view.height/rect.height;
  const dx=e.clientX-drag.x, dy=e.clientY-drag.y;
  if(Math.abs(dx)+Math.abs(dy)>3) dragged=true;
  view.x=drag.view.x-dx*unitsPerPixel;
  view.y=drag.view.y-dy*unitsPerPixel;
  render();
});
function stop(e){if(drag && e.pointerId===drag.id)drag=null;}
svg.addEventListener('pointerup',stop);
svg.addEventListener('pointercancel',stop);
svg.addEventListener('lostpointercapture',()=>{drag=null;});
reset();
})();
</script>
</body>
</html>'''
    page = page.replace('__TITLE__', html.escape(title)).replace('__SVG__', svg)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(page, encoding='utf-8')
    return links


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('svg',type=Path)
    parser.add_argument('-o','--output',type=Path)
    parser.add_argument('--title',default='Interactive workflow')
    args=parser.parse_args()
    output=args.output or args.svg.with_suffix('.html')
    n=convert(args.svg,output,args.title)
    print(f'Created: {output} ({n} hyperlink elements)')

if __name__=='__main__':
    main()
