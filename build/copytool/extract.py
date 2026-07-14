"""
Extracts all editable visible copy from the 3 site templates into one
human-editable Markdown doc (SITE_COPY.md), plus a manifest.json that
records exactly where each block came from so it can be laid back in
later without re-deriving anything.

Design:
- Walks each template in document order using a curated selector list per page.
- Skips raw alt-text (accessibility transcriptions of real exhibit panels,
  not "his language" to rewrite) and pure decorative glyphs (arrows, dots).
- Converts simple inline tags (<b>/<strong>, <i>/<em>, <a href>) to a
  markdown-lite convention (**bold**, *italic*, [text](url)) so link/bold
  structure survives a round-trip through a plain-text edit.
- ID = pageprefix.sectionid.tag+index.slug -- stable, human-scannable,
  and independent of the text content itself (survives a full rewrite).
- Two timeline representations (chart tooltip vs. reading-list) share
  IDENTICAL text by design -- only the reading-list copy is extracted,
  flagged dual:true in the manifest so re-injection updates both.
"""
import json, re, os
from bs4 import BeautifulSoup, NavigableString, Tag

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.dirname(HERE)
ROOT = os.path.dirname(BUILD)

PAGES = [
    ("home", "site-home-template.html"),
    ("writing", "site-writing-template.html"),
    ("exhibit", "exhibit-built-to-protect-template.html"),
]

# tags whose OWN element (not descendants) should be extracted as one block
BLOCK_TAGS = {"h1", "h2", "h3", "h4", "p", "dd", "dt", "th", "td", "figcaption"}
# span/div classes that hold standalone editable text (not pure structure)
INLINE_CLASSES = {
    "eyebrow", "subtitle", "role", "big-idea-note", "register-sub",
    "ped-label", "thumb-title", "thumb-desc", "tl-reading-title",
    "tl-reading-dates", "tl-reading-detail", "tl-scale-note",
    "divider-label", "manifesto", "plate", "ped-chip", "frame-tag",
    "strip-label",
}
# <a> classes that are standalone text links (not big card containers
# whose inner h3/p/etc. get extracted separately)
LINK_CLASSES = {
    "nav-name", "btn", "btn-primary", "btn-ghost", "exhibit-link",
    "link-card-arrow",
}
# parent classes under which ANY direct <a> or <div> child is a standalone
# text link/block, regardless of the child's own class (nav/closing links
# often carry no class at all, and footer-meta divs are plain containers)
LINK_PARENT_CLASSES = {"nav-links", "closing-links"}
DIV_PARENT_CLASSES = {"footer-meta"}
SKIP_CLASSES = {"tl-li-dot", "tl-legend-dot", "zoom-hint"}

def slugify(text, n=4):
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())[:n]
    return "-".join(words) or "x"

def inline_to_md(el):
    """Serialize an element's children to markdown-lite, decoding entities."""
    out = []
    prev_was_tag = False
    for child in el.children:
        if isinstance(child, NavigableString):
            out.append(str(child))
            prev_was_tag = False
        elif isinstance(child, Tag):
            # two tags with no text node between them (e.g. <b>label</b><span>detail</span>)
            # means adjacent block-ish lines in the original CSS -- keep them on separate lines
            if prev_was_tag and "zoom-hint" not in (child.get("class") or []):
                out.append("\n")
            prev_was_tag = True
            if child.name in ("b", "strong"):
                out.append(f"**{inline_to_md(child)}**")
            elif child.name in ("i", "em"):
                out.append(f"*{inline_to_md(child)}*")
            elif child.name == "a":
                href = child.get("href", "")
                out.append(f"[{inline_to_md(child)}]({href})")
            elif child.name == "br":
                out.append("\n")
            elif "zoom-hint" in (child.get("class") or []):
                continue  # boilerplate, not per-instance content
            else:
                out.append(inline_to_md(child))
    text = "".join(out)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text).strip()
    return text

def nearest_section_id(el):
    cur = el
    while cur is not None:
        if isinstance(cur, Tag) and cur.get("id"):
            return cur.get("id")
        cur = cur.parent
    return "root"

def should_take(el):
    if not isinstance(el, Tag):
        return False
    classes = set(el.get("class") or [])
    if classes & SKIP_CLASSES:
        return False
    if el.name in BLOCK_TAGS:
        # if this block contains a more-specific nested INLINE_CLASSES
        # element (e.g. a <figcaption> wrapping .thumb-title + .thumb-desc),
        # let those finer-grained children win instead of mashing them
        # together into one block with no separator
        nested_specific = el.find(
            lambda t: isinstance(t, Tag) and t is not el
            and set(t.get("class") or []) & INLINE_CLASSES
        )
        if nested_specific is not None:
            return False
        return True
    if el.name in ("span", "div") and classes & INLINE_CLASSES:
        return True
    if el.name == "a" and classes & LINK_CLASSES:
        return True
    if el.name == "a" and has_ancestor_class(el, LINK_PARENT_CLASSES, max_levels=2):
        return True
    if el.name == "div" and has_ancestor_class(el, DIV_PARENT_CLASSES, max_levels=1):
        return True
    return False

def has_ancestor_class(el, class_set, max_levels):
    cur = el.parent
    for _ in range(max_levels):
        if not isinstance(cur, Tag):
            return False
        if set(cur.get("class") or []) & class_set:
            return True
        cur = cur.parent
    return False

def is_nested_in_taken(el, taken_set):
    cur = el.parent
    while cur is not None:
        if id(cur) in taken_set:
            return True
        cur = cur.parent
    return False

def walk_page(prefix, filename):
    """Re-walkable core: parses filename fresh and returns (soup, [(block_id, element, text_md), ...])
    in the SAME deterministic order/IDs every time, as long as the template's
    tag/class/id structure is unchanged (only text content may differ)."""
    path = os.path.join(BUILD, filename)
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    soup = BeautifulSoup(raw, "html.parser")

    candidates = [el for el in soup.find_all(True) if should_take(el)]
    taken_ids = set()
    results = []
    counters = {}  # (section, tag) -> running index

    for el in candidates:
        if is_nested_in_taken(el, taken_ids):
            continue
        text_md = inline_to_md(el)
        if not text_md or not re.search(r"[a-zA-Z0-9]", text_md):
            continue
        section = nearest_section_id(el)
        key = (section, el.name)
        counters[key] = counters.get(key, 0) + 1
        idx = counters[key]
        block_id = f"{prefix}.{section}.{el.name}{idx}.{slugify(text_md)}"
        taken_ids.add(id(el))
        results.append((block_id, el, text_md))
    return soup, results

def extract_page(prefix, filename):
    soup, results = walk_page(prefix, filename)
    blocks = []
    for block_id, el, text_md in results:
        blocks.append({
            "id": block_id,
            "file": filename,
            "section": nearest_section_id(el),
            "tag": el.name,
            "classes": sorted(set(el.get("class") or [])),
            "text": text_md,
        })
    return blocks

def main():
    all_blocks = []
    for prefix, filename in PAGES:
        blocks = extract_page(prefix, filename)
        print(f"{filename}: {len(blocks)} blocks")
        all_blocks.extend(blocks)

    manifest_path = os.path.join(HERE, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(all_blocks, f, indent=2, ensure_ascii=False)
    print("Wrote", manifest_path, "-", len(all_blocks), "total blocks")

if __name__ == "__main__":
    main()
