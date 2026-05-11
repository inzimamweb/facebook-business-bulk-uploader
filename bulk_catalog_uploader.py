"""
========================================================
  Facebook Business Suite — Bulk Catalog/Services Uploader
  Uses: Facebook Catalog Batch API (Graph API v19.0)
  Author: Manus AI Toolkit
========================================================

PREREQUISITES:
  1. A Facebook Business Manager account
  2. A Product Catalog created in Commerce Manager
     (https://business.facebook.com/commerce)
  3. A System User Access Token OR User Access Token with:
       - catalog_management permission
       - business_management permission
  4. Your Catalog ID (found in Commerce Manager > Catalog Settings)

USAGE:
  1. Fill in your credentials in the CONFIG section below.
  2. Edit services_catalog.csv with your products/services.
  3. Run:  python3 bulk_catalog_uploader.py

SUPPORTED METHODS:
  - CREATE : Add new items to the catalog
  - UPDATE : Update existing items (matched by 'id')
  - DELETE : Remove items from the catalog

CSV REQUIRED COLUMNS:
  id, title, description, availability, condition, price,
  link, image_link, brand, category

CSV OPTIONAL COLUMNS:
  sale_price, inventory, item_group_id, gender, size, color, material
"""

import csv
import json
import os
import sys
import time
import requests
from datetime import datetime

# ─────────────────────────────────────────────
#  CONFIG — Fill in your credentials here
# ─────────────────────────────────────────────
CATALOG_ID    = "YOUR_CATALOG_ID"           # e.g., "123456789012345"
ACCESS_TOKEN  = "YOUR_ACCESS_TOKEN"         # System User or User Access Token
GRAPH_API_VERSION = "v19.0"
CSV_FILE      = "services_catalog.csv"      # Path to your CSV file
BATCH_SIZE    = 50                          # Max items per API batch call (Facebook limit: 1000, but 50 is safer)
METHOD        = "CREATE"                    # "CREATE", "UPDATE", or "DELETE"
# ─────────────────────────────────────────────


BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

# Required fields for catalog items
REQUIRED_FIELDS = ["id", "title", "description", "availability", "condition", "price", "link", "image_link"]

# Optional fields to include if present in CSV
OPTIONAL_FIELDS = [
    "brand", "category", "sale_price", "inventory", "item_group_id",
    "gender", "size", "color", "material", "additional_image_link",
    "age_group", "shipping", "custom_label_0", "custom_label_1"
]


def validate_config():
    """Ensure credentials are set before running."""
    if CATALOG_ID == "YOUR_CATALOG_ID" or ACCESS_TOKEN == "YOUR_ACCESS_TOKEN":
        print("\n[ERROR] Please update CATALOG_ID and ACCESS_TOKEN in the CONFIG section.\n")
        sys.exit(1)
    if METHOD not in ("CREATE", "UPDATE", "DELETE"):
        print(f"\n[ERROR] Invalid METHOD '{METHOD}'. Must be CREATE, UPDATE, or DELETE.\n")
        sys.exit(1)


def validate_row(row: dict, row_num: int) -> tuple:
    """
    Validate a CSV row for required fields.

    Returns:
        (is_valid: bool, missing_fields: list)
    """
    missing = [f for f in REQUIRED_FIELDS if not row.get(f, "").strip()]
    return (len(missing) == 0, missing)


def build_item_payload(row: dict) -> dict:
    """
    Build a single catalog item payload from a CSV row.

    Args:
        row: A dictionary representing one CSV row.

    Returns:
        dict: Formatted item payload for the Batch API.
    """
    item = {}

    # Add all required fields
    for field in REQUIRED_FIELDS:
        value = row.get(field, "").strip()
        if value:
            item[field] = value

    # Add optional fields if present and non-empty
    for field in OPTIONAL_FIELDS:
        value = row.get(field, "").strip()
        if value:
            item[field] = value

    return item


def upload_batch(items: list, method: str = "CREATE") -> dict:
    """
    Upload a batch of catalog items using the Facebook Catalog Batch API.

    Args:
        items  : List of item payload dicts (max 1000 per call).
        method : "CREATE", "UPDATE", or "DELETE".

    Returns:
        dict: API response.
    """
    endpoint = f"{BASE_URL}/{CATALOG_ID}/items_batch"

    # Build the requests array
    requests_payload = []
    for item in items:
        requests_payload.append({
            "method": method,
            "data": item
        })

    payload = {
        "access_token": ACCESS_TOKEN,
        "requests": json.dumps(requests_payload),
        "item_type": "PRODUCT_ITEM"
    }

    response = requests.post(endpoint, data=payload, timeout=60)
    return response.json()


