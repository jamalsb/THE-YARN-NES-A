import os
import datetime
from google import genai

# گٹ ہب سیکرٹس سے اے پی آئی کی حاصل کرنا
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def generate_blog_post():
    # 1. جেমینی سے بلاگ پوسٹ لکھوانا
    prompt = """
    Write a complete, engaging blog post about modern crochet ideas and tips for handmade plushes in clean HTML format. 
    It should include a catchy title inside an <h1> tag, an introduction, 3-4 descriptive sections with <h2> subheadings, and a conclusion.
    Return only the clean HTML content for the article body.
    """
    
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
    )
    
    article_html = response.text
    
    # 2. تاریخ کے حساب سے منفرد فائل کا نام بنانا
    today = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename = f"post-{today}.html"
    
    # 3. مکمل ایچ ٹی ایم ایل پیج کا ڈھانچہ تیار کرنا
    full_page_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Generated Crochet Post</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <a href="blog.html">← Back to Blog</a>
        {article_html}
    </div>
</body>
</html>
"""
    
    # 4. فائل کو گٹ ہب ریپوزٹری میں محفوظ کرنا
    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_page_content)
        
    print(f"New blog post saved as: {filename}")

if __name__ == "__main__":
    generate_blog_post()
