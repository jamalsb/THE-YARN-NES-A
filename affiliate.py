"""Pick affiliate links for a new article from affiliate_links.json and render the HTML block.

The AI model never sees or writes affiliate URLs: links are inserted by this code only,
and only when an entry's keywords actually match the article's keywords.
"""
import json
from html import escape
from pathlib import Path

BANK = Path(__file__).resolve().parent / "affiliate_links.json"
DISCLOSURE = ("Affiliate disclosure: This article contains an affiliate link. If you buy through it, "
              "The Yarn Nest may earn a commission at no extra cost to you.")


def load_links(path=BANK):
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    links = []
    for item in data.get("links", []):
        if all(isinstance(item.get(k), str) and item[k].strip() for k in ("id", "name", "url")) \
                and item["url"].startswith("https://") and isinstance(item.get("keywords"), list):
            links.append(item)
    return links


def pick_links(primary, secondary, history_used, max_links=1, path=BANK):
    """Return up to max_links entries whose keywords appear in the article keywords.
    Ties prefer links used least in earlier generated posts, so one product is not repeated daily."""
    text = " ".join([primary] + list(secondary)).lower()
    usage = {}
    for entry in history_used:
        for link_id in entry.get("affiliate_ids", []):
            usage[link_id] = usage.get(link_id, 0) + 1
    scored = []
    for link in load_links(path):
        score = sum(1 for kw in link["keywords"] if isinstance(kw, str) and kw.strip() and kw.strip().lower() in text)
        if score:
            scored.append((-score, usage.get(link["id"], 0), link["id"], link))
    scored.sort(key=lambda row: row[:3])
    return [row[3] for row in scored[:max_links]]


def render_block(links):
    if not links:
        return ""
    cards = []
    for link in links:
        image = ""
        if isinstance(link.get("image"), str) and link["image"].startswith("https://"):
            image = (f'<img src="{escape(link["image"], quote=True)}" '
                     f'alt="{escape(link.get("image_alt") or link["name"], quote=True)}" loading="lazy">')
        cards.append(
            f'<div class="affiliate-product-card">{image}<div class="affiliate-product-info">'
            f'<h3>{escape(link["name"])}</h3>'
            f'<p>{escape(link.get("description", ""))}</p>'
            f'<a class="shop-now-button" href="{escape(link["url"], quote=True)}" target="_blank" '
            f'rel="sponsored nofollow noopener noreferrer">Shop Now</a>'
            f'<p class="affiliate-disclosure">{DISCLOSURE}</p></div></div>')
    return ('<section class="affiliate-product" aria-label="Recommended product">'
            '<h2>Recommended for This Project</h2>' + "".join(cards) + '</section>')
