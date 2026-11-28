"""Daily health check for The Yarn Nest automatic posts (standard library only).

Checks that the expected number of posts were published today (UTC), and that each
recent post is complete: page file, h1, meta description, image, canonical URL, sitemap
entry, blog card, no duplicate title, enough text, and affiliate links marked sponsored.
Exits with status 1 when something is wrong, so GitHub emails the owner about the failed run.
"""
import argparse, datetime, json, os, re, sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = "https://www.theyarnnest.shop/"
NON_POSTS = {"index", "blog", "about", "contact", "privacy", "download", "post"}


def text_of(html):
    html = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S | re.I)
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", html))).strip()


def h1_of(html):
    m = re.search(r"<h1\b[^>]*>(.*?)</h1>", html, re.S | re.I)
    return re.sub(r"\s+", " ", text_of(m.group(1))).strip().lower() if m else ""


def check_post(entry, sitemap, blog, other_titles):
    problems = []
    name = entry.get("file", "")
    path = ROOT / name
    if not name or not path.is_file():
        return [f"{name or '(no file)'}: page file is missing"]
    html = path.read_text(encoding="utf-8", errors="ignore")
    stem = name.removesuffix(".html")
    title = h1_of(html)
    if not title:
        problems.append(f"{name}: no h1 title")
    elif other_titles.get(title, 0) > 1:
        problems.append(f"{name}: another page has the same h1 title: {title[:70]}")
    desc = re.search(r'<meta name="description" content="([^"]*)"', html)
    if not desc or not (120 <= len(unescape(desc.group(1))) <= 180):
        problems.append(f"{name}: meta description missing or outside 120-180 characters")
    if f'rel="canonical" href="{SITE}{stem}"' not in html:
        problems.append(f"{name}: canonical URL missing or wrong")
    img = re.search(r"<figure><img src=\"([^\"]+)\"", html)
    if not img:
        problems.append(f"{name}: no main image")
    elif not img.group(1).startswith("http") and not (ROOT / img.group(1)).is_file():
        problems.append(f"{name}: image file is missing: {img.group(1)}")
    if f"{SITE}{stem}</loc>" not in sitemap:
        problems.append(f"{name}: not in sitemap.xml")
    if f'href="{stem}"' not in blog:
        problems.append(f"{name}: no card on blog.html")
    words = len(text_of(html).split())
    if words < 500:
        problems.append(f"{name}: only about {words} words (looks too short)")
    for tag in re.findall(r"<a\b[^>]*href=\"https://s\.click\.aliexpress\.com/[^\"]*\"[^>]*>", html):
        if "sponsored" not in tag:
            problems.append(f"{name}: an affiliate link is missing rel=\"sponsored\"")
            break
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expected", type=int, default=2, help="posts expected today (UTC)")
    ap.add_argument("--history", default=str(ROOT / "keyword_history.json"))
    ap.add_argument("--recent-days", type=int, default=2)
    args = ap.parse_args()

    history = json.loads(Path(args.history).read_text(encoding="utf-8")) if Path(args.history).exists() else {"used": []}
    now = datetime.datetime.now(datetime.timezone.utc)
    today = now.date().isoformat()
    cutoff = now - datetime.timedelta(days=args.recent_days)

    def published(entry):
        try:
            return datetime.datetime.fromisoformat(entry["published_at"].replace("Z", "+00:00"))
        except (KeyError, ValueError, AttributeError):
            return None

    todays = [e for e in history.get("used", []) if (published(e) and published(e).date().isoformat() == today)]
    recent = [e for e in history.get("used", []) if (published(e) and published(e) >= cutoff)]

    titles = {}
    for page in ROOT.glob("*.html"):
        if page.stem in NON_POSTS:
            continue
        t = h1_of(page.read_text(encoding="utf-8", errors="ignore"))
        if t:
            titles[t] = titles.get(t, 0) + 1
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8") if (ROOT / "sitemap.xml").exists() else ""
    blog = (ROOT / "blog.html").read_text(encoding="utf-8") if (ROOT / "blog.html").exists() else ""

    problems = []
    if len(todays) < args.expected:
        problems.append(f"Only {len(todays)} of {args.expected} expected posts were published today ({today} UTC). Check the 'Auto Generate HTML Blog Post' runs in the Actions tab.")
    for entry in recent:
        problems += check_post(entry, sitemap, blog, titles)

    lines = [f"# Yarn Nest daily check ({today} UTC)", "",
             f"- Posts published today: {len(todays)} (expected {args.expected})",
             f"- Recent posts checked (last {args.recent_days} days): {len(recent)}"]
    lines += ["", "## Problems" if problems else "## All good"]
    lines += [f"- {p}" for p in problems] or ["No problems found."]
    report = "\n".join(lines)
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(report + "\n")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
