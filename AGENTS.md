# Personal AI Assistant

> Claude Code 專案指引文件

## 專案概述

私人 AI 助理系統，整合行事曆、待辦事項、健康數據，協助使用者追蹤個人發展目標。

**核心原則**：
- 完全私有，不上公網
- 透過 ZeroTier 內網存取
- 靜音運作（同居伴侶）

---

## 使用者背景

### 個人發展狀態（Human 3.0 計畫）

```yaml
職業:
  身份: 全端工程師
  現況: 6-7 條收入線，沒有主軸
  目標: 簡化到 3 條以內
  問題: 會議常開到 23:00 後，工作殖民整個生活

身體:
  作息: 嚴重倒置，常凌晨 4 點後才睡
  目標: 02:00 前就寢，睡滿 7 小時
  運動: 有健身房會員但三個月沒去
  體型: 179cm / 65kg，偏瘦，體力差

學業:
  狀態: 碩士論文進行中
  死線: 6 月畢業（研發替代役需要）
  方向: 資安相關，教授專長 fuzzing / symbolic execution

關係:
  伴侶: 有同居伴侶
  問題: 主要是日常運作，深度對話少
  限制: 系統必須靜音，不能吵到她

心理:
  模式: 焦慮觸發才反思，平常在執行模式
  逃避方式: 刷短影音
```

### AI 助理的角色定位

```
✓ 直接、不囉唆
✓ 有問題就講，不委婉
✓ 追蹤使用者承諾的事
✓ 指出重複出現的模式
✓ 繁體中文、台灣用語

✗ 過度正向或打氣
✗ 長篇大論
✗ 問太多問題
```

---

## 系統架構

```
┌─────────────────────────────────────────────────────┐
│  Server（使用者家中電腦）                            │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │           FastAPI Backend (:8000)            │   │
│  │                                              │   │
│  │  /morning  ─── 早安流程                      │   │
│  │  /health   ─── 健康檢查                      │   │
│  └──────────────────┬───────────────────────────┘   │
│                     │                               │
│         ┌───────────┼───────────┐                   │
│         ▼           ▼           ▼                   │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│   │ Gemini   │ │ Todoist  │ │ Google   │           │
│   │ API      │ │ API      │ │ Calendar │           │
│   └──────────┘ └──────────┘ └──────────┘           │
│                                                     │
│   ┌──────────────────────────────────────────┐     │
│   │ SQLite (data/assistant.db)               │     │
│   │ • 睡眠紀錄                                │     │
│   │ • 起床時間                                │     │
│   │ • 每週統計                                │     │
│   └──────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
                        │
                        │ ZeroTier (10.x.x.x)
                        ▼
┌─────────────────────────────────────────────────────┐
│  iPhone + Apple Watch                               │
│                                                     │
│  起床流程：                                          │
│  ┌─────────────────────────────────────────────┐   │
│  │ 1. Apple Watch 震動（無聲鬧鐘）              │   │
│  │ 2. 使用者醒來，解鎖 iPhone                   │   │
│  │ 3. iOS 捷徑自動觸發（或定時 09:00）          │   │
│  │ 4. 捷徑讀取 HealthKit 睡眠數據               │   │
│  │ 5. POST 到 server                           │   │
│  │ 6. 收到回應，顯示通知（不朗讀）              │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 技術選型

| 層級 | 選擇 | 原因 |
|------|------|------|
| Backend | FastAPI (Python) | 使用者熟悉、async、輕量 |
| LLM | Gemini API | 免費額度高、速度快、中文好 |
| 資料庫 | SQLite | 單機、簡單、不需額外服務 |
| 網路 | ZeroTier | 使用者已有，私有網路 |
| 前端 | iOS 捷徑 | 不需開發 App，原生整合 |
| 通知 | iOS 推播 | 靜音顯示，不朗讀 |
| 鬧鐘 | Apple Watch | 震動喚醒，不吵伴侶 |

---

## API Endpoints

### POST /morning

早安流程。

Request:
```json
{
  "wake_time": "2024-12-04T09:30:00",
  "sleep_start": "2024-12-04T03:47:00",
  "sleep_hours": 5.7
}
```

Response:
```json
{
  "message": "你昨晚 3:47 才睡，又破戒了。今天有 2 個會議，先處理論文的事。",
  "calendar_summary": "- 14:00 團隊會議\n- 16:00 1:1",
  "todo_summary": "- 聯絡教授\n- 訂機票",
  "health_note": "睡眠不足"
}
```

### GET /health

健康檢查，回傳 `{"status": "ok"}`。

### GET /test/morning

開發測試用，不需要 iOS 捷徑也能觸發。

---

## 待實作功能

### P0 - 核心功能
- [x] **SQLite 持久化**：記錄每日睡眠數據與早安快取
- [x] **回應長度限制**：50 字內，適合通知顯示

### P1 - 重要功能
- [x] **Google Calendar OAuth**：完整整合
- [ ] **每週回顧 GET /weekly-review**：睡眠趨勢、目標達成率
- [ ] **職業審計追蹤**：記錄每日工時分配到哪條收入線

### P2 - 擴充功能
- [ ] **Notion 整合**
- [ ] **論文進度追蹤**
- [ ] **運動紀錄整合**（Apple Health workout）

---

## 程式碼規範

```python
# Async 優先
async def fetch_data() -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        return resp.json()

