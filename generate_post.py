import os
import datetime
import re
from google import genai

# Gemini API سیٹ اپ
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# آج کی تاریخ
today = datetime.date.today().strftime("%Y-%m-%d")

# اے آئی سے ایچ ٹی ایم ایل بلاگ پوسٹ لکھوانے کے لیے پرامپٹ
prompt = """
You are an expert affiliate blogger for 'The Yarn Nest' (a blog about yarn, knitting, crochet, and plushies).
Write a complete, SEO-friendly blog post in HTML format (only return the inner HTML content for the body, like headings, paragraphs, and lists).
Topic: Choose a trending or popular topic about crochet hooks, chunky blankets, or yarn care.
Include:
1. Catchy Heading (<h1>)
2. Engaging introduction paragraphs (<p>)
3. Product review or guide with bullet points (<ul>/<li>)
4. An affiliate link placeholder like: <a href="#affiliate-link">Check Price on Amazon</a>
5. Conclusion (<p>)

Return ONLY valid HTML elements (no ```html code blocks, just raw HTML).
"""

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=prompt,
)

html_content = response.text.strip()
# اگر غلطی سے markdown code blocks آ جائیں تو انہیں ہٹا دیں
html_content = re.sub(r'^```html\s*', '', html_content)
html_content = re.sub(r'\s*```$', '', html_content)

# فائل کا نام بنانے کے لیے (مثلاً: best-yarn-for-beginners.html)
slug = "new-yarn-post-" + today
filename = f"{slug}.html"

# مکمل HTML پیج کا سانچہ (Template) جو آپ کے دوسرے صفحات سے ملتا جلتا ہو
full_page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Yarn Nest Blog</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header>
        <nav>
            <a href="blog.html">← Back to Blog</a>
        </nav>
    </header>
    <main style="padding: 20px; max-width: 800px; margin: auto;">
        {html_content}
    </main>
</body>
</html>
"""

# فائل کو محفوظ کریں
with open(filename, "w", encoding="utf-8") as f:
    f.write(full_page_html)

print(f"Successfully generated static HTML page: {filename}")
