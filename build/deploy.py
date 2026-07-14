import os, re, shutil

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