# Type hints 必須
def process(items: list[dict], limit: int = 10) -> str:
    pass

# Pydantic 驗證
class MorningRequest(BaseModel):
    wake_time: datetime
    sleep_start: Optional[datetime] = None
    sleep_hours: Optional[float] = None

# 環境變數
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
```

---

## 重要限制

```
⚠️ 不能上公網
   所有服務都在 ZeroTier 內網運行

⚠️ 不能吵到伴侶
   不使用朗讀功能，只用靜音通知
   鬧鐘用 Apple Watch 震動

⚠️ 通知長度限制
   iOS 通知會截斷，回應控制在 50 字內

⚠️ 健康數據敏感
   睡眠數據只存本地 SQLite
```

---

## LLM Prompt 設計原則

```python
PERSONAL_CONTEXT = """
你是我的個人發展教練。

【我的狀態】
- 全端工程師，6-7 條收入線要簡化成 3 條
- 作息倒置，目標 02:00 前睡
- 碩士論文 6 月要交
- 有同居伴侶

【你的風格】
- 直接講，不囉唆
- 數據有問題就指出
- 繁體中文
- 回應 50 字內（給通知用）

【不要做】
- 過度正向打氣
- 長篇大論
- 反問太多問題
"""
```

---

## 開發指令

```bash
# 安裝
cd personal-ai-assistant
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 編輯 .env 填入 GEMINI_API_KEY

# 啟動
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 測試
curl http://localhost:8000/health
curl http://localhost:8000/test/morning
```

---

## 檔案結構

```
personal-ai-assistant/
├── AGENTS.md                 # Claude Code 指引（本檔案）
├── main.py                   # FastAPI 主程式
├── requirements.txt          # Python 依賴
├── .env.example              # 環境變數範例
├── .env                      # 環境變數（git ignore）
├── README.md                 # 使用者說明
├── IOS_SHORTCUT_GUIDE.md     # iOS 捷徑設定圖解
└── data/
    └── assistant.db          # SQLite（待實作）
```

---

## 關鍵字對照表

當使用者提到這些詞，注意相關背景：

| 關鍵字 | 背景 |
|--------|------|
| 論文 | 碩士，6 月死線，資安方向，教授帶 fuzzing |
| 作息、睡眠 | 目標 02:00 前，現況常 04:00 後 |
| 工作、收入線 | 6-7 條要砍成 3 條 |
| 伴侶 | 同居，系統要靜音 |
| 研替、當兵 | 需要碩士學位 |
| 健身房 | 有會員，三個月沒去 |
| 短影音 | 逃避焦慮的方式 |

---

## 版本紀錄

| 日期 | 變更 |
|------|------|
| 2024-12-05 | 初版：FastAPI + Gemini + iOS 捷徑 |