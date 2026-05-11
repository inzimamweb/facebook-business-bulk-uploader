"""
========================================================
  Facebook Access Token Helper
  Helps you generate and verify Page Access Tokens
  Uses: Facebook Graph API v19.0
  Author: Manus AI Toolkit
========================================================

USAGE:
  python3 get_access_token.py

STEPS THIS SCRIPT HELPS WITH:
  1. Exchange a short-lived user token for a long-lived user token (60 days)
  2. List all pages you manage and their access tokens
  3. Verify a token is valid and check its permissions

HOW TO GET YOUR INITIAL SHORT-LIVED TOKEN:
  1. Go to: https://developers.facebook.com/tools/explorer/
  2. Select your App from the dropdown
  3. Click "Generate Access Token"
  4. Grant permissions: pages_manage_posts, pages_read_engagement,
     pages_show_list, catalog_management
  5. Copy the token and paste it below when prompted
"""

import requests
import json

GRAPH_API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def exchange_for_long_lived_token(app_id: str, app_secret: str, short_lived_token: str) -> dict:
    """
    Exchange a short-lived user access token (1-2 hours) for a long-lived one (60 days).

    Args:
        app_id           : Your Facebook App ID
        app_secret       : Your Facebook App Secret
        short_lived_token: The short-lived user access token

    Returns:
        dict: Contains 'access_token' and 'expires_in' on success
    """
    url = f"{BASE_URL}/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_lived_token
    }
    response = requests.get(url, params=params, timeout=15)
    return response.json()


def get_page_access_tokens(long_lived_user_token: str) -> list:
    """
    Retrieve all Facebook Pages you manage and their Page Access Tokens.

    Args:
        long_lived_user_token: Your long-lived user access token

    Returns:
        list: Each item contains page 'id', 'name', and 'access_token'
    """
    url = f"{BASE_URL}/me/accounts"
    params = {
        "access_token": long_lived_user_token,
        "fields": "id,name,access_token,category,fan_count"
    }
    response = requests.get(url, params=params, timeout=15)
    data = response.json()

    if "data" in data:
        return data["data"]
    return []


def inspect_token(token_to_inspect: str, app_id: str, app_secret: str) -> dict:
    """
    Inspect a token to check its validity, expiry, and permissions.

    Args:
        token_to_inspect : The token you want to inspect
        app_id           : Your Facebook App ID
        app_secret       : Your Facebook App Secret

    Returns:
        dict: Token debug information
    """
    app_token = f"{app_id}|{app_secret}"
    url = f"{BASE_URL}/debug_token"
    params = {
        "input_token": token_to_inspect,
        "access_token": app_token
    }
    response = requests.get(url, params=params, timeout=15)
    return response.json()


def main():
    print("\n" + "="*55)
    print("  Facebook Access Token Helper")
    print("="*55)
    print("""
Options:
  1. Exchange short-lived token → long-lived token (60 days)
  2. Get Page Access Tokens for all your pages
  3. Inspect / verify a token
  4. Exit
""")

    choice = input("Select an option (1-4): ").strip()

    if choice == "1":
        print("\n[Step 1] Exchange Short-Lived Token for Long-Lived Token")
        app_id     = input("  Enter your App ID     : ").strip()
        app_secret = input("  Enter your App Secret : ").strip()
        token      = input("  Enter short-lived token: ").strip()

        result = exchange_for_long_lived_token(app_id, app_secret, token)
        if "access_token" in result:
            print(f"\n  ✓ Long-lived token obtained!")
            print(f"  Token     : {result['access_token']}")
            print(f"  Expires in: {result.get('expires_in', 'N/A')} seconds (~60 days)")
        else:
            print(f"\n  ✗ Error: {result}")

    elif choice == "2":
        print("\n[Step 2] Get Page Access Tokens")
        user_token = input("  Enter your long-lived user access token: ").strip()

        pages = get_page_access_tokens(user_token)
        if pages:
            print(f"\n  Found {len(pages)} page(s):\n")
            for page in pages:
                print(f"  Page Name    : {page.get('name', 'N/A')}")
                print(f"  Page ID      : {page.get('id', 'N/A')}")
                print(f"  Category     : {page.get('category', 'N/A')}")
                print(f"  Fans/Likes   : {page.get('fan_count', 'N/A')}")
                print(f"  Access Token : {page.get('access_token', 'N/A')}")
                print("  " + "-"*50)
        else:
            print("  No pages found or error occurred.")

    elif choice == "3":
        print("\n[Step 3] Inspect / Verify a Token")
        app_id     = input("  Enter your App ID     : ").strip()
        app_secret = input("  Enter your App Secret : ").strip()
        token      = input("  Enter the token to inspect: ").strip()

        result = inspect_token(token, app_id, app_secret)
        data   = result.get("data", {})

        if data:
            print(f"\n  Token Info:")
            print(f"  Valid       : {data.get('is_valid', False)}")
            print(f"  App ID      : {data.get('app_id', 'N/A')}")
            print(f"  User ID     : {data.get('user_id', 'N/A')}")
            print(f"  Type        : {data.get('type', 'N/A')}")
            expires = data.get("expires_at", 0)
            if expires:
                from datetime import datetime
                exp_dt = datetime.fromtimestamp(expires)
                print(f"  Expires at  : {exp_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"  Expires at  : Never (permanent token)")
            scopes = data.get("scopes", [])
            print(f"  Permissions : {', '.join(scopes) if scopes else 'None listed'}")
        else:
            print(f"  ✗ Error: {result}")

    elif choice == "4":
        print("\n  Goodbye!\n")
    else:
        print("\n  Invalid option. Please run the script again.\n")


if __name__ == "__main__":
    main()
