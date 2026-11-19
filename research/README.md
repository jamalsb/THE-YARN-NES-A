# The Yarn Nest: Automated Research

This workflow runs weekly on Sunday at 10:00 UTC and can also be started manually from GitHub Actions.

## What it does
- Uses the existing `GEMINI_API_KEY` GitHub Actions secret.
- Uses the Gemini API with Google Search grounding to discover new US-focused yarn, crochet, knitting, weaving, macrame, material, tool, and tutorial topics.
- Avoids phrases already present in `keyword_bank.json` and previously discovered research.
- Stores new ideas in `research/discovered_keywords.json` and a readable history in `research/ongoing-research.md`.
- Records grounding source links returned by Google Search when available.

## Safety and publishing separation
- This workflow is research-only. It never creates articles, edits the blog index, changes the sitemap, or publishes content.
- New ideas are always marked `candidate_unverified`.
- Search volume and organic keyword difficulty remain null until checked with a dedicated SEO data provider.
- The weekly research workflow is separate from `.github/workflows/auto-blog.yml`. The blog-publishing workflow remains manual-only and the article generator still requires human-entered verification evidence before it can generate an article.
- Gemini/Google Search topic discovery is not a substitute for Ahrefs/other SEO provider metrics or a manual SERP review.

## Required GitHub secret
- `GEMINI_API_KEY`: the same Gemini API key already used by the article generator.
