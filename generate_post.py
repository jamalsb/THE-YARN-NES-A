import os
from google import genai

# جেমینی کلائنٹ کو اے پی آئی کی کے ساتھ سیٹ کرنا
client = genai.Client(api_key="آپ_کی_یہاں_اصل_اے_پی_آی_کی_آئےگی")

def generate_blog_post():
    prompt = """
    Write a complete, engaging blog post about modern crochet ideas and tips for handmade plushes in HTML format. 
    It should include a catchy title, introduction, 3-4 descriptive sections with subheadings, and a conclusion.
    Return only the clean HTML content for the article body.
    """
    
    # جেমینی ماڈل سے آرٹیکل لکھوانا
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    
    article_html = response.text
    print("New article generated successfully!")
    
    # یہاں ہم اس آرٹیکل کو ایک نئی ایچ ٹی ایم ایل فائل میں محفوظ کر سکتے ہیں
    # یا اپنے بلاگ انڈیکس میں ایڈ کر سکتے ہیں

if __name__ == "__main__":
    generate_blog_post()
    
