import base64, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")

# each entry: (template filename, output filename)
PAGES = [
    ("exhibit-built-to-protect-template.html", "exhibit-built-to-protect.html"),
    ("site-home-template.html", "site-home.html"),
    ("site-writing-template.html", "site-writing.html"),
]

tokens = {
    "__IMG_HERO_WIDE__": "hero-wide.jpg",
    "__IMG_WIDE2__": "wide2.jpg",
    "__IMG_JACKET__": "jacket.jpg",
    "__IMG_JACKET_PANEL__": "jacket-panel.jpg",
    "__IMG_GEARCHANGE_PANEL__": "gearchange-panel.jpg",
    "__IMG_FIRES_PANEL__": "panel-fires.jpg",
    "__IMG_SMOKE_PANEL__": "panel-smoke.jpg",
    "__IMG_OSHA_PANEL__": "panel-osha.jpg",
    "__IMG_WOMEN_PANEL__": "panel-women.jpg",
    "__IMG_HELMET__": "helmet.jpg",
    "__IMG_MASK__": "mask.jpg",
    "__IMG_CLOSING_WIDE__": "closing.jpg",
    "__IMG_PROCESS_SKETCH__": "process-sketch.jpg",
    "__IMG_PROCESS_PLAN__": "process-plan.jpg",
    "__IMG_PROCESS_PROTOTYPE__": "process-prototype.jpg",
    "__IMG_DFM_MAP__": "dfm-map.jpg",
    "__IMG_STD_HERO__": "std-hero.jpg",
    "__IMG_STD_FOXSISTERS__": "std-foxsisters.jpg",
    "__IMG_STD_PARLOR__": "std-parlor.jpg",
    "__IMG_STD_WOMANLY__": "std-womanly.jpg",
    "__IMG_STD_CHANNELING__": "std-channeling.jpg",
    "__IMG_STD_APPROPRIATION__": "std-appropriation.jpg",
    "__IMG_STD_GRAPH1__": "std-graph1.jpg",
    "__IMG_STD_GRAPH2__": "std-graph2.jpg",
    "__IMG_STD_MAP__": "std-map.jpg",
    "__IMG_STD_SANKEY__": "std-sankey.jpg",
    "__IMG_STD_SWIPE__": "std-swipe.jpg",
}

url_tokens = {
    "__HOME_URL__": "https://claude.ai/code/artifact/c01b7fd9-133c-439b-9ed7-63da494cf53d",
    "__EXHIBIT_URL__": "https://claude.ai/code/artifact/dce235ce-8627-4e0d-a727-7d1e906e2ee9",
    "__WRITING_URL__": "https://claude.ai/code/artifact/f6812eb5-add0-47ce-8e7c-01241eda484c",
    "__CONTACT_FORM_ACTION__": "https://formspree.io/f/xaqrneny",
}

# cache base64 data URIs across pages so multi-page runs don't re-encode the same file twice
_data_uri_cache = {}
def data_uri_for(filename):
    if filename not in _data_uri_cache:
        path = os.path.join(IMG, filename)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as imgf:
            b64 = base64.b64encode(imgf.read()).decode("ascii")
        _data_uri_cache[filename] = f"data:image/jpeg;base64,{b64}"
    return _data_uri_cache[filename]

for template_name, out_name in PAGES:
    template_path = os.path.join(HERE, template_name)
    out_path = os.path.join(HERE, out_name)

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    print(f"\n=== {template_name} -> {out_name} ===")

    missing = []
    for token, filename in tokens.items():
        count = html.count(token)
        if count == 0:
            continue
        uri = data_uri_for(filename)
        if uri is None:
            missing.append(filename)
            continue
        html = html.replace(token, uri)
        print(f"{token}: {filename} -> {count} occurrence(s)")

    if missing:
        print("MISSING FILES:", missing)

    for token, url in url_tokens.items():
        count = html.count(token)
        if count:
            html = html.replace(token, url)
            print(f"{token}: {count} occurrence(s)")

    remaining = set(m.group(0) for m in re.finditer(r"__[A-Z0-9_]+__", html))
    if remaining:
        print("UNRESOLVED TOKENS REMAIN:", remaining)
    else:
        print("All tokens resolved.")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print("Wrote", out_path, "-", os.path.getsize(out_path), "bytes")
