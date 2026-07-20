import os, re, shutil, base64

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_SRC = os.path.join(HERE, "img")
REPO_ROOT = os.path.dirname(HERE)
DOCS = os.path.join(REPO_ROOT, "docs")
DOCS_IMG = os.path.join(DOCS, "img")

# each entry: (template filename, output filename)
# clean page names for the real site -- index.html is required for the root URL
PAGES = [
    ("exhibit-built-to-protect-template.html", "exhibits.html"),
    ("site-home-template.html", "index.html"),
    ("site-writing-template.html", "writing.html"),
]

# same image tokens as inject.py, but resolved to relative file paths instead of base64
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

# this is a <username>.github.io user-site repo, so it serves at the domain root
# (not /reponame/) both on the interim github.io URL and once the custom domain is live
url_tokens = {
    "__HOME_URL__": "/",
    "__EXHIBIT_URL__": "/exhibits.html",
    "__WRITING_URL__": "/writing.html",
    "__CONTACT_FORM_ACTION__": "https://formspree.io/f/xaqrneny",
}

# DNS confirmed pointed at GitHub Pages 2026-07-14 -- CNAME restored.
WRITE_CNAME = True
CUSTOM_DOMAIN = "petermcguire.info"

# bold brass "P" monogram on a dark rounded square, matching the site's own
# --black/--brass palette -- simple shapes read better than fine detail at
# 16-32px tab size. Only used for the real deploy; the Artifact-preview tab
# icon is set separately via the Artifact tool's own emoji favicon param.
FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
    '<rect width="32" height="32" rx="6" fill="#0c0b09"/>'
    '<text x="16" y="23" font-family="Georgia, \'Iowan Old Style\', serif" '
    'font-size="20" font-weight="700" fill="#c9a24b" text-anchor="middle">P</text>'
    '</svg>'
)
FAVICON_DATA_URI = "data:image/svg+xml;base64," + base64.b64encode(FAVICON_SVG.encode("utf-8")).decode("ascii")

# GA4 (aggregate traffic/referrers/funnels) + Microsoft Clarity (session replay/heatmaps).
# Added 2026-07-14 per Peter's request to track user journeys on the live site.
GA4_MEASUREMENT_ID = "G-1975K6Y3DZ"
CLARITY_PROJECT_ID = "xmlbu1xz69"

ANALYTICS_SNIPPET = f'''<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_MEASUREMENT_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA4_MEASUREMENT_ID}');
</script>
'''
if CLARITY_PROJECT_ID:
    ANALYTICS_SNIPPET += f'''<!-- Microsoft Clarity -->
<script type="text/javascript">
  (function(c,l,a,r,i,t,y){{
    c[a]=c[a]||function(){{(c[a].q=c[a].q||[]).push(arguments)}};
    t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
    y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
  }})(window, document, "clarity", "script", "{CLARITY_PROJECT_ID}");
</script>
'''

os.makedirs(DOCS_IMG, exist_ok=True)

copied = set()
for token, filename in tokens.items():
    src = os.path.join(IMG_SRC, filename)
    if filename in copied:
        continue
    if not os.path.exists(src):
        print(f"MISSING SOURCE IMAGE: {filename}")
        continue
    shutil.copy2(src, os.path.join(DOCS_IMG, filename))
    copied.add(filename)

for template_name, out_name in PAGES:
    template_path = os.path.join(HERE, template_name)
    out_path = os.path.join(DOCS, out_name)

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    print(f"\n=== {template_name} -> docs/{out_name} ===")

    for token, filename in tokens.items():
        count = html.count(token)
        if count == 0:
            continue
        html = html.replace(token, f"img/{filename}")
        print(f"{token}: img/{filename} -> {count} occurrence(s)")

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

    # templates are headless fragments (<title> + <style> + body content) meant to be
    # auto-wrapped by the Artifact tool on publish -- GitHub Pages serves this file as-is,
    # with no such wrapping, so deploy.py has to supply a real <html>/<head>/<body> itself.
    style_close = html.index("</style>") + len("</style>")
    html = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<link rel="icon" type="image/svg+xml" href="{FAVICON_DATA_URI}">\n'
        + ANALYTICS_SNIPPET
        + html[:style_close]
        + "\n</head>\n<body>\n"
        + html[style_close:]
        + "\n</body>\n</html>\n"
    )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print("Wrote", out_path, "-", os.path.getsize(out_path), "bytes")

cname_path = os.path.join(DOCS, "CNAME")
if WRITE_CNAME:
    with open(cname_path, "w", encoding="utf-8") as f:
        f.write(CUSTOM_DOMAIN + "\n")
    print(f"\nWrote docs/CNAME ({CUSTOM_DOMAIN})")
elif os.path.exists(cname_path):
    os.remove(cname_path)
    print(f"\nWRITE_CNAME is False -- removed existing docs/CNAME")
else:
    print(f"\nWRITE_CNAME is False -- no docs/CNAME present, nothing to do")
