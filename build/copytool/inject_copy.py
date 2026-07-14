"""
Reads the edited SITE_COPY.md and lays the rewritten text back into the
3 template files, in place, by re-walking each template exactly the way
extract.py did (same deterministic element order/IDs) and swapping in
whatever text now sits under each [[ID: ...]] marker.

Run this AFTER Peter has rewritten SITE_COPY.md and BEFORE running
build/inject.py (the image/URL token injector) and republishing.

Usage: python3 inject_copy.py
"""
import os, re
from bs4 import BeautifulSoup, NavigableString, Tag
from extract import walk_page, PAGES, has_ancestor_class

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.dirname(HERE)
ROOT = os.path.dirname(BUILD)
COPY_DOC = os.path.join(ROOT, "SITE_COPY.md")

ID_RE = re.compile(r"^`\[\[ID:\s*([\w.\-]+)\]\]`")
FENCE = "```"

def parse_copy_doc(path):
    """Returns {id: new_text}. Looks for an optional 'Rewrite:' fenced
    block after 'Current:' -- uses Rewrite if present, else Current
    (meaning Peter edited the Current block in place)."""
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    edits = {}
    i = 0
    n = len(lines)
    while i < n:
        m = ID_RE.match(lines[i].strip())
        if not m:
            i += 1
            continue
        block_id = m.group(1)
        i += 1
        current_text, rewrite_text = None, None
        # scan forward until the next [[ID: marker, collecting fenced blocks
        while i < n and not ID_RE.match(lines[i].strip()):
            line = lines[i].strip()
            if line == "Current:" or line == "Rewrite:":
                label = line[:-1]
                i += 1
                if i < n and lines[i].strip() == FENCE:
                    i += 1
                    body = []
                    while i < n and lines[i].strip() != FENCE:
                        # rstrip each line -- inline_to_md's extraction side
                        # normalizes trailing whitespace the same way, so a
                        # harmless trailing space Peter leaves while editing
                        # shouldn't register as a "real" content change and
                        # cause inject_copy.py to re-touch the block on every run
                        body.append(lines[i].rstrip("\n").rstrip())
                        i += 1
                    i += 1  # skip closing fence
                    text = "\n".join(body).strip("\n").strip()
                    if label == "Current":
                        current_text = text
                    else:
                        rewrite_text = text
                continue
            i += 1
        edits[block_id] = rewrite_text if rewrite_text is not None else current_text
    return edits

# ---- markdown-lite -> HTML fragment (inverse of extract.inline_to_md) ----
INLINE_TOKEN = re.compile(r"(\*\*.+?\*\*|\*.+?\*|\[.+?\]\(.*?\))")

def md_to_html(text, force_bold_span_split=False):
    if force_bold_span_split and "\n" in text:
        # exact inverse of the td.from special case: **label**\ndetail -> <b>label</b><span>detail</span>
        parts = text.split("\n", 1)
        bold = re.sub(r"^\*\*(.+)\*\*$", r"\1", parts[0].strip())
        rest = parts[1].strip() if len(parts) > 1 else ""
        return f"<b>{esc(bold)}</b><span>{esc(rest)}</span>"
    return _inline_md_to_html(text)

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _inline_md_to_html(text):
    out = []
    pos = 0
    for m in INLINE_TOKEN.finditer(text):
        out.append(esc(text[pos:m.start()]))
        token = m.group(0)
        if token.startswith("**"):
            out.append(f"<b>{esc(token[2:-2])}</b>")
        elif token.startswith("["):
            label, url = re.match(r"\[(.+?)\]\((.*?)\)", token).groups()
            out.append(f'<a href="{url}">{esc(label)}</a>')
        elif token.startswith("*"):
            out.append(f"<i>{esc(token[1:-1])}</i>")
        pos = m.end()
    out.append(esc(text[pos:]))
    return "".join(out).replace("\n", "<br>")

def main():
    if not os.path.exists(COPY_DOC):
        print("No SITE_COPY.md found at", COPY_DOC)
        return
    edits = parse_copy_doc(COPY_DOC)
    print(f"Parsed {len(edits)} blocks from {COPY_DOC}")

    changed_count = 0
    for prefix, filename in PAGES:
        # walk_page re-parses the file fresh -- str(el) on these UNMODIFIED
        # elements reproduces the exact original source substring (verified:
        # html.parser round-trips simple tags byte-for-byte), so we can do
        # surgical text-level replacement instead of re-serializing the
        # whole soup (which reorders attributes and strips hand-formatting
        # on every line, not just the ones we're changing).
        soup, results = walk_page(prefix, filename)
        path = os.path.join(BUILD, filename)
        with open(path, encoding="utf-8") as f:
            text = f.read()

        # IMPORTANT: search forward from a cursor that only ever advances,
        # instead of always searching from position 0. Two elements can
        # share byte-identical original HTML (e.g. two <h2>What it adds up
        # to</h2> in different sections) -- if the EARLIER one in document
        # order is left unchanged (skipped below) while a LATER duplicate
        # IS changed, a naive text.replace(old, new, 1) from position 0
        # would silently rewrite the wrong (earlier, still-unedited) one.
        # Walking results in document order and always resuming the search
        # from where the previous element ended keeps every match aligned
        # to the correct occurrence regardless of which duplicates changed.
        file_changed = 0
        cursor = 0
        for block_id, el, original_text in results:
            old_fragment = str(el)
            pos = text.find(old_fragment, cursor)
            if pos == -1:
                print(f"  WARNING: {block_id} original fragment not found verbatim (from cursor) in {filename}, skipping -- fix by hand")
                continue
            new_text = edits.get(block_id)
            if new_text is None:
                print(f"  WARNING: {block_id} not found in SITE_COPY.md, leaving as-is")
                cursor = pos + len(old_fragment)
                continue
            if new_text == original_text:
                cursor = pos + len(old_fragment)
                continue
            is_bridge_from = "from" in (el.get("class") or [])
            inner_html = md_to_html(new_text, force_bold_span_split=is_bridge_from)
            attrs = "".join(
                f' {k}="{v if isinstance(v, str) else " ".join(v)}"' for k, v in el.attrs.items()
            )
            new_fragment = f"<{el.name}{attrs}>{inner_html}</{el.name}>"
            text = text[:pos] + new_fragment + text[pos + len(old_fragment):]
            cursor = pos + len(new_fragment)
            file_changed += 1
            changed_count += 1

        if file_changed:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"{filename}: {file_changed} blocks changed, file rewritten (surgical, rest of file untouched)")
        else:
            print(f"{filename}: no changes")

    print(f"\nTotal blocks changed: {changed_count}")
    print("Next: run build/inject.py to re-resolve image/URL tokens, then republish each Artifact.")

if __name__ == "__main__":
    main()
