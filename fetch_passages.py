"""Fetch the papers in data/papers.txt and save them as short passages.

Run: python3 fetch_passages.py
"""

import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
PAPERS_FILE = DATA_DIR / "papers.txt"
OUTPUT_FILE = DATA_DIR / "passages.json"
PASSAGE_SIZE = 800


def tag_name(element):
    return element.tag.split("}")[-1]


def find_one(root, name):
    for element in root.iter():
        if tag_name(element) == name:
            return element
    return None


def paragraph_text(element):
    return " ".join(" ".join(element.itertext()).split())


def split_text(text):
    """Cut a long paragraph into pieces of about PASSAGE_SIZE characters."""
    pieces = []
    rest = text
    while len(rest) > PASSAGE_SIZE:
        cut = rest.rfind(". ", 0, PASSAGE_SIZE)
        if cut < PASSAGE_SIZE // 2:
            cut = PASSAGE_SIZE
        else:
            cut += 1
        pieces.append(rest[:cut].strip())
        rest = rest[cut:].strip()
    if rest:
        pieces.append(rest)
    return pieces


def fetch_article(pmcid):
    numeric_id = pmcid.removeprefix("PMC")
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        f"?db=pmc&id={numeric_id}&retmode=xml"
    )
    request = urllib.request.Request(url, headers={"User-Agent": "microbelinks-prototype"})
    with urllib.request.urlopen(request) as response:
        return ET.fromstring(response.read())


def passages_from_paper(pmcid):
    article = fetch_article(pmcid)
    title_element = find_one(article, "article-title")
    title = paragraph_text(title_element) if title_element is not None else pmcid

    sections = [find_one(article, "abstract"), find_one(article, "body")]
    if sections[1] is None:
        print(f"{pmcid}: full text is not available, using the abstract")

    passages = []
    for section in sections:
        if section is None:
            continue
        for element in section.iter():
            if tag_name(element) != "p":
                continue
            text = paragraph_text(element)
            if len(text) < 80:
                continue
            for piece in split_text(text):
                passages.append({"pmcid": pmcid, "title": title, "text": piece})
    return passages


def main():
    pmcids = [line.strip() for line in PAPERS_FILE.read_text().splitlines() if line.strip()]
    passages = []
    for pmcid in pmcids:
        found = passages_from_paper(pmcid)
        print(f"{pmcid}: {len(found)} passages")
        passages.extend(found)

    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(passages, indent=2))
    print(f"wrote {len(passages)} passages to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