def check_batch_status(handles: list) -> dict:
    """
    Check the processing status of a batch upload using its handles.

    Args:
        handles: List of batch handle strings returned by upload_batch.

    Returns:
        dict: Status response.
    """
    endpoint = f"{BASE_URL}/{CATALOG_ID}/check_batch_request_status"
    payload = {
        "access_token": ACCESS_TOKEN,
        "handle": json.dumps(handles)
    }
    response = requests.get(endpoint, params=payload, timeout=30)
    return response.json()


def bulk_upload_from_csv(csv_path: str):
    """
    Read a CSV file and bulk upload products/services to the Facebook Catalog.

    Args:
        csv_path: Path to the CSV file.
    """
    if not os.path.isfile(csv_path):
        print(f"[ERROR] CSV file not found: {csv_path}")
        sys.exit(1)

    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    total = len(rows)
    print(f"\n{'='*55}")
    print(f"  Facebook Bulk Catalog Uploader")
    print(f"  Method : {METHOD}")
    print(f"  Total items in CSV: {total}")
    print(f"{'='*55}\n")

    valid_items   = []
    skipped_rows  = []

    # Validate and build item payloads
    for idx, row in enumerate(rows):
        row_num = idx + 2  # +2 for header row and 1-based index
        is_valid, missing = validate_row(row, row_num)

        if not is_valid:
            print(f"  [ROW {row_num}] SKIPPED — Missing required fields: {', '.join(missing)}")
            skipped_rows.append({"row": row_num, "reason": f"Missing: {', '.join(missing)}"})
            continue

        item = build_item_payload(row)
        valid_items.append({"row": row_num, "item": item})

    print(f"\n  Valid items  : {len(valid_items)}")
    print(f"  Skipped rows : {len(skipped_rows)}")

    if not valid_items:
        print("\n[WARNING] No valid items to upload. Please check your CSV file.\n")
        return

    # Split into batches and upload
    batches = [valid_items[i:i+BATCH_SIZE] for i in range(0, len(valid_items), BATCH_SIZE)]
    total_batches = len(batches)
    all_handles   = []
    batch_results = []

    print(f"\n  Uploading in {total_batches} batch(es) of up to {BATCH_SIZE} items each...\n")

    for batch_idx, batch in enumerate(batches):
        items_payload = [entry["item"] for entry in batch]
        print(f"  [Batch {batch_idx+1}/{total_batches}] Uploading {len(items_payload)} items...")

        result = upload_batch(items_payload, method=METHOD)

        if "handles" in result:
            handles = result["handles"]
            all_handles.extend(handles)
            print(f"    ✓ Accepted — Handles: {handles}")
            batch_results.append({"batch": batch_idx+1, "status": "accepted", "handles": handles})
        elif "error" in result:
            error_msg = result["error"].get("message", str(result))
            print(f"    ✗ FAILED   — {error_msg}")
            batch_results.append({"batch": batch_idx+1, "status": "failed", "error": error_msg})
        else:
            print(f"    ? UNKNOWN  — Response: {result}")
            batch_results.append({"batch": batch_idx+1, "status": "unknown", "response": str(result)})

        if batch_idx < total_batches - 1:
            print(f"    Waiting 3s before next batch...")
            time.sleep(3)

    # ── Check batch status if handles were returned ───────
    if all_handles:
        print(f"\n  Checking batch processing status...")
        time.sleep(5)  # Give Facebook time to process
        status = check_batch_status(all_handles)
        print(f"  Status response: {json.dumps(status, indent=2)}")

    # ── Summary ──────────────────────────────────────────
    accepted = sum(1 for r in batch_results if r["status"] == "accepted")
    failed   = sum(1 for r in batch_results if r["status"] == "failed")

    print(f"\n{'='*55}")
    print(f"  UPLOAD COMPLETE")
    print(f"  Batches accepted : {accepted} / {total_batches}")
    print(f"  Batches failed   : {failed} / {total_batches}")
    print(f"  Items skipped    : {len(skipped_rows)}")
    print(f"{'='*55}")

    # Save results log
    log_path = "catalog_upload_results.log"
    with open(log_path, "w", encoding="utf-8") as log:
        log.write(f"Catalog Upload run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write(f"Method: {METHOD} | Total: {total} | Valid: {len(valid_items)} | Skipped: {len(skipped_rows)}\n\n")
        log.write("BATCH RESULTS:\n")
        for r in batch_results:
            log.write(f"  Batch {r['batch']}: {r['status'].upper()}")
            if "handles" in r:
                log.write(f" | Handles: {r['handles']}")
            if "error" in r:
                log.write(f" | Error: {r['error']}")
            log.write("\n")
        log.write("\nSKIPPED ROWS:\n")
        for s in skipped_rows:
            log.write(f"  Row {s['row']}: {s['reason']}\n")
        if all_handles:
            log.write(f"\nALL HANDLES: {all_handles}\n")

    print(f"\n  Results saved to: {log_path}\n")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    validate_config()
    bulk_upload_from_csv(CSV_FILE)
