#!/usr/bin/env python3
"""
依某一週官方 What's New 的真實內容，用 Claude API 起草 1-2 則食譜，
驗證後 append 進 recipes.json。

與舊版「憑空生成」最大的不同：內容 grounded 在官方真實週報，且每則都要
通過驗證關卡（連結必須是可達的官方文件頁、欄位齊全、標題不重複）才會寫入。
沒有任何一則通過驗證就不改檔（exit 0，讓 workflow 安靜結束）。

環境變數：
  ANTHROPIC_API_KEY  必填
  WEEK_URL           當週週報頁面網址（不含 .md），例如
                     https://code.claude.com/docs/en/whats-new/2026-w38
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECIPES_FILE = os.path.join(ROOT, "recipes.json")
API_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")

VALID_LEVELS = {"初階", "中階", "高階"}
VALID_CATEGORIES = {"生產力", "內容創作", "資料分析", "程式原型"}
DOC_PREFIX = "https://code.claude.com/docs/en/"


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "docs-watch/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def url_ok(url):
    """確認連結真的可達（200），避免 AI 給出幻覺網址。"""
    if not url.startswith(DOC_PREFIX):
        return False
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "docs-watch/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


def call_claude(api_key, week_content):
    prompt = f"""以下是 Claude Code 官方「What's New」某一週的真實彙整內容。請從中挑出「值得做成一則實戰食譜」的新功能或改進，起草 1 到 2 則食譜。

嚴格規則：
1. 只能根據下面內容提到的真實功能，不可自行發明。
2. 每則食譜的 source_link 必須是對應該功能的官方文件頁，格式為 {DOC_PREFIX}<page>（例如 {DOC_PREFIX}hooks、{DOC_PREFIX}skills）。不確定就不要寫這一則。
3. 全繁體中文。只回傳 JSON，不要任何說明或 markdown code block。
4. 格式：{{"recipes": [{{"level": "初階|中階|高階", "title": "6-12字", "tagline": "20-50字一句話", "description": "80-200字，2-3句說明功能/場景/產出", "prompt": "150-400字可複製的起手式提示詞", "tip": "40-80字，為什麼收錄", "category": "生產力|內容創作|資料分析|程式原型", "duration": "分鐘數字串", "source_link": "{DOC_PREFIX}...", "source_label": "官方文件：<頁名>"}}]}}
5. 如果這週沒有值得收錄的新功能，回傳 {{"recipes": []}}。

官方週報內容：
---
{week_content[:12000]}
---"""

    body = json.dumps({
        "model": MODEL,
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL, data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        result = json.loads(r.read().decode("utf-8"))

    text = result["content"][0]["text"].strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    start, end = text.find("{"), text.rfind("}") + 1
    text = text[start:end]
    return json.loads(text).get("recipes", [])


def valid(r, existing_titles):
    required = ["level", "title", "tagline", "description", "prompt",
                "tip", "category", "duration", "source_link"]
    if any(not r.get(f) for f in required):
        return False, "缺欄位"
    if r["level"] not in VALID_LEVELS:
        return False, f"level 非法：{r['level']}"
    if r["category"] not in VALID_CATEGORIES:
        return False, f"category 非法：{r['category']}"
    if r["title"] in existing_titles:
        return False, f"標題重複：{r['title']}"
    if not url_ok(r["source_link"]):
        return False, f"連結不可達或非官方：{r['source_link']}"
    return True, "ok"


def emit_changed(value):
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"added={value}\n")
    print(f"added={value}")


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    week_url = os.environ.get("WEEK_URL")
    if not api_key or not week_url:
        print("❌ 缺 ANTHROPIC_API_KEY 或 WEEK_URL")
        emit_changed("false")
        return 0

    try:
        content = fetch(week_url + ".md")
    except Exception as e:
        print(f"⚠️ 無法取得週報內容：{e}")
        emit_changed("false")
        return 0

    try:
        drafts = call_claude(api_key, content)
    except Exception as e:
        print(f"⚠️ Claude API 失敗：{e}")
        emit_changed("false")
        return 0

    with open(RECIPES_FILE, "r", encoding="utf-8") as f:
        recipes = json.load(f)
    existing_titles = {r["title"] for r in recipes}

    accepted = []
    for d in drafts:
        ok, reason = valid(d, existing_titles)
        if ok:
            d.setdefault("source_label", "參考連結")
            accepted.append(d)
            existing_titles.add(d["title"])
            print(f"✅ 收錄：[{d['level']}] {d['title']}")
        else:
            print(f"⏭️  跳過：{d.get('title','(無標題)')} — {reason}")

    if not accepted:
        print("本週沒有通過驗證的食譜，不改檔。")
        emit_changed("false")
        return 0

    recipes.extend(accepted)
    with open(RECIPES_FILE, "w", encoding="utf-8") as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"共新增 {len(accepted)} 則，recipes.json 已更新。")
    emit_changed("true")
    return 0


if __name__ == "__main__":
    sys.exit(main())
