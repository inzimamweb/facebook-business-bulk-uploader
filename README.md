# facebook-business-bulk-uploader
Welcome to the Facebook Business Suite Bulk Uploader Toolkit. This guide will walk you through the process of automating bulk uploads of photos to your Facebook Page and products/services to your Facebook Catalog using Python and the Facebook Graph API.

Overview of the Toolkit

This toolkit contains three main Python scripts and two CSV templates:

1.
bulk_photo_uploader.py: Automates uploading multiple photos with captions to your Facebook Page.

2.
bulk_catalog_uploader.py: Automates adding, updating, or deleting products and services in your Facebook Catalog using the Batch API.

3.
get_access_token.py: A helper script to generate long-lived access tokens and verify permissions.

4.
photos_upload.csv: Template for bulk photo uploads.

5.
services_catalog.csv: Template for bulk catalog/service uploads.




Step 1: Set Up Your Facebook Developer Account

Before running any scripts, you need to set up a Facebook App to interact with the Graph API.

1.
Go to the Meta for Developers portal and log in.

2.
Click on My Apps in the top right corner, then click Create App.

3.
Select Other for the app type, then select Business.

4.
Give your app a name (e.g., "My Bulk Uploader") and click Create App.

5.
Once your app is created, navigate to App Settings > Basic to find your App ID and App Secret. You will need these later.




Step 2: Generate Access Tokens

To post on behalf of your Page or manage your Catalog, you need a Page Access Token or a System User Access Token.

Getting a Short-Lived Token

1.
Go to the Graph API Explorer.

2.
In the right sidebar, select your newly created App from the Meta App dropdown.

3.
Under User or Page, select Get User Access Token.

4.
Add the following permissions:

•
pages_manage_posts

•
pages_read_engagement

•
pages_show_list

•
catalog_management (for services/products)



5.
Click Generate Access Token and follow the prompts to link your Facebook account and select the Pages you want to manage.

6.
Copy the generated short-lived token.

Converting to a Long-Lived Token

Short-lived tokens expire in 1-2 hours. Use the included helper script to get a 60-day token.

1.
Open your terminal and navigate to the toolkit directory.

2.
Run the helper script:

Bash


python3 get_access_token.py





3.
Select Option 1 and enter your App ID, App Secret, and the short-lived token.

4.
The script will output a Long-Lived User Token. Copy this token.

5.
Run the script again, select Option 2, and paste your Long-Lived User Token.

6.
The script will list all your Pages and their corresponding Page Access Tokens. Copy the Page Access Token for the specific Page you want to automate. This token will not expire as long as the user token is valid.




Step 3: Bulk Uploading Photos to Your Page

The bulk_photo_uploader.py script reads a CSV file and uploads each photo as a separate post on your Facebook Page.

1. Prepare Your Data

Open photos_upload.csv and fill it with your data. The required columns are:

•
photo_url: The publicly accessible URL of the image (e.g., hosted on your website, AWS S3, or Imgur).

•
caption: The text you want to appear in the post.

•
published: Set to true to publish immediately, or false to save as a draft/unpublished post.

2. Configure the Script

Open bulk_photo_uploader.py in a text editor and update the CONFIG section:

Python


PAGE_ID          = "YOUR_PAGE_ID"           # Your Facebook Page ID
PAGE_ACCESS_TOKEN = "YOUR_PAGE_ACCESS_TOKEN" # The Page Access Token from Step 2



3. Run the Uploader

Execute the script in your terminal:

Bash


python3 bulk_photo_uploader.py



The script will process each row, upload the photo, and print the resulting Post ID. A log file (upload_results.log) will be generated with the summary.

(Optional): To upload all photos in the CSV as a single multi-photo (carousel) post, run:

Bash


python3 bulk_photo_uploader.py --multi






Step 4: Bulk Uploading Services/Products to Your Catalog

The bulk_catalog_uploader.py script uses the Facebook Catalog Batch API to efficiently upload up to 50 items per request.

1. Find Your Catalog ID

1.
Go to Commerce Manager.

2.
Select your Catalog.

3.
Go to Settings > Catalog.

4.
Copy the Catalog ID.

2. Prepare Your Data

Open services_catalog.csv and fill it with your services or products. The required columns are:

•
id: A unique identifier for the item (e.g., SVC-001).

•
title: The name of the service/product.

•
description: A detailed description.

•
availability: Usually in stock.

•
condition: Usually new.

•
price: The price with currency (e.g., 49.99 USD).

•
link: The URL where customers can buy or view the item.

•
image_link: A publicly accessible URL of the item's image.

3. Configure the Script

Open bulk_catalog_uploader.py in a text editor and update the CONFIG section:

Python


CATALOG_ID    = "YOUR_CATALOG_ID"           # Your Catalog ID
ACCESS_TOKEN  = "YOUR_ACCESS_TOKEN"         # Your User Token or System User Token
METHOD        = "CREATE"                    # Use "CREATE", "UPDATE", or "DELETE"



4. Run the Uploader

Execute the script in your terminal:

Bash


python3 bulk_catalog_uploader.py



The script will validate your CSV, split the items into batches, and send them to Facebook. A log file (catalog_upload_results.log) will be generated with the batch handles and status.




Troubleshooting & Best Practices

•
Rate Limits: Facebook enforces rate limits on API calls. The photo uploader includes a built-in delay (DELAY_BETWEEN_POSTS = 5) to prevent hitting these limits. Do not upload more than ~200 photos per hour.

•
Image Hosting: The Graph API requires images to be hosted on publicly accessible URLs. If your images are stored locally, you must upload them to a server or cloud storage (like AWS S3) first, or modify the script to use the multipart/form-data local upload method provided in the code.

•
Token Expiration: If you receive an OAuth exception regarding an invalid or expired token, you will need to generate a new short-lived token and exchange it for a new long-lived token using get_access_token.py.

References

[1] Meta for Developers. "Batch Requests - Graph API."
[2] Meta for Developers. "Catalog Overview."
[3] Meta for Developers. "Graph API Reference v19.0: Page Photos."
