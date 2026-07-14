"""
Turns manifest.json into SITE_COPY.md -- the single human-editable
document Peter will rewrite. Grouped by page, then by section, in
document order, each block shown with its stable ID and current text.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.dirname(HERE)
ROOT = os.path.dirname(BUILD)

PAGE_TITLES = {
    "home": "HOME  (build/site-home-template.html)",
    "about": "ABOUT  (build/site-about-template.html)",
    "exhibit": "EXHIBITS — Built to Protect + Speaking Through the Dead  (build/exhibit-built-to-protect-template.html)",
}
SECTION_TITLES = {
    "root": "Nav / global chrome",
    "top": "Hero",
    "exhibits": "Exhibit preview cards",
    "timeline": "Career timeline",
    "about": "Explore-the-site link cards" ,  # home page's #about anchor (the "Keep going" section)
    "throughline": "The Throughline",
    "skills-bridge": "Skills Bridge",
    "built-to-protect": "Built to Protect — hero",
    "big-idea": "Built to Protect — The Big Idea & Research Foundation",
    "final-design": "Built to Protect — The Final Design & Its Pedagogy",
    "install-outcome": "Built to Protect — Install & Outcome",
    "speaking-through-the-dead": "Speaking Through the Dead — hero",
    "std-big-idea": "Speaking Through the Dead — The Big Idea & Research Foundation",
    "std-method": "Speaking Through the Dead — The Exhibit & Its Method",
    "std-outcome": "Speaking Through the Dead — Outcome",
}

def main():
    with open(os.path.join(HERE, "manifest.json"), encoding="utf-8") as f:
        blocks = json.load(f)

    by_page = {}
    for b in blocks:
        prefix = b["id"].split(".")[0]
        by_page.setdefault(prefix, []).append(b)

    lines = []
    lines.append("# Site Copy — Master Editable Document\n")
    lines.append(
        "This is every piece of visible writing on the 3 built pages (Home, About, "
        "Exhibits). Rewrite the text under each `Current:` block however you like — "
        "add a `Rewrite:` line yourself, or just edit the text in place, whichever is "
        "easier for you.\n"
    )
    lines.append(
        "**Do not touch the `[[ID: ...]]` markers** — those are how everything gets "
        "matched back to its exact spot in the site when you're done. Everything else "
        "is fair game.\n"
    )
    lines.append(
        "A few things NOT in this doc, on purpose: raw image `alt` text (the verbatim "
        "transcriptions of real exhibit panels/screenshots — not your prose to rewrite), "
        "and the CV (not built yet). Say the word if you want either pulled in too.\n"
    )
    lines.append(
        "Formatting notes: `**bold**` and `*italic*` and `[link text](url)` all mean "
        "what they look like — keep that syntax if you want the bold/italic/link to "
        "survive, or delete it if you don't want that word linked/bold anymore. Some "
        "links point at internal pages using placeholder tokens like `__WRITING_URL__` — "
        "leave those alone, they get swapped for the real URL automatically at publish "
        "time.\n"
    )
    lines.append("---\n")

    for prefix in ("home", "about", "exhibit"):
        page_blocks = by_page.get(prefix, [])
        lines.append(f"\n## {PAGE_TITLES.get(prefix, prefix.upper())}\n")
        current_section = None
        for b in page_blocks:
            if b["section"] != current_section:
                current_section = b["section"]
                title = SECTION_TITLES.get(current_section, current_section)
                lines.append(f"\n### {title}\n")
            lines.append(f"`[[ID: {b['id']}]]`  <sub>({b['tag']}"
                          + (f".{'.'.join(b['classes'])}" if b['classes'] else "") + ")</sub>")
            lines.append("Current:")
            lines.append("```")
            lines.append(b["text"])
            lines.append("```")
            lines.append("")

    out_path = os.path.join(ROOT, "SITE_COPY.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("Wrote", out_path, "-", len(blocks), "blocks across", len(by_page), "pages")

if __name__ == "__main__":
    main()
