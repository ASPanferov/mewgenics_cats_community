"""Vercel Blob storage for generated images."""

import os
import requests as http_requests

BLOB_TOKEN = os.environ.get("BLOB_READ_WRITE_TOKEN", "")
BLOB_API = "https://blob.vercel-storage.com"


def upload_blob(filename, data, content_type="image/png"):
    """Upload bytes to Vercel Blob. Returns public URL or None."""
    if not BLOB_TOKEN:
        return None

    resp = http_requests.put(
        f"{BLOB_API}/{filename}",
        headers={
            "Authorization": f"Bearer {BLOB_TOKEN}",
            "Content-Type": content_type,
            "x-api-version": "7",
        },
        data=data,
        timeout=30,
    )

    if resp.status_code in (200, 201):
        return resp.json().get("url")
    return None


def delete_blob(url):
    """Delete a blob by URL."""
    if not BLOB_TOKEN or not url:
        return

    http_requests.post(
        f"{BLOB_API}/delete",
        headers={
            "Authorization": f"Bearer {BLOB_TOKEN}",
            "Content-Type": "application/json",
            "x-api-version": "7",
        },
        json={"urls": [url]},
        timeout=10,
    )
