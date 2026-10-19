#!/usr/bin/env python3
"""Build the lab website.

Reads the text files in data/ and writes docs/index.html from template.html.
Run it from the folder that contains this file:

    python3 build.py

Everything the browser sees is in docs/ (GitHub Pages serves that folder). The only things you ever edit are
the files in data/ (content) and docs/style.css (appearance).
"""

import html
import re
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SITE = ROOT / "docs"
TEMPLATE = ROOT / "template.html"


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------

def load(name):
    """Read one YAML file from data/."""
    with open(DATA / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def esc(text):
    """Escape text so it is safe to drop into HTML."""
    return html.escape(str(text), quote=True)


LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def rich(text):
    """Escape text, then turn [label](url) into links."""
    escaped = esc(text).strip()
    return LINK_RE.sub(r'<a href="\2">\1</a>', escaped)


def paragraphs(items):
    """A string or a list of strings becomes one <p> per item."""
    if isinstance(items, str):
        items = [items]
    return "\n".join(f"<p>{rich(p)}</p>" for p in items)


MISSING = []


def image(path, alt, kind="generic"):
    """Return an <img> tag. If the file is missing, write a labeled
    placeholder SVG beside where it should be, and use that instead, so the
    site still builds. Missing files are listed at the end of the build."""
    target = SITE / path
    if target.exists():
        return f'<img src="{esc(path)}" alt="{esc(alt)}" loading="lazy">'
    MISSING.append(path)
    placeholder = target.with_suffix(".svg")
    placeholder.parent.mkdir(parents=True, exist_ok=True)
    label = target.name
    if kind == "portrait":
        w, h = 400, 500
    elif kind == "wide":
        w, h = 1200, 400
    else:
        w, h = 1200, 800
    placeholder.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">'
        f'<rect width="{w}" height="{h}" fill="#d9dde1"/>'
        f'<text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="sans-serif" font-size="{max(14, w // 32)}" fill="#6b7480">'
        f'{esc(label)}</text></svg>',
        encoding="utf-8",
    )
    rel = placeholder.relative_to(SITE).as_posix()
    return f'<img src="{esc(rel)}" alt="{esc(alt)}" loading="lazy">'


# ----------------------------------------------------------------------------
# Section builders. Each returns a string of HTML.
# ----------------------------------------------------------------------------

def build_research(areas):
    out = []
    for area in areas:
        # `image` may be one path or a list of paths shown side by side.
        paths = area["image"] if isinstance(area["image"], list) else [area["image"]]
        alts = area.get("alt", area["title"])
        alts = alts if isinstance(alts, list) else [alts] * len(paths)
        imgs = "".join(image(p, a, "generic") for p, a in zip(paths, alts))
        out.append(
            '<article class="area">\n'
            f'  <figure class="panels panels-{len(paths)}">{imgs}</figure>\n'
            '  <div class="area-text">\n'
            f'    <h3>{esc(area["title"])}</h3>\n'
            f'    <div>{paragraphs(area["text"])}</div>\n'
            "  </div>\n"
            "</article>"
        )
    return "\n".join(out)


def build_pi(pi):
    cv = ""
    if pi.get("cv"):
        cv_path = SITE / pi["cv"]
        if cv_path.exists():
            cv = f'<p class="cv"><a href="{esc(pi["cv"])}">Curriculum vitae (PDF)</a></p>'
        else:
            MISSING.append(pi["cv"])
    return (
        '<div class="pi">\n'
        '  <div class="pi-head">\n'
        f'    <h3>{esc(pi["name"])}</h3>\n'
        f'    <p class="role">{esc(pi["role"])}</p>\n'
        "  </div>\n"
        f'  <figure class="portrait">{image(pi["photo"], pi["name"], "portrait")}</figure>\n'
        '  <div class="pi-text">\n'
        f'    {paragraphs(pi["blurb"])}\n'
        f"    {cv}\n"
        "  </div>\n"
        "</div>"
    )


def build_members(members):
    out = []
    for m in members:
        out.append(
            '<li class="member">\n'
            f'  <figure class="portrait">{image(m["photo"], m["name"], "portrait")}</figure>\n'
            f'  <h4>{esc(m["name"])}</h4>\n'
            f'  <p class="role">{esc(m["role"])}</p>\n'
            f'  {paragraphs(m.get("blurb", ""))}\n'
            "</li>"
        )
    return "\n".join(out)


