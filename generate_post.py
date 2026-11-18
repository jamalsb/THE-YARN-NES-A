import os
from google import genai

# یہ لائن خود بخود گٹ ہب سیکرٹس سے آپ کی GEMINI_API_KEY اٹھا لے گی
api_key = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

def generate_blog_post():
    prompt = """
    Write a complete, engaging blog post about modern crochet ideas and tips for handmade plushes in HTML format. 
    It should include a catchy title, introduction, 3-4 descriptive sections with subheadings, and a conclusion.
    Return only the clean HTML content for the article body.
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    
    article_html = response.text
    print("New article generated successfully!")

if __name__ == "__main__":
    generate_blog_post()
    
