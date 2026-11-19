import json
import os
import re
import datetime
from pathlib import Path

from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parent
RESEARCH_DIR = ROOT / "research"
DISCOVERED_PATH = RESEARCH_DIR / "discovered_keywords.json"
LOG_PATH = RESEARCH_DIR / "ongoing-research.md"
BANK_PATH = ROOT / "keyword_bank.json"

MODEL = os.getenv("GEMINI_RESEARCH_MODEL", "gemini-3.8-flash")
COUNTRY = "United States"

def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def extract_json(text):
    cleaned = re.sub(r"^\x60\x60\x60(?:json)?\s*|\s*\x60\x60\x60$", "", text.strip(), flags=re.I)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("Gemini research response did not contain a JSON object.")
    return json.loads(cleaned[start:end + 1])

def grounding_sources(response):
    found = []
    try:
        for candidate in response.candidates or []:
            metadata = getattr(candidate, "grounding_metadata", None)
            for chunk in (getattr(metadata, "grounding_chunks", None) or []):
                web = getattr(chunk, "web", None)
                uri = getattr(web, "uri", None) if web else None
                title = getattr(web, "title", None) if web else None
                if uri and uri.startswith("http"):
                    item = {"title": title or uri, "url": uri}
                    if item not in found:
                        found.append(item)
    except Exception as exc:
        print(f"Could not read optional grounding metadata: {exc}")
    return found

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY secret is required for scheduled research.")

    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    bank = load_json(BANK_PATH, {"keywords": []})
    existing = load_json(DISCOVERED_PATH, {"keywords": []})
    known = set()
    for item in bank.get("keywords", []):
        known.add(str(item.get("primary", "")).strip().lower())
        known.update(str(x).strip().lower() for x in item.get("secondary", []))
    for item in existing.get("keywords", []):
        known.add(str(item.get("keyword", "")).strip().lower())

    client = genai.Client(api_key=api_key)
    prompt = f"""
You are a careful research assistant for The Yarn Nest, an English-language educational blog for US readers about yarn crafts, crochet, knitting, weaving, macrame, yarn materials, tools, beginner tutorials, and handmade projects.

Use Google Search to discover genuinely useful and timely or evergreen content opportunities relevant to this blog. Research the United States audience and use US English. Explore multiple related subtopics, including questions beginners ask, practical problems, project ideas, seasonal craft interests, yarn types, and technique explanations.

Already known phrases (do not return duplicates or close spelling variants):
{json.dumps(sorted(known), ensure_ascii=False)}

Return ONLY one valid JSON object with this exact shape:
{{
  "research_summary": "short summary of what was researched",
  "keywords": [
    {{
      "keyword": "natural English search phrase",
      "category": "crochet|yarn crafts|knitting|weaving|macrame|yarn materials|tools|care|other",
      "search_intent": "informational|commercial investigation|transactional",
      "why_useful": "specific reader need this could answer",
      "suggested_article_angle": "specific, non-generic article angle",
      "seasonality": "evergreen or specify season",
      "evidence_note": "brief evidence-based note; do not claim search volume or KD"
    }}
  ]
}}

Return at most 15 genuinely distinct keyword ideas. Prefer specific long-tail questions and useful tutorial topics over broad head terms. Keep all ideas tightly relevant to The Yarn Nest. Exclude local-store queries, unrelated topics, brand-targeting ideas, and trademark-led content. Do not invent search-volume figures, keyword-difficulty scores, trend percentages, or claims that a keyword is easy to rank for. Google Search results can support topic discovery, but they do NOT provide reliable monthly search volume or SEO difficulty metrics. If evidence is weak, say so in evidence_note. Do not copy competitor article text.
"""
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=1.0,
        ),
    )
    if not response.text:
        raise RuntimeError("Gemini returned an empty research response.")
    result = extract_json(response.text)
    sources = grounding_sources(response)
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    new_items = []
    seen_this_run = set()
    for raw in result.get("keywords", []):
        phrase = re.sub(r"\s+", " ", str(raw.get("keyword", "")).strip())
        key = phrase.lower()
        if not phrase or key in known or key in seen_this_run:
            continue
        if len(phrase) > 120:
            continue
        seen_this_run.add(key)
        new_items.append({
            "keyword": phrase,
            "category": str(raw.get("category", "other")),
            "search_intent": str(raw.get("search_intent", "informational")),
            "why_useful": str(raw.get("why_useful", "")),
            "suggested_article_angle": str(raw.get("suggested_article_angle", "")),
            "seasonality": str(raw.get("seasonality", "evergreen")),
            "evidence_note": str(raw.get("evidence_note", "")),
            "target_country": "US",
            "discovered_at": today,
            "status": "candidate_unverified",
            "search_volume": None,
            "organic_keyword_difficulty": None,
            "sources": sources,
        })

    # Keep all discoveries, deduplicated, without changing verified keyword-bank entries.
    existing_items = existing.get("keywords", [])
    old_keys = {str(x.get("keyword", "")).strip().lower() for x in existing_items}
    for item in new_items:
        if item["keyword"].lower() not in old_keys:
            existing_items.append(item)
            old_keys.add(item["keyword"].lower())
    existing["keywords"] = existing_items
    existing["last_researched_at"] = today
    existing["target_country"] = COUNTRY
    DISCOVERED_PATH.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    log = LOG_PATH.read_text(encoding="utf-8") if LOG_PATH.exists() else "# The Yarn Nest: Ongoing Keyword & Topic Research\n\nResearch-only log. Candidate ideas are not verified SEO metrics and never trigger publishing.\n"
    log += f"\n## Research run: {today}\n\n"
    log += f"{result.get('research_summary', 'Gemini research completed.')}\n\n"
    if new_items:
        for item in new_items:
            log += f"### {item['keyword']}\n"
            log += f"- Category: {item['category']}\n- Search intent: {item['search_intent']}\n"
            log += f"- Article angle: {item['suggested_article_angle']}\n"
            log += f"- Why useful: {item['why_useful']}\n"
            log += f"- Evidence note: {item['evidence_note']}\n"
            log += "- Status: candidate_unverified; US volume and organic KD not measured.\n\n"
    else:
        log += "No new distinct candidates were added in this run.\n\n"
    if sources:
        log += "Grounding sources returned by Google Search:\n"
        for source in sources:
            log += f"- [{source['title']}]({source['url']})\n"
        log += "\n"
    LOG_PATH.write_text(log, encoding="utf-8")
    print(f"Research completed for {COUNTRY}. Added {len(new_items)} new candidate keywords. No blog content was generated or published.")

if __name__ == "__main__":
    main()
