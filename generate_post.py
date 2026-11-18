
import os
import re
import time
import random
import datetime
from html import escape, unescape
from html.parser import HTMLParser
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is missing in GitHub Secrets.")

client = genai.Client(api_key=api_key)


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self):
        return " ".join(self.parts)


def clean_text(content):
    parser = TextExtractor()
    parser.feed(content)
    return re.sub(r"\s+", " ", unescape(parser.get_text())).strip()


def generate_blog_post():
    prompt = """
    Write a complete, engaging blog post about modern crochet
    ideas and tips for handmade plushes.

    Requirements:
    - Write in clear natural English.
    - Include a catchy title inside an h1 tag.
    - Include an introduction.
    - Include 3-4 sections with h2 headings.
    - Include a useful conclusion.
    - Return only clean HTML article content.
    - Do not use Markdown code fences.
    """

    article_html = None

    for attempt in range(1, 6):
        try:
            print(f"Generating post: Attempt {attempt}/5")

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            article_html = response.text

            if not article_html or not article_html.strip():
                raise ValueError("Gemini returned an empty response.")

            article_html = re.sub(
                r"^```(?:html)?\s*|\s*```$",
                "",
                article_html.strip(),
                flags=re.IGNORECASE
            ).strip()

            break

        except Exception as error:
            message = str(error).upper()
            retry_codes = [
                "503", "429", "500", "502", "504",
                "UNAVAILABLE", "RESOURCE_EXHAUSTED",
                "INTERNAL", "TIMEOUT"
            ]

            if not any(code in message for code in retry_codes):
                raise

            if attempt == 5:
                raise

            wait = min(60, 5 * (2 ** (attempt - 1)))
            wait += random.uniform(0, 3)

            print(f"Temporary Gemini error. Waiting {wait:.1f}s")
            time.sleep(wait)

    if not article_html:
        raise RuntimeError("Post generation failed.")

    title_match = re.search(
        r"<h1\b[^>]*>(.*?)</h1>",
        article_html,
        flags=re.IGNORECASE | re.DOTALL
    )

    title = (
        clean_text(title_match.group(1))
        if title_match
        else "New Crochet Ideas and Tips"
    )

    safe_title = escape(title)

    excerpt = clean_text(article_html)
    if len(excerpt) > 160:
        excerpt = excerpt[:157].rsplit(" ", 1)[0] + "..."

    safe_excerpt = escape(excerpt)

    now = datetime.datetime.now(datetime.timezone.utc)
    filename = "post-" + now.strftime("%Y-%m-%d-%H-%M-%S") + ".html"
    date_text = now.strftime("%B %d, %Y")

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{safe_title}</title>
<link rel="stylesheet" href="css/style.css">
</head>
<body>
<div class="container">
<a href="blog.html">← Back to Blog</a>
{article_html}
</div>
</body>
</html>
"""

    with open(filename, "w", encoding="utf-8") as file:
        file.write(page)

    blog_path = "blog.html"
    marker = "<!-- END POST 6 -->"

    with open(blog_path, "r", encoding="utf-8") as file:
        blog_html = file.read()

    if filename not in blog_html:
        if marker not in blog_html:
            raise RuntimeError("Blog insertion marker was not found.")

        card = f"""
<article class="blog-card">
  <div class="blog-img">
    <img src="dot6.jpg" alt="{safe_title}">
    <span class="blog-cat">AI Crochet Guide</span>
  </div>
  <div class="blog-content">
    <span class="blog-date">{date_text}</span>
    <h3><a href="{filename}">{safe_title}</a></h3>
    <p>{safe_excerpt}</p>
    <a href="{filename}" class="read-more">Read Article →</a>
  </div>
</article>
"""

        blog_html = blog_html.replace(
            marker,
            marker + "\n" + card,
            1
        )

        with open(blog_path, "w", encoding="utf-8") as file:
            file.write(blog_html)

    print(f"SUCCESS: Created {filename}")
    print("Blog page updated successfully.")


if __name__ == "__main__":
    generate_blog_post()
