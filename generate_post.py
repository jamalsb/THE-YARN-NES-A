
import os
import datetime
import time
import random
import re
from google import genai

# Gemini API Key حاصل کریں
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY is missing. Please check GitHub Secrets."
    )

client = genai.Client(api_key=api_key)


def generate_blog_post():

    prompt = """
    Write a complete, engaging blog post about modern crochet ideas
    and tips for handmade plushes.

    Requirements:
    - Write in clear, natural English.
    - Include a catchy title inside an <h1> tag.
    - Include an introduction.
    - Include 3-4 descriptive sections with <h2> subheadings.
    - Include a useful conclusion.
    - Use clean HTML tags.
    - Return ONLY the HTML article body.
    - Do not include markdown code fences.
    """

    # Gemini API کے لیے خودکار Retry System
    max_attempts = 5
    article_html = None

    for attempt in range(1, max_attempts + 1):

        try:
            print(
                f"Generating blog post... "
                f"Attempt {attempt}/{max_attempts}"
            )

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
            )

            article_html = response.text

            if not article_html or not article_html.strip():
                raise ValueError("Gemini returned an empty response.")

            # اگر AI نے HTML کو code fences میں دیا ہو
            article_html = article_html.strip()
            article_html = re.sub(
                r"^```(?:html)?\s*",
                "",
                article_html,
                flags=re.IGNORECASE
            )
            article_html = re.sub(
                r"\s*```$",
                "",
                article_html
            )

            print("Blog content generated successfully!")
            break

        except Exception as error:

            error_message = str(error).upper()

            retryable_errors = [
                "503",
                "429",
                "500",
                "502",
                "504",
                "UNAVAILABLE",
                "RESOURCE_EXHAUSTED",
                "INTERNAL",
                "DEADLINE_EXCEEDED",
                "TIMEOUT",
            ]

            should_retry = any(
                code in error_message
                for code in retryable_errors
            )

            if not should_retry:
                print(f"Non-retryable error: {error}")
                raise

            if attempt == max_attempts:
                print("All retry attempts failed.")
                raise

            wait_time = min(60, 5 * (2 ** (attempt - 1)))
            wait_time += random.uniform(0, 3)

            print(f"Temporary Gemini error: {error}")
            print(f"Retrying in {wait_time:.1f} seconds...")

            time.sleep(wait_time)

    if not article_html:
        raise RuntimeError("Blog generation failed.")

    # منفرد فائل کا نام
    today = datetime.datetime.now(
        datetime.timezone.utc
    ).strftime("%Y-%m-%d-%H-%M-%S")

    filename = f"post-{today}.html"

    # مکمل HTML پیج تیار کریں
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

    # HTML فائل محفوظ کریں
    with open(filename, "w", encoding="utf-8") as file:
        file.write(full_page_content)

    print(f"SUCCESS: New blog post saved as {filename}")


if __name__ == "__main__":
    generate_blog_post()
