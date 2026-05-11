"""
========================================================
  Facebook Business Suite — Bulk Photo Uploader
  Uses: Facebook Graph API v19.0
  Author: Manus AI Toolkit
========================================================

PREREQUISITES:
  1. A Facebook Developer account at https://developers.facebook.com
  2. A Facebook App with the following permissions granted:
       - pages_manage_posts
       - pages_read_engagement
       - pages_show_list
       - publish_to_groups (if posting to groups)
  3. A long-lived Page Access Token (see guide for how to generate one)
  4. Your Facebook Page ID

USAGE:
  1. Fill in your credentials in the CONFIG section below.
  2. Edit photos_upload.csv with your photo URLs and captions.
  3. Run:  python3 bulk_photo_uploader.py

NOTES:
  - Photos must be publicly accessible URLs (hosted online).
  - To upload local files, use the --local flag (see LOCAL UPLOAD section).
  - Rate limit: Facebook allows ~200 calls per hour per token.
"""

import csv
import time
import os
import sys
import requests
from datetime import datetime

# ─────────────────────────────────────────────
#  CONFIG — Fill in your credentials here
# ─────────────────────────────────────────────
PAGE_ID          = "YOUR_PAGE_ID"           # e.g., "123456789012345"
PAGE_ACCESS_TOKEN = "YOUR_PAGE_ACCESS_TOKEN" # Long-lived Page Access Token
GRAPH_API_VERSION = "v19.0"
CSV_FILE          = "photos_upload.csv"      # Path to your CSV file
DELAY_BETWEEN_POSTS = 5                      # Seconds to wait between each upload (avoid rate limits)
# ─────────────────────────────────────────────


BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def validate_config():
    """Ensure credentials are set before running."""
    if PAGE_ID == "YOUR_PAGE_ID" or PAGE_ACCESS_TOKEN == "YOUR_PAGE_ACCESS_TOKEN":
        print("\n[ERROR] Please update PAGE_ID and PAGE_ACCESS_TOKEN in the CONFIG section.\n")
        sys.exit(1)


def upload_single_photo_url(photo_url: str, caption: str = "", published: bool = True) -> dict:
    """
    Upload a single photo to the Facebook Page using a public URL.

    Args:
        photo_url  : Publicly accessible URL of the image.
        caption    : Text caption/message for the post.
        published  : If True, publishes immediately. If False, saves as unpublished.

    Returns:
        dict: API response containing 'id' on success, or error details.
    """
    endpoint = f"{BASE_URL}/{PAGE_ID}/photos"
    payload = {
        "url": photo_url,
        "caption": caption,
        "published": str(published).lower(),
        "access_token": PAGE_ACCESS_TOKEN,
    }

    response = requests.post(endpoint, data=payload, timeout=30)
    return response.json()


def upload_single_photo_local(file_path: str, caption: str = "", published: bool = True) -> dict:
    """
    Upload a single photo from a local file path to the Facebook Page.

    Args:
        file_path  : Absolute or relative path to the local image file.
        caption    : Text caption/message for the post.
        published  : If True, publishes immediately.

    Returns:
        dict: API response containing 'id' on success, or error details.
    """
    if not os.path.isfile(file_path):
        return {"error": f"File not found: {file_path}"}

    endpoint = f"{BASE_URL}/{PAGE_ID}/photos"
    payload = {
        "caption": caption,
        "published": str(published).lower(),
        "access_token": PAGE_ACCESS_TOKEN,
    }

    with open(file_path, "rb") as img_file:
        files = {"source": img_file}
        response = requests.post(endpoint, data=payload, files=files, timeout=60)

    return response.json()


def upload_multi_photo_post(photo_urls: list, message: str = "") -> dict:
    """
    Create a single post containing multiple photos (carousel-style).

    Steps:
      1. Upload each photo as unpublished to get their IDs.
      2. Create a feed post attaching all photo IDs.

    Args:
        photo_urls : List of publicly accessible image URLs.
        message    : Text message for the post.

    Returns:
        dict: API response for the final feed post.
    """
    print(f"  Uploading {len(photo_urls)} photos as unpublished...")
    photo_ids = []

    for idx, url in enumerate(photo_urls):
        result = upload_single_photo_url(url, caption="", published=False)
        if "id" in result:
            photo_ids.append(result["id"])
            print(f"    [{idx+1}/{len(photo_urls)}] Uploaded → ID: {result['id']}")
        else:
            print(f"    [{idx+1}/{len(photo_urls)}] FAILED: {result}")
        time.sleep(1)  # Small delay between individual uploads

    if not photo_ids:
        return {"error": "No photos were successfully uploaded."}

    # Build the feed post with all photo IDs attached
    feed_endpoint = f"{BASE_URL}/{PAGE_ID}/feed"
    payload = {
        "message": message,
        "access_token": PAGE_ACCESS_TOKEN,
    }
    for i, pid in enumerate(photo_ids):
        payload[f"attached_media[{i}]"] = f'{{"media_fbid":"{pid}"}}'

    response = requests.post(feed_endpoint, data=payload, timeout=30)
    return response.json()


