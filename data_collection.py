"""
Downloads Guardian articles for each target section and saves them into:
data/<section_name>/*.txt

Each .txt has a header + BODY  + metadata + tags + section info that sensing.py can parse.

Using the guardian API, we can get the articles for each section. 
With the following fields:
    - Article metadata
ID - A unique identifier for the article in The Guardian system
SECTION_ID - The internal Guardian code of the section the article belongs to (e.g., sport, culture, commentisfree).
SECTION_NAME - The human-readable name of the section (e.g., Sport, Culture, Comment is Free [the internal name for the section]).
WEB_TITLE - The title of the article as displayed on the Guardian website.
WEB_URL - The full URL of the article on the Guardian website.
HEADLINE - The main headline of the article.
TRAIL_TEXT - A short summary or excerpt from the article.
BYLINE - The author or byline of the article.
BODY_TEXT - The full text of the article.
TAGS_IDS - A list of unique identifiers for the tags associated with the article.
TAGS_TITLES - A list of human-readable names for the tags associated with the article.
PRIMARY_TAG_ID - The unique identifier of the primary tag associated with the article.
PRIMARY_TAG_TITLE - The human-readable name of the primary tag associated with the article.
PRIMARY_TAG_TYPE - The type of the primary tag (e.g., keyword, topic, section).

"""

from theguardian import theguardian_content
from dotenv import load_dotenv
from pathlib import Path
import os
import time

# Maps HW categories to Guardian section IDs
SECTIONS = {
    "news": "news",
    "sport": "sport",
    "opinion": "commentisfree",
    "culture": "culture",
}

ARTICLES_PER_SECTION = 1000
PAGE_SIZE = 50
SLEEP_BETWEEN_CALLS = 0.2 #for correct API usage

def get_api_key():
    load_dotenv()
    key = os.getenv("GUARDIAN_API_KEY")
    if not key:
        raise RuntimeError("GUARDIAN_API_KEY missing from .env")
    return key

def join_csv(values: list[str]) -> str:
    return ",".join(values) if values else ""


def format_article(article: dict):
    fields = article.get("fields", {}) or {}
    tags = article.get("tags", []) or []

    body_text = fields.get("bodyText", "") or ""

    tag_ids = [tag.get("id", "") for tag in tags]
    tag_titles = [tag.get("title", "") for tag in tags]

    primary_tag = tags[0] if tags else None
    primary_id = primary_tag.get("id", "") if primary_tag else ""
    primary_title = primary_tag.get("title", "") if primary_tag else ""
    primary_type = primary_tag.get("type", "") if primary_tag else ""

    # Header lines, EXACT field names as requested by sensing.py
    lines = [
        f"ID: {article.get('id', '')}",
        f"SECTION_ID: {article.get('sectionId', '')}",
        f"SECTION_NAME: {article.get('sectionName', '')}",
        f"WEB_TITLE: {article.get('webTitle', '')}",
        f"WEB_URL: {article.get('webUrl', '')}",

        f"HEADLINE: {fields.get('headline', '')}",
        f"TRAIL_TEXT: {fields.get('trailText', '')}",
        f"BYLINE: {fields.get('byline', '')}",
        f"BODY_TEXT: {body_text}",

        f"TAGS_IDS: {join_csv(tag_ids)}",
        f"TAGS_TITLES: {join_csv(tag_titles)}",
        f"PRIMARY_TAG_ID: {primary_id}",
        f"PRIMARY_TAG_TITLE: {primary_title}",
        f"PRIMARY_TAG_TYPE: {primary_type}",
    ]

    return "\n".join(lines)



def collect_section(api_key, base: Path, target_name, gurdian_id):
    print(f"\nCollecting {target_name} section ({gurdian_id}), (Gurdian_ID: {gurdian_id})")

    out_dir = base / target_name
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    page = 1

    while count < ARTICLES_PER_SECTION:
        content = theguardian_content.Content(
            api=api_key,
            section=gurdian_id,
            page_size=PAGE_SIZE,
            page=page,
            show_fields="all",
            order_by="newest",
            show_tags="all",
            )
	
        json_data = content.get_content_response()
        results = content.get_results(json_data)
        if not results:
            print(f"No results found for page {page}")
            break
        
        for article in results:
            if count >= ARTICLES_PER_SECTION:
                break
        
        art_id = article.get("id", "").replace("/", "_") or f"{target_name}_{page}_{count}"
        out_path = out_dir / f"{art_id}.txt" 
        
        if out_path.exists():
            continue #skip if already exists
        formatted_content = format_article(article)
        out_path.write_text(formatted_content, encoding='utf-8')
        count += 1 #increment count

        if count >= ARTICLES_PER_SECTION:
            break
        page += 1 #increment page
        time.sleep(SLEEP_BETWEEN_CALLS) #sleep to avoid rate limiting

    print(f"Collected {count} articles for {target_name})")


def main():
    api_key = get_api_key()
    base = Path("data")
    for target_name, gurdian_id in SECTIONS.items():
        collect_section(api_key, base, target_name, gurdian_id)

if __name__ == "__main__":
    main()
