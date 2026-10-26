"""Extract microbe–metabolite links from data/passages.json.

Uses a free local model through Ollama. No API key.
Run: python3 scripts/extract_links.py
"""

import json
import urllib.error
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PASSAGES_FILE = DATA_DIR / "passages.json"
LINKS_FILE = DATA_DIR / "links.json"
MODEL = "qwen2.5:3b"
URL = "http://127.0.0.1:11434/api/chat"


def normalize(text):
    return " ".join(text.split()).lower()


def relation_name(value):
    value = value.lower()
    if "produc" in value:
        return "produces"
    if "consum" in value or "util" in value:
        return "consumes"
    if "convert" in value:
        return "converts"
    return ""


def ask(passage_text):
    prompt = (
        "Extract microbe-metabolite links this passage explicitly states.\n"
        'Return JSON: {"links": [{"microbe": "", "metabolite": "", '
        '"relation": "produces or consumes or converts", "quote": ""}]}\n'
        "Copy the quote from the passage. "
        'If there is no link, return {"links": []}.\n\n'
        f"Passage:\n{passage_text}"
    )
    body = json.dumps(
        {
            "model": MODEL,
            "stream": False,
            "format": "json",
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode()
    request = urllib.request.Request(
        URL, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        payload = json.loads(response.read())
    parsed = json.loads(payload["message"]["content"])
    if isinstance(parsed, list):
        return parsed
    return parsed.get("links", [])


def clean_links(raw_links, passage, index):
    passage_norm = normalize(passage["text"])
    cleaned = []
    for item in raw_links:
        if not isinstance(item, dict):
            continue
        microbe = str(item.get("microbe", "")).strip()
        metabolite = str(item.get("metabolite", "")).strip()
        relation = relation_name(str(item.get("relation", "")))
        quote = " ".join(str(item.get("quote", "")).split())
        if not (microbe and metabolite and relation and quote):
            continue
        if normalize(quote) not in passage_norm:
            continue
        cleaned.append(
            {
                "pmcid": passage["pmcid"],
                "passage_index": index,
                "microbe": microbe,
                "metabolite": metabolite,
                "relation": relation,
                "quote": quote,
            }
        )
    return cleaned


def load_progress():
    if not LINKS_FILE.exists():
        return set(), []
    saved = json.loads(LINKS_FILE.read_text())
    return set(saved.get("completed", [])), saved.get("links", [])


def save_progress(completed, links):
    LINKS_FILE.write_text(
        json.dumps({"completed": sorted(completed), "links": links}, indent=2)
    )


def main():
    passages = json.loads(PASSAGES_FILE.read_text())
    completed, links = load_progress()
    for index, passage in enumerate(passages):
        if index in completed:
            continue
        try:
            raw_links = ask(passage["text"])
        except urllib.error.URLError:
            print("Ollama is not running. Start it with: ollama serve")
            save_progress(completed, links)
            return
        found = clean_links(raw_links, passage, index)
        links.extend(found)
        completed.add(index)
        save_progress(completed, links)
        print(f"{index + 1}/{len(passages)} {passage['pmcid']}: {len(found)} links")
    print(f"wrote {len(links)} links to {LINKS_FILE}")


if __name__ == "__main__":
    main()
