import os
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
import uvicorn
import tempfile
import traceback
app = FastAPI()

def upload_facebook_video(
    page_id: str,
    access_token: str,
    video_path: str,
    title: str,
    description: str,
    scheduled_datetime: Optional[datetime] = None
) -> str:
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    file_size = os.path.getsize(video_path)

    # Validate scheduled_datetime if provided
    scheduled_timestamp = None
    if scheduled_datetime:
        if scheduled_datetime.tzinfo is None:
            raise ValueError("scheduled_datetime must be timezone-aware in UTC")
        now_utc = datetime.now(timezone.utc)
        min_schedule_time = now_utc + timedelta(minutes=10)
        if scheduled_datetime < min_schedule_time:
            raise ValueError("Scheduled publish time must be at least 10 minutes in the future")
        scheduled_timestamp = int(scheduled_datetime.timestamp())

    # Start upload session
    start_response = requests.post(
        f"https://graph-video.facebook.com/v19.0/{page_id}/videos",
        data={
            "upload_phase": "start",
            "file_size": file_size,
            "access_token": access_token
        }
    )
    start_data = start_response.json()

    if "error" in start_data:
        raise RuntimeError(f"Failed to start upload session: {start_data['error']}")

    upload_session_id = start_data.get("upload_session_id")
    video_id = start_data.get("video_id")
    start_offset = int(start_data.get("start_offset", 0))
    end_offset = int(start_data.get("end_offset", 0))

    with open(video_path, "rb") as f:
        while start_offset < file_size:
            f.seek(start_offset)
            chunk_size = end_offset - start_offset
            chunk = f.read(chunk_size)
            if not chunk:
                break

            transfer_response = requests.post(
                f"https://graph-video.facebook.com/v19.0/{page_id}/videos",
                data={
                    "upload_phase": "transfer",
                    "upload_session_id": upload_session_id,
                    "start_offset": start_offset,
                    "access_token": access_token
                },
                files={"video_file_chunk": chunk}
            )
            transfer_data = transfer_response.json()

            if "error" in transfer_data:
                import json
                print("Transfer phase error response:", json.dumps(transfer_data, indent=2))
                raise RuntimeError(f"Transfer upload failed: {transfer_data['error']['message']}")

            start_offset = int(transfer_data.get("start_offset", start_offset))
            end_offset = int(transfer_data.get("end_offset", end_offset))

            progress_percent = (start_offset / file_size) * 100
            print(f"Upload progress: {progress_percent:.2f}%")

    # Finish upload
    finish_data = {
        "upload_phase": "finish",
        "upload_session_id": upload_session_id,
        "access_token": access_token,
        "title": title,
        "description": description,
    }
    if scheduled_timestamp:
        finish_data["published"] = "false"
        finish_data["scheduled_publish_time"] = scheduled_timestamp

    finish_response = requests.post(
        f"https://graph-video.facebook.com/v19.0/{page_id}/videos",
        data=finish_data
    )
    result = finish_response.json()

    if "error" in result:
        raise RuntimeError(f"Finish upload failed: {result['error']}")

    print("Upload complete!")
    return video_id

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Service is running"}


@app.post("/upload_video")
async def upload_video(
    page_id: str = Form(...),
    access_token: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    scheduled_time: Optional[str] = Form(None),  # Format: "YYYY-MM-DD HH:MM"
    video_file: UploadFile = Form(...)
):
    local_video_path = None
    try:
        content = await video_file.read()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            local_video_path = tmp.name
            tmp.write(content)

        scheduled_datetime = None
        if scheduled_time:
            scheduled_datetime = datetime.strptime(scheduled_time, "%Y-%m-%d %H:%M")
            scheduled_datetime = scheduled_datetime.replace(tzinfo=timezone.utc)

        video_id = upload_facebook_video(
            page_id=page_id,
            access_token=access_token,
            video_path=local_video_path,
            title=title,
            description=description,
            scheduled_datetime=scheduled_datetime
        )

        return JSONResponse(content={"status": "success", "video_id": video_id})

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

    finally:
        if local_video_path and os.path.exists(local_video_path):
            try:
                os.remove(local_video_path)
            except Exception as cleanup_error:
                print(f"Failed to delete temporary file: {cleanup_error}")

from fastapi import Query


@app.post("/exchange_token")
def exchange_token(
    app_id: str = Query(...),
    app_secret: str = Query(...),
    short_token: str = Query(...)
):
    try:
        url = "https://graph.facebook.com/v19.0/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": short_token
        }

        response = requests.get(url, params=params)
        data = response.json()

        if "access_token" in data:
            return JSONResponse(content={
                "status": "success",
                "long_lived_user_token": data["access_token"]
            })

        return JSONResponse(status_code=400, content={"error": data.get("error", "Unknown error")})

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    uvicorn.run("fb_uploader.upload:app", host="0.0.0.0", port=8000, reload=False)