def build_alumni(alumni):
    if not alumni:
        return ""
    rows = []
    # Alphabetical by last name (the last word of the name).
    for a in sorted(alumni, key=lambda a: a["name"].split()[-1].lower()):
        detail = a.get("role", "")
        now = f' <span class="now">Now: {esc(a["now"])}</span>' if a.get("now") else ""
        rows.append(
            f'<li><span class="name">{esc(a["name"])}</span> '
            f'<span class="detail">{esc(detail)}</span>{now}</li>'
        )
    return '<h3>Alumni</h3>\n<ul class="alumni">\n' + "\n".join(rows) + "\n</ul>"


def bold_authors(authors, highlight):
    """Bold the lab's own names in an author string."""
    names = [n.strip() for n in authors.split(",")]
    out = []
    for n in names:
        e = esc(n)
        out.append(f"<b>{e}</b>" if n in highlight else e)
    return ", ".join(out)


def pub_links(p):
    links = []
    if p.get("doi"):
        links.append(f'<a href="https://doi.org/{esc(p["doi"])}">DOI</a>')
    if p.get("pmid"):
        links.append(f'<a href="https://pubmed.ncbi.nlm.nih.gov/{esc(p["pmid"])}/">PubMed</a>')
    if p.get("pmc"):
        links.append(f'<a href="https://www.ncbi.nlm.nih.gov/pmc/articles/{esc(p["pmc"])}/">Free full text</a>')
    if p.get("pdf"):
        if (SITE / p["pdf"]).exists():
            links.append(f'<a href="{esc(p["pdf"])}">PDF</a>')
        else:
            MISSING.append(p["pdf"])
    return " ".join(links)


def pub_item(p, highlight):
    primary = None
    if p.get("doi"):
        primary = f'https://doi.org/{p["doi"]}'
    elif p.get("pmid"):
        primary = f'https://pubmed.ncbi.nlm.nih.gov/{p["pmid"]}/'
    title = esc(p["title"])
    if primary:
        title = f'<a href="{esc(primary)}">{title}</a>'
    return (
        '<li class="pub">\n'
        f'  <span class="pub-title">{title}</span>\n'
        f'  <span class="pub-authors">{bold_authors(p["authors"], highlight)}</span>\n'
        f'  <span class="pub-where"><i>{esc(p["journal"])}</i> {esc(p["year"])}</span>\n'
        f'  <span class="pub-links">{pub_links(p)}</span>\n'
        "</li>"
    )


def build_publications(pubs, highlight):
    pubs = sorted(pubs, key=lambda p: int(p["year"]), reverse=True)
    out = []
    selected = [p for p in pubs if p.get("selected")]
    if selected:
        out.append('<h3>Selected</h3>\n<ul class="pubs">')
        out.extend(pub_item(p, highlight) for p in selected)
        out.append("</ul>")
        # The full list sits under a fold so the page does not trail off.
        out.append('<details class="pubs-all"><summary>All publications</summary>')
    year = None
    for p in pubs:
        if p["year"] != year:
            if year is not None:
                out.append("</ul>")
            year = p["year"]
            out.append(f'<h4 class="year">{esc(year)}</h4>\n<ul class="pubs">')
        out.append(pub_item(p, highlight))
    out.append("</ul>")
    if selected:
        out.append("</details>")
    return "\n".join(out)


def news_item(n):
    text = rich(n["text"])
    if n.get("link"):
        text += f' <a class="more" href="{esc(n["link"])}">Read more</a>'
    return (
        '<li class="news-item">\n'
        f'  <span class="news-date">{esc(n["date"])}</span>\n'
        f'  <span class="news-text">{text}</span>\n'
        "</li>"
    )


MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], 1)}


def news_key(item):
    """Sort key for a news date written as 'June 2026', '2026', or
    '2026-06-15'. Anything unrecognized sorts to the top so it is noticed."""
    d = str(item.get("date", "")).strip()
    parts = d.replace("-", " ").split()
    try:
        if len(parts) == 1:
            return (int(parts[0]), 0, 0)
        if parts[0].lower() in MONTHS:
            return (int(parts[1]), MONTHS[parts[0].lower()], 0)
        return tuple(int(x) for x in parts[:3]) + (0,) * (3 - len(parts[:3]))
    except ValueError:
        return (9999, 99, 99)


