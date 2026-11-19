import os, re, json, time, random, datetime
from pathlib import Path
from html import escape, unescape
from html.parser import HTMLParser
import requests
from google import genai

ROOT = Path(__file__).resolve().parent
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
PIXABAY_KEY = os.environ["PIXABAY_API_KEY"]

class Extractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)

def plain(html):
    parser = Extractor()
    parser.feed(html)
    return re.sub(r"\s+", " ", unescape(" ".join(parser.parts))).strip()

def pixabay_image():
    cache = ROOT / ".cache" / "pixabay.json"
    data = None
    if cache.exists():
        try:
            old = json.loads(cache.read_text(encoding="utf-8"))
            if time.time() - old["saved"] < 86400:
                data = old["data"]
        except Exception:
            data = None
    if data is None:
        r = requests.get("https://pixabay.com/api/", params={
            "key": PIXABAY_KEY, "q": "crochet amigurumi yarn craft",
            "image_type": "photo", "safesearch": "true", "per_page": 50,
            "order": "popular"
        }, timeout=30)
        r.raise_for_status()
        data = r.json()
        if not data.get("hits"):
            raise RuntimeError("Pixabay returned no images.")
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"saved": time.time(), "data": data}), encoding="utf-8")

    # Read attribution URLs already used by published pages so a cached Pixabay
    # result cannot be selected again for another post.
    used_urls = set()
    for html_file in ROOT.glob("*.html"):
        try:
            html = html_file.read_text(encoding="utf-8")
            used_urls.update(re.findall(
                r'href=["\\'](https?://(?:www\\.)?pixabay\\.com/[^"\\']+)',
                html, re.I
            ))
        except OSError:
            continue

    available = [
        hit for hit in data.get("hits", [])
        if hit.get("pageURL") and hit.get("webformatURL")
        and hit.get("pageURL") not in used_urls
    ]
    if not available:
        raise RuntimeError(
            "No unused Pixabay images remain in the cached results. "
            "Refresh the Pixabay cache or expand the search before generating another post."
        )
    hit = random.choice(available)
    image_url, credit_url = hit.get("webformatURL"), hit.get("pageURL")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
    folder = ROOT / "images"
    folder.mkdir(exist_ok=True)
    name = f"crochet-{stamp}.jpg"
    response = requests.get(image_url, timeout=45)
    response.raise_for_status()
    (folder / name).write_bytes(response.content)
    return "images/" + name, credit_url

def main():
    prompt = """Write a helpful English crochet blog article about modern amigurumi plush ideas.
Return clean HTML only, with one h1 title, an introduction, 3-4 h2 sections,
practical beginner-friendly advice, and a conclusion. No Markdown fences."""
    # Retry temporary Gemini capacity/rate-limit errors instead of failing the workflow immediately.
    response = None
    for attempt in range(6):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )
            break
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            message = str(exc)
            temporary = status in (429, 500, 502, 503, 504) or any(
                code in message for code in ("429", "500", "502", "503", "504")
            )
            if not temporary or attempt == 5:
                raise
            delay = min(30, 5 * (2 ** attempt))
            print(f"Gemini temporarily unavailable; retry {attempt + 1}/5 in {delay}s: {message}")
            time.sleep(delay)

    if response is None or not response.text:
        raise RuntimeError("Gemini returned an empty article after retries.")
    article = response.text.strip()
    article = re.sub(r"^\x60\x60\x60(?:html)?\s*|\s*\x60\x60\x60$", "", article, flags=re.I).strip()
    title_match = re.search(r"<h1\b[^>]*>(.*?)</h1>", article, re.I | re.S)
    if not title_match:
        raise RuntimeError("Gemini response did not contain an h1 title.")
    title = plain(title_match.group(1))
    safe_title = escape(title)
    excerpt = plain(article)
    excerpt = excerpt[:157].rsplit(" ", 1)[0] + "..." if len(excerpt) > 160 else excerpt
    description = excerpt

    blog_path = ROOT / "blog.html"
    blog = blog_path.read_text(encoding="utf-8")
    grid_start = blog.find('<div class="blog-grid">')
    if grid_start < 0:
        raise RuntimeError("blog-grid container not found.")
    count = len(re.findall(r'<article\b[^>]*class=["\'][^"\']*\bblog-card\b', blog, re.I))
    post_number = count + 1
    depth = 1
    token = re.compile(r"<div\b[^>]*>|</div>", re.I)
    grid_end = -1
    for match in token.finditer(blog, grid_start + len('<div class="blog-grid">')):
        if match.group(0).lower().startswith("<div"):
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                grid_end = match.start()
                break
    if grid_end < 0:
        raise RuntimeError("Could not safely locate blog-grid end.")

    now = datetime.datetime.now(datetime.timezone.utc)
    stamp = now.strftime("%Y-%m-%d-%H-%M-%S")
    filename = "post-" + stamp + ".html"
    canonical_url = "https://www.theyarnnest.shop/" + filename
    image_path, credit_url = pixabay_image()
    image_url = "https://www.theyarnnest.shop/" + image_path
    published_at = now.isoformat(timespec="seconds").replace("+00:00", "Z")

    # Structured data for search engines: BlogPosting + BreadcrumbList.
    article_schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical_url},
        "headline": title,
        "description": description,
        "image": [image_url],
        "datePublished": published_at,
        "dateModified": published_at,
        "author": {"@type": "Organization", "name": "The Yarn Nest"},
        "publisher": {"@type": "Organization", "name": "The Yarn Nest"},
        "articleSection": "Crochet Ideas",
        "inLanguage": "en"
    }
    breadcrumb_schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.theyarnnest.shop/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": "https://www.theyarnnest.shop/blog.html"},
            {"@type": "ListItem", "position": 3, "name": title, "item": canonical_url}
        ]
    }
    article_json = json.dumps(article_schema, ensure_ascii=False).replace("<", "\\u003c")
    breadcrumb_json = json.dumps(breadcrumb_schema, ensure_ascii=False).replace("<", "\\u003c")
    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{safe_title} | The Yarn Nest</title>
