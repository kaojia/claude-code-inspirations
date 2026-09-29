#!/usr/bin/env python3
"""
從 recipes.json（單一真實來源）產生 index.html。

用法：
    python scripts/build.py

設計原則：
- 資料與畫面分離：所有內容都在 recipes.json，這支程式只負責套模板。
- 不做正則改 HTML：每次都用 scripts/template.html 全新產生 index.html。
- 版面／搜尋／篩選 JS 沿用原本 template.html，卡片屬性（data-level /
  data-category / data-searchtext / .searchable）保持一致才不會壞掉。
"""

import json
import os
import html as _html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RECIPES_FILE = os.path.join(ROOT, "recipes.json")
TEMPLATE_FILE = os.path.join(HERE, "template.html")
OUTPUT_FILE = os.path.join(ROOT, "index.html")

LEVEL_CLASS = {"初階": "level-1", "中階": "level-2", "高階": "level-3"}
LEVEL_ORDER = {"初階": 0, "中階": 1, "高階": 2}
VALID_CATEGORIES = {"生產力", "內容創作", "資料分析", "程式原型"}


def esc(s):
    return _html.escape(str(s), quote=True)


def validate(recipes):
    """基本欄位檢查，讓資料問題在 build 時就爆出來，而不是上線才發現。"""
    required = ["level", "title", "tagline", "description", "prompt",
                "tip", "category", "duration", "source_link"]
    errors = []
    for i, r in enumerate(recipes):
        for f in required:
            if not r.get(f):
                errors.append(f"recipe[{i}] 缺少欄位：{f}")
        if r.get("level") not in LEVEL_CLASS:
            errors.append(f"recipe[{i}] level 非法：{r.get('level')}")
        if r.get("category") not in VALID_CATEGORIES:
            errors.append(f"recipe[{i}] category 非法：{r.get('category')}")
        link = r.get("source_link", "")
        if link and not link.startswith("https://"):
            errors.append(f"recipe[{i}] source_link 必須是 https：{link}")
    if errors:
        raise SystemExit("❌ recipes.json 驗證失敗：\n  - " + "\n  - ".join(errors))


def render_card(r, badge):
    level_class = LEVEL_CLASS[r["level"]]
    source_label = r.get("source_label", "參考連結")
    searchtext = f"{r['title']} {r['category']} {r.get('tagline','')}"
    return f"""  <article class="card searchable" data-level="{esc(r['level'])}" data-category="{esc(r['category'])}" data-searchtext="{esc(searchtext)}">
    <div class="card-header">
      <span class="badge">{badge}</span>
      <span class="tag {level_class}">{esc(r['level'])}</span>
      <span class="tag">{esc(r['category'])}</span>
      <span class="tag time">{esc(r['duration'])} 分鐘</span>
    </div>
    <h2>{esc(r['title'])}</h2>
    <div class="tagline">{esc(r['tagline'])}</div>
    <p>{esc(r['description'])}</p>
    <div class="prompt-box">{esc(r['prompt'])}</div>
    <div class="tip">
      <span class="tip-label">為什麼收錄</span>
      {esc(r['tip'])}
    </div>
    <a class="source-link" href="{esc(r['source_link'])}" target="_blank" rel="noopener">{esc(source_label)}</a>
  </article>"""


def main():
    with open(RECIPES_FILE, "r", encoding="utf-8") as f:
        recipes = json.load(f)
    validate(recipes)

    # 依難度排序（初階→高階），同難度維持原順序
    recipes.sort(key=lambda r: LEVEL_ORDER.get(r["level"], 9))

    cards = "\n".join(render_card(r, i + 1) for i, r in enumerate(recipes))

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()

    n = len(recipes)
    out = template.replace("<!-- CARDS -->", cards)
    out = out.replace('<span id="totalCount">0</span>', f'<span id="totalCount">{n}</span>')
    out = out.replace('顯示全部 266 個專案', f'顯示全部 {n} 則')
    out = out.replace('<span class="count" id="recipeCount"></span>',
                      f'<span class="count" id="recipeCount">{n} 則精選</span>')

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(out)

    print(f"✅ 已產生 index.html：{n} 則食譜")
    for r in recipes:
        print(f"  - [{r['level']}] {r['title']}（{r['category']}）")


if __name__ == "__main__":
    main()
