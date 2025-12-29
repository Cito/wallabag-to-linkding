#!/usr/bin/env python3

"""
Load Wallabag JSON export file into linkding via REST API.
"""


import json
import os
import time
import warnings

try:
    import httpx
except ImportError as e:
    raise ImportError("Please install httpx") from e


JSON_FILE = 'All articles.json'

API_TOKEN = '...'
API_URL = 'http://localhost:9090'

HTTP_TIMEOUT_SECONDS = 60
WAIT_BETWEEN_REQUESTS_SECONDS = 3


def load_json_file():
    json_file = os.environ.get('WALLABAG_JSON_FILE') or JSON_FILE
    if not json_file or not os.path.isfile(JSON_FILE):
        raise RuntimeError("No Wallabag JSON file")
    with open(json_file) as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise RuntimeError("Wallabag JSON file is not a list")
    return data


def get_client():
    url = os.environ.get('LINKDING_API_URL') or API_URL
    if not url or not url.startswith(('http://', 'https://')):
        raise RuntimeError("No linkding API URL")
    token = os.environ.get('LINKDING_API_TOKEN') or API_TOKEN
    if not token or len(token) != 40 or not token.isalnum():
        raise RuntimeError("No linkding API token")
    return httpx.Client(
        base_url=url,
        headers={"Authorization": f"Token {token}"},
        timeout=HTTP_TIMEOUT_SECONDS,
    )


def make_bookmark(entry):
    archived = bool(entry.get("is_archived"))
    shared = bool(entry.get("is_public"))
    tags = [tag.lower() for tag in entry.get("tags", [])]
    url = entry.get("url")
    if not url or not url.startswith(('http://', 'https://')):
        warnings.warn(f"Invalid URL: {url}")
        return None
    title = entry.get("title") or None
    return {
        "url": url,
        "title": title,
        "tag_names": tags,
        "unread": not archived,
        "is_archived": archived,
        "shared": shared,
    }


def post_bookmark(client, payload):
    response = client.post("/api/bookmarks/", json=payload)
    url = payload['url']
    response.raise_for_status()
    posted = response.json()
    bookmark_id = posted.get("id")
    if not bookmark_id or not posted.get("url"):
        raise RuntimeError(f"Failed to post bookmark: {url}")
    return bookmark_id


def get_asset(entry):
    content = (entry.get("content") or '').strip()
    if not content:
        return None
    head = content[:32].lower()
    if not (head.startswith('<!doctype') or '<html' in head):
        content = (
            "<!DOCTYPE html>\n"
            '<html><head><meta charset="utf-8"></head>\n'
            f"<body>{content}</body>\n</html>"
        )
    return content.encode("utf-8")


def post_asset(client, bookmark_id, name, asset):
    mime_type = "text/html"
    file_tuple = (name, asset, mime_type)
    files = {"file": file_tuple}
    url = f"/api/bookmarks/{bookmark_id}/assets/upload/"
    response = client.post(url, files=files)
    response.raise_for_status()
    posted = response.json()
    asset_id = posted.get("id")
    if not asset_id or not posted.get("file_size"):
        raise RuntimeError(
            f"Failed to post asset for bookmark ID: {bookmark_id}")
    return bookmark_id


def main():
    client = get_client()
    entries = load_json_file()
    num_entries = len(entries)
    wait_time = WAIT_BETWEEN_REQUESTS_SECONDS
    for num, entry in enumerate(reversed(entries)):
        payload = make_bookmark(entry)
        if not payload:
            continue
        print(f"Importing {num + 1}/{num_entries}: {payload['url']}")
        bookmark_id = post_bookmark(client, payload)
        asset = get_asset(entry)
        if asset:
            name = 'Page content'
            created_at = entry.get("created_at")
            if created_at:
                name += f" ({created_at[:10]})"
            print("Importing asset for bookmark", bookmark_id)
            post_asset(client, bookmark_id, name, asset)
        if wait_time:
            time.sleep(wait_time)


if __name__ == "__main__":
    main()
