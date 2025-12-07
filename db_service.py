import sqlite3
from datetime import datetime, date
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent / "data" / "assistant.db"


def init_db():
    """初始化資料庫，建立所需的表格。"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sleep_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                sleep_start TEXT NOT NULL,
                sleep_end TEXT NOT NULL,
                total_hours REAL NOT NULL,
                actual_sleep_hours REAL NOT NULL,
                deep_hours REAL NOT NULL,
                rem_hours REAL NOT NULL,
                core_hours REAL NOT NULL,
                awake_hours REAL NOT NULL,
                awake_count INTEGER NOT NULL,
                sleep_efficiency REAL NOT NULL,
                quality_score TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS morning_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                summary TEXT NOT NULL,
                weather TEXT NOT NULL,
                events TEXT NOT NULL,
                todos TEXT NOT NULL,
                display TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


@contextmanager
def get_connection():
    """取得資料庫連線。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def save_sleep_record(
    sleep_date: date,
    sleep_start: datetime,
    sleep_end: datetime,
    total_hours: float,
    actual_sleep_hours: float,
    deep_hours: float,
    rem_hours: float,
    core_hours: float,
    awake_hours: float,
    awake_count: int,
    sleep_efficiency: float,
    quality_score: str,
    note: str,
) -> bool:
    """儲存睡眠紀錄，若當天已有紀錄則更新。"""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sleep_records (
                date, sleep_start, sleep_end, total_hours, actual_sleep_hours,
                deep_hours, rem_hours, core_hours, awake_hours, awake_count,
                sleep_efficiency, quality_score, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                sleep_start = excluded.sleep_start,
                sleep_end = excluded.sleep_end,
                total_hours = excluded.total_hours,
                actual_sleep_hours = excluded.actual_sleep_hours,
                deep_hours = excluded.deep_hours,
                rem_hours = excluded.rem_hours,
                core_hours = excluded.core_hours,
                awake_hours = excluded.awake_hours,
                awake_count = excluded.awake_count,
                sleep_efficiency = excluded.sleep_efficiency,
                quality_score = excluded.quality_score,
                note = excluded.note
            """,
            (
                sleep_date.isoformat(),
                sleep_start.isoformat(),
                sleep_end.isoformat(),
                total_hours,
                actual_sleep_hours,
                deep_hours,
                rem_hours,
                core_hours,
                awake_hours,
                awake_count,
                sleep_efficiency,
                quality_score,
                note,
            ),
        )
        conn.commit()
        return True


def get_sleep_record(sleep_date: date) -> dict | None:
    """取得指定日期的睡眠紀錄。"""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM sleep_records WHERE date = ?",
            (sleep_date.isoformat(),),
        ).fetchone()
        return dict(row) if row else None


def get_sleep_records_range(start_date: date, end_date: date) -> list[dict]:
    """取得指定日期範圍的睡眠紀錄。"""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM sleep_records WHERE date BETWEEN ? AND ? ORDER BY date",
            (start_date.isoformat(), end_date.isoformat()),
        ).fetchall()
        return [dict(row) for row in rows]


def get_recent_sleep_records(days: int = 7) -> list[dict]:
    """取得最近 N 天的睡眠紀錄。"""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM sleep_records ORDER BY date DESC LIMIT ?",
            (days,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_morning_cache(cache_date: date) -> dict | None:
    """取得指定日期的早安快取。"""
    import json
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM morning_cache WHERE date = ?",
            (cache_date.isoformat(),),
        ).fetchone()
        if row:
            result = dict(row)
            result["events"] = json.loads(result["events"])
            result["todos"] = json.loads(result["todos"])
            return result
        return None


def save_morning_cache(
    cache_date: date,
    summary: str,
    weather: str,
    events: list[dict],
    todos: list[str],
    display: str,
) -> bool:
    """儲存早安快取，若當天已有則更新。"""
    import json
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO morning_cache (date, summary, weather, events, todos, display)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                summary = excluded.summary,
                weather = excluded.weather,
                events = excluded.events,
                todos = excluded.todos,
                display = excluded.display
            """,
            (
                cache_date.isoformat(),
                summary,
                weather,
                json.dumps(events, ensure_ascii=False),
                json.dumps(todos, ensure_ascii=False),
                display,
            ),
        )
        conn.commit()
        return True


init_db()
