#!/usr/bin/env python3
"""
每週檢查 Claude Code 官方文件的「What's New」有沒有新的一週彙整。

用途：這不是自動生成內容，只是「提醒」。偵測到官方出了新的週報，
就開一個 GitHub Issue 提醒你去看看有沒有值得收錄成食譜的新功能。
要不要加、加什麼，仍由你決定（維持策展式、零 API 費）。

輸出（寫進 $GITHUB_OUTPUT，給 workflow 用）：
  changed = true / false
  week    = 例如 2026-w38
  url     = 該週報頁面網址
純標準庫，不需 pip install。
"""

import os
import re
import sys
import urllib.request

INDEX_URL = "https://code.claude.com/docs/en/whats-new/index.md"
PAGE_BASE = "https://code.claude.com/docs/en/whats-new/"
STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          ".docs-watch", "last_week.txt")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "docs-watch/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def latest_week(text):
    """從 What's New 索引抓出最新的週 slug，例如 2026-w38。"""
    weeks = re.findall(r"whats-new/(\d{4}-w\d{1,2})", text)
    if not weeks:
        return None

    def sort_key(w):
        year, wk = w.split("-w")
        return (int(year), int(wk))

    return max(set(weeks), key=sort_key)


def read_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def write_state(week):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(week + "\n")


def emit(**kwargs):
    out = os.environ.get("GITHUB_OUTPUT")
    lines = [f"{k}={v}" for k, v in kwargs.items()]
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    for line in lines:
        print(line)


def main():
    try:
        index = fetch(INDEX_URL)
    except Exception as e:
        # 抓不到就安靜跳過，不要讓排程失敗吵人
        print(f"⚠️ 無法取得 What's New 索引：{e}")
        emit(changed="false")
        return

    week = latest_week(index)
    if not week:
        print("⚠️ 索引中找不到週報 slug，跳過")
        emit(changed="false")
        return

    previous = read_state()
    print(f"最新週報：{week}；上次記錄：{previous or '(無)'}")

    if week == previous:
        emit(changed="false", week=week)
        return

    write_state(week)
    emit(changed="true", week=week, url=f"{PAGE_BASE}{week}")


if __name__ == "__main__":
    sys.exit(main())
