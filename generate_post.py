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

def pixabay_image(search_query):
    cache_key = re.sub(r"[^a-z0-9]+", "-", search_query.lower()).strip("-")[:60] or "yarn-crafts"
    cache = ROOT / ".cache" / f"pixabay-{cache_key}.json"
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
            "key": PIXABAY_KEY, "q": search_query,
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
                r'href="(https?://(?:www\.)?pixabay\.com/[^"]+)',
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
    name = f"yarn-craft-{stamp}.jpg"
    response = requests.get(image_url, timeout=45)
    response.raise_for_status()
    (folder / name).write_bytes(response.content)
    return "images/" + name, credit_url

def main():
    # Select the next unused long-tail keyword candidate. These candidates are not live competition metrics.
    bank_path = ROOT / "keyword_bank.json"
    history_path = ROOT / "keyword_history.json"
    if not bank_path.exists():
        raise RuntimeError("keyword_bank.json is missing.")
    bank = json.loads(bank_path.read_text(encoding="utf-8"))
    history = json.loads(history_path.read_text(encoding="utf-8")) if history_path.exists() else {"used": []}
    used = {item.get("primary", "").strip().lower() for item in history.get("used", [])}
    def is_verified(item):
        evidence = item.get("verification") or {}
        difficulty = evidence.get("organic_difficulty")
        volume = evidence.get("monthly_searches")
        return (
            item.get("status") == "verified"
            and isinstance(evidence.get("source"), str) and evidence["source"].strip()
            and isinstance(evidence.get("checked_at"), str) and evidence["checked_at"].strip()
            and isinstance(volume, (int, float)) and volume >= 0
            and isinstance(difficulty, (int, float)) and 0 <= difficulty <= 30
            and isinstance(evidence.get("search_intent"), str) and evidence["search_intent"].strip()
            and evidence.get("serp_review") is True
        )
    candidates = [
        item for item in bank.get("keywords", [])
        if item.get("primary", "").strip().lower() not in used and is_verified(item)
    ]
    if not candidates:
        raise RuntimeError(
            "SAFE STOP: No unused keyword has verified evidence. "
            "No article was generated or published. Verify a keyword first "
            "(organic_difficulty 0-30, source, checked_at, monthly_searches, "
            "search_intent, and serp_review=true)."
        )
    keyword = candidates[0]
    primary_keyword = keyword["primary"]
    secondary_keywords = keyword.get("secondary", [])

    knowledge_path = ROOT / "yarn_knowledge_base.md"
    knowledge_base = ""
    if knowledge_path.exists():
        knowledge_base = knowledge_path.read_text(encoding="utf-8")[:24000]

    prompt = f"""You are the senior human-style editor and specialist craft writer for The Yarn Nest, an English-language craft publication for readers in the United States.
Your job is to produce genuinely useful, accurate, original editorial content, not generic AI-sounding filler.

EDITORIAL VOICE:
- Sound like a skilled, thoughtful human craft instructor speaking clearly to a real beginner or hobbyist.
- Use natural sentence rhythm and varied paragraph lengths. Be warm, practical, specific, and confident without sounding salesy.
- Avoid robotic openings, generic claims, repetitive transitions, empty enthusiasm, fake personal anecdotes, and phrases such as "In today's world", "Let's dive in", "Whether you're a seasoned crafter", "unleash your creativity", or "the possibilities are endless".
- Do not mention AI, language models, prompts, or that the article was generated.
- Do not pretend to have personally tested a yarn, hook, kit, pattern, or technique. Never invent first-hand experience, quotes, reviews, measurements, or results.
- Prefer concrete useful details over inflated word count. Every paragraph must help the reader understand, choose, make, fix, or care for something.

SUBJECT KNOWLEDGE AND ACCURACY:
- Use the supplied knowledge base as background, not as a source to copy. If it does not contain enough reliable information, keep claims conservative and identify what needs checking rather than guessing.
- Keep crochet, knitting, weaving, macrame, and other yarn crafts technically distinct. Do not describe one technique as another.
- Explain unfamiliar terms briefly on first use. Give practical steps in the correct order when the topic is a tutorial.
- Do not invent yarn fiber properties, hook/needle sizes, gauge, care instructions, safety claims, or product specifications. State that readers should check the yarn label or pattern where details depend on a specific product.
- Do not give unsafe advice for projects involving children; mention age-appropriate supervision when relevant.

SEO AND SEARCH INTENT:
- Primary keyword: "{primary_keyword}"
- Related keywords: {", ".join(secondary_keywords)}
- Match the likely search intent exactly. Do not force every related keyword into the article; use only terms that fit naturally and help the reader.
- Include the exact primary keyword naturally in the H1, first 100 words, SEO description, and one relevant subheading when it reads naturally.
- Use relevant secondary phrases in suitable H2/H3 headings and body copy without keyword stuffing or awkward repetition.
- Add helpful synonyms and related entities naturally, but never repeat keywords just to increase density.
- Write for people first. Avoid over-optimizing, keyword lists in paragraphs, or unnatural exact-match repetition.
- Do not make ranking guarantees or claims about search volume or difficulty in the article.

ARTICLE STRUCTURE:
- Return one compelling, accurate H1 title containing the primary keyword.
- Start with a useful introduction that quickly answers what the reader will learn and who the guide is for. Avoid generic hooks.
- Use 4-7 descriptive H2 sections in a logical order. Add H3s only when they improve navigation.
- For tutorials, include materials/tools only when relevant, realistic step-by-step instructions, common mistakes and fixes, and practical finishing/care advice where appropriate.
- Include a concise FAQ section with 3-5 questions that genuinely match reader questions. Do not repeat the same answer in different wording.
- End with a useful conclusion and a natural next step.
- Aim for 900-1,300 words only when the topic supports that depth. A shorter complete answer is better than padding.
- Use US English spelling and measurements where relevant, while preserving standard crochet terminology and explaining alternatives when useful.
- Return clean semantic HTML only: h1, h2, h3, p, ul, ol, li, strong, em. No Markdown fences, no outer html/head/body tags, no invented citations.

META DESCRIPTION:
- Write a clear, accurate meta description of 140-160 characters containing the primary keyword naturally.
- Return it in an HTML comment exactly like: <!-- SEO_DESCRIPTION: your description here -->

INTERNAL KNOWLEDGE BASE:
{knowledge_base}

Return only the finished article HTML and the required SEO_DESCRIPTION comment.
"""

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
    if primary_keyword.lower() not in title.lower():
        raise RuntimeError(f"Generated H1 does not contain the selected primary keyword: {primary_keyword}")
    safe_title = escape(title)
    description_match = re.search(r"<!--\s*SEO_DESCRIPTION:\s*(.*?)\s*-->", article, re.I | re.S)
    if not description_match:
        raise RuntimeError("Gemini response did not include the required SEO_DESCRIPTION comment.")
    description = plain(description_match.group(1))
    if not (120 <= len(description) <= 180):
        raise RuntimeError(f"SEO description length is outside the accepted range: {len(description)} characters")
    article = re.sub(r"<!--\s*SEO_DESCRIPTION:.*?-->", "", article, flags=re.I | re.S).strip()
    excerpt = plain(article)
    excerpt = excerpt[:157].rsplit(" ", 1)[0] + "..." if len(excerpt) > 160 else excerpt

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
    image_query = primary_keyword + " yarn craft"
    image_path, credit_url = pixabay_image(image_query)
    image_url = "https://www.theyarnnest.shop/" + image_path
    published_at = now.isoformat(timespec="seconds").replace("+00:00", "Z")

    # Structured data for search engines: BlogPosting + BreadcrumbList.
    article_schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical_url},
        "headline": title,
        "description": description,
        "keywords": ", ".join([primary_keyword] + secondary_keywords),
        "image": [image_url],
        "datePublished": published_at,
        "dateModified": published_at,
        "author": {"@type": "Organization", "name": "The Yarn Nest"},
        "publisher": {"@type": "Organization", "name": "The Yarn Nest"},
        "articleSection": "Yarn Crafts",
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
<span class="blog-cat">Yarn Crafts</span></div>
<div class="blog-content"><span class="blog-date">{now.strftime("%B %d, %Y")}</span>
<h3><a href="{filename}">{safe_title}</a></h3><p>{escape(excerpt)}</p>
<a href="{filename}" class="read-more">Read Article</a>
<small>Image: <a href="{escape(credit_url, quote=True)}" rel="noopener noreferrer">Pixabay</a></small>
</div></article>
"""
    blog_path.write_text(blog[:grid_end] + card + blog[grid_end:], encoding="utf-8")
    sitemap_path.write_text(sitemap, encoding="utf-8")
    history.setdefault("used", []).append({
        "primary": primary_keyword,
        "secondary": secondary_keywords,
        "title": title,
        "file": filename,
        "published_at": published_at
    })
    history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created post {post_number}: {filename}; primary keyword: {primary_keyword}; image: {image_path}; sitemap updated.")

if __name__ == "__main__":
    main()
