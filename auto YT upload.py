import os
import time
import shutil
import random
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# === CONFIGURATION ===
UPLOAD_FOLDER = "upload"
UPLOADED_FOLDER = "uploaded"
CLIENT_SECRETS_FILE = "client_secrets.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
LOG_FILE = "upload_log.txt"

def authenticate_youtube():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    youtube = build("youtube", "v3", credentials=creds)
    return youtube

def log_upload(video_name, video_id):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{now}] Uploaded: {video_name} → Video ID: {video_id}\n")

def upload_video(youtube, file_path):
    title = os.path.splitext(os.path.basename(file_path))[0]
    request_body = {
        "snippet": {
            "title": title,
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public",
            "madeForKids": False,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

    print(f"\nUploading: {title}")
    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploading... {int(status.progress() * 100)}%")

    print(f"✅ Upload complete: {response['id']}")
    log_upload(title, response["id"])
    return response["id"]

def main():
    youtube = authenticate_youtube()

    while True:
        videos = [f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith((".mp4", ".mov", ".avi", ".webm"))]

        if not videos:
            print("✅ No videos left to upload.")
            break

        video_file = videos[0]
        video_path = os.path.join(UPLOAD_FOLDER, video_file)

        try:
            upload_video(youtube, video_path)
            shutil.move(video_path, os.path.join(UPLOADED_FOLDER, video_file))
            print(f"📦 Moved {video_file} to '{UPLOADED_FOLDER}'")
        except Exception as e:
            print(f"❌ Error uploading {video_file}: {e}")

        wait_minutes = random.randint(30, 40)
        print(f"⏳ Waiting {wait_minutes} minutes until next upload...")
        time.sleep(wait_minutes * 60)

if __name__ == "__main__":
    main()
