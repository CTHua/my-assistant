import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv()

# 如果只需要讀取，使用 readonly scope
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# 認證檔案路徑
CREDENTIALS_FILE = Path(__file__).parent / "credentials.json"
TOKEN_FILE = Path(__file__).parent / "token.json"


def get_credentials() -> Credentials:
    """取得或刷新 Google OAuth credentials。"""
    creds = None

    # 嘗試載入已存在的 token
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # 如果沒有有效的 credentials，進行授權
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"找不到 {CREDENTIALS_FILE}，請從 Google Cloud Console 下載 OAuth 2.0 憑證"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # 儲存 token 供下次使用
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds


def get_today_events() -> list[dict]:
    """取得今日行程。

    Returns:
        行程列表，每個行程包含 summary, start, end
    """
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)

    # 取得今日的時間範圍
    now = datetime.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    events_result = service.events().list(
        calendarId="primary",
        timeMin=start_of_day.isoformat() + "Z",
        timeMax=end_of_day.isoformat() + "Z",
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = events_result.get("items", [])

    result = []
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        end = event["end"].get("dateTime", event["end"].get("date"))

        # 解析時間
        if "T" in start:
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            start_str = start_dt.strftime("%H:%M")
        else:
            start_str = "全天"

        result.append({
            "summary": event.get("summary", "（無標題）"),
            "start": start_str,
            "location": event.get("location", ""),
        })

    return result


def format_events_for_prompt(events: list[dict]) -> str:
    """將行程格式化為 prompt 用的字串。"""
    if not events:
        return "今日無行程"

    lines = []
    for e in events:
        line = f"- {e['start']} {e['summary']}"
        if e.get("location"):
            line += f"（{e['location']}）"
        lines.append(line)

    return "\n".join(lines)


if __name__ == "__main__":
    events = get_today_events()
    print("今日行程：")
    print(format_events_for_prompt(events))
