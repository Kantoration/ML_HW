import pandas as pd
from pathlib import Path

OUTPUT_CSV_NAME = "sensed_data.csv"
DATA_ROOT = Path("data")

def parse_article(file_path: Path) -> dict:
    """	
    for each article in the txt file, parse the header, body, metadata, tags, and section info.
    return a dictionary
    """	
    article_data = {}
    article_data["label"]= file_path.parent.name
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

    lines = content.strip().split("\n")
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            article_data[key] = value

    return article_data

def main():
    for file_path in DATA_ROOT.rglob("*.txt"):
        article_data = parse_article(file_path)
        print(article_data)

if __name__ == "__main__":
    main()