<meta name="description" content="{escape(description, quote=True)}">
<link rel="canonical" href="{canonical_url}">
<meta property="og:title" content="{safe_title}">
<meta property="og:description" content="{escape(description, quote=True)}">
<meta property="og:url" content="{canonical_url}">
<meta property="og:type" content="article">
<meta property="og:image" content="{image_url}">
<script type="application/ld+json">{article_json}</script>
<script type="application/ld+json">{breadcrumb_json}</script>
<link rel="stylesheet" href="css/style.css">  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-ZT8H6KLQH6"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-ZT8H6KLQH6');
  </script>
</head>
<body><div class="container"><a href="blog.html">Back to Blog</a>
<figure><img src="{escape(image_path, quote=True)}" alt="{safe_title}" style="max-width:100%;height:auto"></figure>
{article}
<p class="image-credit">Image source: <a href="{escape(credit_url, quote=True)}" rel="noopener noreferrer">Pixabay</a></p>
</div></body></html>"""
    post_file = ROOT / filename
    if post_file.exists():
        raise RuntimeError("Refusing to overwrite an existing post.")

    sitemap_path = ROOT / "sitemap.xml"
    if not sitemap_path.exists():
        raise RuntimeError("sitemap.xml not found; refusing to create a post without updating the sitemap.")
    sitemap = sitemap_path.read_text(encoding="utf-8")
    sitemap_entry = f"<url><loc>{canonical_url}</loc></url>"
    if canonical_url not in sitemap:
        if "</urlset>" not in sitemap:
            raise RuntimeError("sitemap.xml has no closing urlset element.")
        sitemap = sitemap.replace("</urlset>", f"  {sitemap_entry}\n</urlset>")

    post_file.write_text(page, encoding="utf-8")
    card = f"""
<!-- POST {post_number} - AUTO GENERATED -->
<article class="blog-card"><div class="blog-img">
<img src="{escape(image_path, quote=True)}" alt="{safe_title}">
<span class="blog-cat">Crochet Ideas</span></div>
<div class="blog-content"><span class="blog-date">{now.strftime("%B %d, %Y")}</span>
<h3><a href="{filename}">{safe_title}</a></h3><p>{escape(excerpt)}</p>
<a href="{filename}" class="read-more">Read Article</a>
<small>Image: <a href="{escape(credit_url, quote=True)}" rel="noopener noreferrer">Pixabay</a></small>
</div></article>
"""
    blog_path.write_text(blog[:grid_end] + card + blog[grid_end:], encoding="utf-8")
    sitemap_path.write_text(sitemap, encoding="utf-8")
    print(f"Created post {post_number}: {filename}; image: {image_path}; sitemap updated.")

if __name__ == "__main__":
    main()