def build_news(items, show=5):
    """The newest `show` items are visible; older ones sit under a fold.
    Entries are sorted newest first, so order in the file does not matter."""
    if not items:
        return ""
    items = sorted(items, key=news_key, reverse=True)
    recent = items[:show]
    older = items[show:]
    out = ['<ul class="news">']
    out.extend(news_item(n) for n in recent)
    out.append("</ul>")
    if older:
        out.append('<details class="news-older"><summary>Earlier</summary>\n<ul class="news">')
        out.extend(news_item(n) for n in older)
        out.append("</ul></details>")
    return "\n".join(out)


def build_links(links):
    return "\n".join(f'<li><a href="{esc(l["url"])}">{esc(l["label"])}</a></li>' for l in links)


def build_logos(links):
    """Affiliations that have a logo get it shown as a linked image."""
    out = []
    for l in links:
        if l.get("logo") and (SITE / l["logo"]).exists():
            out.append(
                f'<a class="logo" href="{esc(l["url"])}">'
                f'<img src="{esc(l["logo"])}" alt="{esc(l["label"])}" loading="lazy"></a>'
            )
        elif l.get("logo"):
            MISSING.append(l["logo"])
    return "\n".join(out)


# ----------------------------------------------------------------------------
# Put it together
# ----------------------------------------------------------------------------

def main():
    site = load("site.yaml")
    research = load("research.yaml")
    people = load("people.yaml")
    pubs = load("publications.yaml")
    news = load("news.yaml") if (DATA / "news.yaml").exists() else []

    template = TEMPLATE.read_text(encoding="utf-8")

    years = str(date.today().year)

    fields = {
        "NAME": esc(site["name"]),
        "SITE_URL": esc(site.get("site_url", "").rstrip("/")),
        "SHORT_NAME": esc(site.get("short_name", site["name"])),
        "TAGLINE": esc(site["tagline"]),
        "INSTITUTION": "<br>".join(esc(x) for x in site["institution_lines"]),
        "INTRO": rich(site["intro"]),
        "HERO": image(site["hero_image"], site.get("hero_alt", ""), "generic"),
        "NEWS": build_news(news),
        "RESEARCH_INTRO": paragraphs(site["research_intro"]),
        "RESEARCH": build_research(research),
        "PI": build_pi(people["pi"]),
        "MEMBERS": build_members(people.get("current", [])),
        "ALUMNI": build_alumni(people.get("alumni", [])),
        "PUBLICATIONS": build_publications(pubs, set(site.get("highlight_authors", []))),
        "FUNDING": rich(site["funding"]),
        "JOIN": rich(site["join"]),
        "GIVING": rich(site["giving"]),
        "GIVING_URL": esc(site["giving_url"]),
        "EMAIL": esc(site["email"]),
        "ADDRESS": "<br>".join(esc(x) for x in site["address"]),
        "LINKS": build_links(site.get("links", [])),
        # Affiliations with a logo are shown as the logo alone; the rest as text.
        "AFFILIATIONS": build_links([a for a in site.get("affiliations", []) if not a.get("logo")]),
        "LOGOS": build_logos(site.get("affiliations", [])),
        "YEARS": years,
    }

    page = template
    for key, value in fields.items():
        page = page.replace("{{" + key + "}}", value)

    leftover = re.findall(r"{{[A-Z_]+}}", page)
    if leftover:
        sys.exit(f"Template has fields with no content: {leftover}")

    # Links that leave the site (other websites, and files such as the CV PDF)
    # open in a new tab; links within the page (#research and so on) do not.
    page = re.sub(
        r'<a (class="[^"]*" )?href="((?:https?://|files/)[^"]*)"',
        lambda m: f'<a {m.group(1) or ""}href="{m.group(2)}" target="_blank" rel="noopener"',
        page,
    )

    SITE.mkdir(exist_ok=True)
    (SITE / "index.html").write_text(page, encoding="utf-8")
    print(f"Wrote {SITE / 'index.html'}")
    if MISSING:
        print("Missing files (placeholders used where possible):")
        for m in MISSING:
            print("  -", m)


if __name__ == "__main__":
    main()
