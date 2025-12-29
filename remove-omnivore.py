#!/usr/bin/env python3

"""
Remove Omnivore proxy metadata from content in Wallabag JSON export file.
"""


import json
import os

from bs4 import BeautifulSoup

JSON_FILE = 'All articles.json'


def load_json_file():
    json_file = os.environ.get('WALLABAG_JSON_FILE') or JSON_FILE
    if not json_file or not os.path.isfile(JSON_FILE):
        raise RuntimeError("No Wallabag JSON file")
    with open(json_file) as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise RuntimeError("Wallabag JSON file is not a list")
    return data


def save_json_file(data):
    if not isinstance(data, list):
        raise RuntimeError("Wallabag JSON file is not a list")
    json_file = os.environ.get('WALLABAG_JSON_FILE') or JSON_FILE
    if not json_file or not os.path.isfile(JSON_FILE):
        raise RuntimeError("No Wallabag JSON file")
    json_file = json_file.replace('.json', ' cleaned.json')
    with open(json_file, 'w') as f:
        json.dump(data, f)


def fix_content(content):
    soup = BeautifulSoup(content, "html.parser")

    for tag in soup.find_all("source"):
        tag.decompose()

    for tag in soup.find_all(
            attrs={"data-omnivore-anchor-idx": True}):
        del tag["data-omnivore-anchor-idx"]

    for tag in soup.find_all(
            attrs={"data-omnivore-original-src": True, "src": True}):
        tag["src"] = tag["data-omnivore-original-src"]
        del tag["data-omnivore-original-src"]

    return str(soup)


def main():
    print("Loading Wallabag JSON file...")
    entries = load_json_file()
    num_entries = len(entries)
    for num, entry in enumerate(entries):
        content = entry.get("content") or None
        if not content or 'data-omnivore-anchor-idx' not in content:
            continue
        print(f"Fixing {num + 1}/{num_entries}")
        content = fix_content(content)
        entry["content"] = content
    print("Saving cleaned JSON file...")
    save_json_file(entries)


if __name__ == "__main__":
    main()