def bulk_upload_from_csv(csv_path: str):
    """
    Read a CSV file and upload photos in bulk to the Facebook Page.

    CSV columns:
      - photo_url     : Public URL of the image (required)
      - caption       : Post caption/message (optional)
      - scheduled_time: Future datetime string 'YYYY-MM-DD HH:MM:SS' (optional, not yet used)
      - published     : 'true' or 'false' (optional, default: true)

    Args:
        csv_path: Path to the CSV file.
    """
    if not os.path.isfile(csv_path):
        print(f"[ERROR] CSV file not found: {csv_path}")
        sys.exit(1)

    results = {"success": [], "failed": []}

    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    total = len(rows)
    print(f"\n{'='*55}")
    print(f"  Facebook Bulk Photo Uploader")
    print(f"  Total photos to upload: {total}")
    print(f"{'='*55}\n")

    for idx, row in enumerate(rows):
        photo_url  = row.get("photo_url", "").strip()
        caption    = row.get("caption", "").strip()
        published  = row.get("published", "true").strip().lower() == "true"

        if not photo_url:
            print(f"[{idx+1}/{total}] SKIPPED — No photo URL provided in row {idx+2}.")
            results["failed"].append({"row": idx+2, "reason": "Missing photo_url"})
            continue

        print(f"[{idx+1}/{total}] Uploading: {photo_url[:60]}...")
        result = upload_single_photo_url(photo_url, caption=caption, published=published)

        if "id" in result:
            post_id = result["id"]
            print(f"  ✓ SUCCESS — Post ID: {post_id}")
            results["success"].append({"row": idx+2, "url": photo_url, "post_id": post_id})
        else:
            error_msg = result.get("error", {}).get("message", str(result))
            print(f"  ✗ FAILED  — {error_msg}")
            results["failed"].append({"row": idx+2, "url": photo_url, "reason": error_msg})

        if idx < total - 1:
            print(f"  Waiting {DELAY_BETWEEN_POSTS}s before next upload...")
            time.sleep(DELAY_BETWEEN_POSTS)

    # ── Summary ──────────────────────────────────────────
    print(f"\n{'='*55}")
    print(f"  UPLOAD COMPLETE")
    print(f"  Successful: {len(results['success'])} / {total}")
    print(f"  Failed    : {len(results['failed'])} / {total}")
    print(f"{'='*55}")

    if results["failed"]:
        print("\n  Failed rows:")
        for f in results["failed"]:
            print(f"    Row {f['row']}: {f.get('reason', 'Unknown error')}")

    # Save results log
    log_path = "upload_results.log"
    with open(log_path, "w", encoding="utf-8") as log:
        log.write(f"Upload run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write(f"Total: {total} | Success: {len(results['success'])} | Failed: {len(results['failed'])}\n\n")
        log.write("SUCCESSFUL UPLOADS:\n")
        for s in results["success"]:
            log.write(f"  Row {s['row']} | Post ID: {s['post_id']} | URL: {s['url']}\n")
        log.write("\nFAILED UPLOADS:\n")
        for f in results["failed"]:
            log.write(f"  Row {f['row']} | Reason: {f.get('reason')} | URL: {f.get('url','N/A')}\n")

    print(f"\n  Results saved to: {log_path}\n")
    return results


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    validate_config()

    # Check for optional --multi flag for multi-photo posts
    if "--multi" in sys.argv:
        # Example: post all photos in CSV as a single multi-photo post
        print("\n[MODE] Multi-photo post mode selected.")
        urls = []
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("photo_url", "").strip():
                    urls.append(row["photo_url"].strip())
        message = input("Enter the post message for the multi-photo post: ").strip()
        result = upload_multi_photo_post(urls, message=message)
        if "id" in result:
            print(f"\n✓ Multi-photo post created! Post ID: {result['id']}")
        else:
            print(f"\n✗ Failed to create multi-photo post: {result}")
    else:
        # Default: bulk upload each row as an individual post
        bulk_upload_from_csv(CSV_FILE)
