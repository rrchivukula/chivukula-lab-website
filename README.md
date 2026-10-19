# Chivukula Lab website

The lab website at chivukula-lab.org. Plain HTML and CSS, no JavaScript,
served by GitHub Pages from the `docs/` folder.

## How it is put together

- `data/` holds everything you edit. Four plain text files:
  - `site.yaml`: tagline, intro, research intro, funding, join and giving text, contact details, links, affiliations.
  - `research.yaml`: the research areas, each with images and text.
  - `people.yaml`: the PI, current members, and alumni.
  - `publications.yaml`: the publication list, newest first.
  - `news.yaml`: news items; sorted by date automatically.
- `template.html` is the page skeleton with `{{PLACEHOLDERS}}`.
- `build.py` stamps the data into the template and writes `docs/index.html`.
- `docs/` is the finished site: the built page, `style.css`, images, the CV PDF, and the favicon files.
- `headshot.py` crops a photo to the headshot shape used on the team cards.

## Updating the site

The easy way: edit a file in `data/` directly on github.com (open the file,
click the pencil, make the change, "Commit changes"). A GitHub Action then
rebuilds the page and commits `docs/index.html` on its own; the live site
updates a minute or two later. You will see a second commit named "Rebuild
site" appear from github-actions; that is expected.

The same works for images: upload a new headshot to `docs/images/people/`
on github.com (Add file, Upload files) with the same name as the old one.
Crop it first to a 4:5 portrait, or ask Claude to crop it with `headshot.py`.

The manual way, if you have the repository on your own computer:

1. Edit the relevant file in `data/`, or drop a new image into `docs/images/`.
2. Run `python3 build.py` (needs Python 3 and the `pyyaml` package).
3. Commit and push.

The build prints a list of any images or files that are referenced but missing;
those get a grey placeholder so the page still builds. If a YAML file has a
syntax error, the Action fails and the site stays as it was; the error shows
under the repository's Actions tab.

### Common edits

- New paper: add an entry at the top of `data/publications.yaml` with title, authors, journal, year, pmid, and doi. Add `selected: true` to feature it.
- New lab member: add an entry under `current:` in `data/people.yaml` and put their headshot at `docs/images/people/<name>.jpg`. Crop it first with `python3 headshot.py photo.jpg docs/images/people/<name>.jpg`.
- Someone leaves: move their entry to `alumni:` with `role` and `now` fields. Alumni are sorted alphabetically by last name.
- News: add an entry to `data/news.yaml` with a date like `June 2026`, the text, and an optional link.
- Any text or journal name containing a colon must be in double quotes in the YAML files.

## Design notes

- Headshots are converted to black and white by one line in `docs/style.css` (search for `grayscale`); delete it to show them in color.
- Colors and fonts are the tokens at the top of `docs/style.css`.
- The page has a dark mode that follows the visitor's system setting.
- Fonts (Newsreader and IBM Plex Sans) are served from `docs/fonts/`; the page makes no requests to outside servers.
