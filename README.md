# Facebook Video Uploader Service

This service offers a straightforward way to upload videos to your Facebook Pages, supporting both immediate publishing and scheduled posts. It also includes a handy tool for converting short-lived Facebook access tokens into long-lasting ones.

## Table of Contents

* [Features](#features)
* [Prerequisites](#prerequisites)
* [Facebook App Setup](#facebook-app-setup)
* [Installation](#installation)
* [Usage](#usage)
    * [Launching the Service](#launching-the-service)
    * [Uploading a Video](#uploading-a-video)
    * [Exchanging Access Tokens](#exchanging-access-tokens)
* [API Endpoints](#api-endpoints)
    * [`POST /upload_video`](#post-upload_video)
    * [`POST /exchange_token`](#post-exchange_token)
* [Error Handling](#error-handling)

---

## Features

* **Effortless Video Uploads:** Easily push your video content to any Facebook Page.
* **Flexible Scheduling:** Choose to publish your videos instantly or schedule them for a future date and time.
* **Token Longevity:** Convert temporary user access tokens into long-lived ones, saving you from frequent renewals.
* **FastAPI Powered:** Built on FastAPI, ensuring a swift and efficient API experience.

---

## Prerequisites

Before diving in, make sure you have **Python 3.7+** installed. This service relies on a few Python libraries, which you can install with `pip`:

```bash
pip install uvicorn fastapi requests python-multipart
```

---

## Facebook App Setup

To get started with this service, you'll need a Facebook Developer account and a Facebook App.

**Create Your Facebook App:** Head over to Facebook for Developers and create a new app, selecting the "Business" type.

**Add Necessary Products:** Be sure to add "Marketing API" and "Facebook Login" to your app's products.

**Grant Essential Permissions:** For the video upload feature to work seamlessly, your app (and the user token you'll be using) needs specific permissions. Go to your App Dashboard -> "App name X" -> "Use cases" -> "Manage everything on your Page" -> "Customize." Make sure these permissions are requested and granted:

```
pages_show_list  
pages_read_engagement  
pages_manage_posts  
pages_read_user_content  
public_profile
```

Crucially, for publishing videos to a page, `pages_manage_posts` is vital.

You'll also need a **Page Access Token**. You can obtain a short-lived user access token (with `pages_show_list` and `pages_manage_posts` permissions), exchange it for a long-lived one, and then generate page-specific tokens. Just confirm your page access token has `pages_manage_posts` permission!

---

## Installation

Simply download the provided Python code and save it. For instance, you could place it in a file named `fb_uploader.py` inside a folder called `uv_app`. Your project structure would look something like this:

```
your_project/
├── uv_app/
│   └── fb_uploader.py
└── (other files)
```

Once downloaded, you can set up the environment with uvsync:

```bash
uv sync
```

---

## Usage

### Launching the Service

Open your terminal, navigate to the directory that contains your `uv_app` folder (e.g., `your_project/`), and then fire up the Uvicorn server with this command:

```bash
uvicorn fb_uploader.upload:app --host 0.0.0.0 --port 8000 --reload
```

- `--host 0.0.0.0`: Makes your service accessible from all network interfaces. For local access only, use 127.0.0.1 or localhost.
- `--port 8000`: This is the port your service will listen on. Feel free to change it if needed.
- `--reload`: Super helpful for development! This option automatically restarts the server when it detects code changes. Remember to avoid using `--reload` in a production environment.

You'll see a message in your terminal indicating that Uvicorn is up and running, usually at http://0.0.0.0:8000.

---

### Uploading a Video

Ready to upload? Use the `/upload_video` endpoint.

**Important Notes:**

- Replace `your_video.mp4` with the actual path to your video file.
- Populate `YOUR_PAGE_ID` and `YOUR_PAGE_ACCESS_TOKEN` with your own Facebook Page ID and corresponding Page Access Token.
- For `scheduled_time`, provide a string in `YYYY-MM-DD HH:MM` format. This time must be in UTC and at least 10 minutes from the current time. If you omit or set `scheduled_time` to `None`, your video will publish immediately.

```python
import requests
import os

url = "http://localhost:8000/upload_video"

# If you need a dummy video file for testing, you can create one like this:
# with open("your_video.mp4", "wb") as f:
#    f.write(os.urandom(1024 * 1024)) # Creates a 1MB dummy file

try:
    with open("your_video.mp4", "rb") as video_file:
        response = requests.post(url, data={
            "page_id": "YOUR_PAGE_ID",  # Replace with your Facebook Page ID
            "access_token": "YOUR_PAGE_ACCESS_TOKEN",  # Replace with your Page Access Token
            "title": "My Awesome Video",
            "description": "Check out this great content!",
            "scheduled_time": "2025-06-04 16:25"  # Optional: UTC time, at least 10 mins in the future
        }, files={"video_file": video_file})

    print("Upload Response:", response.json())
except FileNotFoundError:
    print("Error: 'your_video.mp4' not found. Please ensure the video file exists at the specified path.")
except Exception as e:
    print(f"An unexpected error occurred during video upload: {e}")
```

---

### Exchanging Access Tokens

Need a long-lived token? Use the `/exchange_token` endpoint to convert your short-lived user access token.

**Important Notes:**

- Replace `YOUR_APP_ID`, `YOUR_APP_SECRET`, and `YOUR_SHORT_LIVED_USER_TOKEN` with your actual Facebook App ID, App Secret, and the short-lived token you wish to extend.
- You can grab a short-lived user access token for testing from the Facebook Graph API Explorer. Remember to select your app and grant necessary permissions (`pages_show_list`, `pages_manage_posts`) when generating the token. This endpoint is specifically for user tokens, not page tokens.

```python
import requests

url = "http://localhost:8000/exchange_token"
params = {
    "app_id": "YOUR_APP_ID",  # Replace with your Facebook App ID
    "app_secret": "YOUR_APP_SECRET",  # Replace with your Facebook App Secret
    "short_token": "YOUR_SHORT_LIVED_USER_TOKEN"  # Replace with your short-lived user token
}

try:
    response = requests.post(url, params=params)
    print("Token Exchange Response:", response.json())
except Exception as e:
    print(f"An error occurred during token exchange: {e}")
```

---

## API Endpoints

### POST /upload_video

Uploads a video to a specified Facebook Page.

**Request Body (Form Data):**

| Field          | Type       | Description                                                                 | Required |
|----------------|------------|-----------------------------------------------------------------------------|----------|
| page_id        | str        | The Facebook Page ID where your video will be posted.                       | Yes      |
| access_token   | str        | Your valid Page Access Token (must have pages_manage_posts permission).     | Yes      |
| title          | str        | The desired title for your video post.                                     | Yes      |
| description    | str        | A description for your video post.                                         | Yes      |
| scheduled_time | str        | (Optional) The scheduled publish time in `YYYY-MM-DD HH:MM` UTC format.     | No       |
| video_file     | UploadFile | The video file itself (e.g., MP4 format).                                  | Yes      |

**Response (JSON):**

- Success (200 OK):
```json
{
    "status": "success",
    "video_id": "YOUR_UPLOADED_VIDEO_ID"
}
```

- Error (500 Internal Server Error):
```json
{
    "error": "Detailed error message"
}
```

---

### POST /exchange_token

Exchanges a short-lived user access token for a long-lived one.

**Request Query Parameters:**

| Parameter    | Type | Description                                            | Required |
|-------------|------|--------------------------------------------------------|----------|
| app_id      | str  | Your Facebook App ID.                                  | Yes      |
| app_secret  | str  | Your Facebook App Secret.                              | Yes      |
| short_token | str  | The short-lived user access token to exchange.         | Yes      |

**Response (JSON):**

- Success (200 OK):
```json
{
    "status": "success",
    "long_lived_user_token": "YOUR_LONG_LIVED_USER_ACCESS_TOKEN"
}
```

- Error (400 Bad Request / 500 Internal Server Error):
```json
{
    "error": "Detailed error message"
}
```

---

## Error Handling

This service is designed with basic error handling, returning clear JSON responses that include an `"error"` key with a descriptive message if something goes wrong during video upload or token exchange. For deeper debugging, detailed traceback information will be printed to your server's console.
