# Claude Code 精選食譜庫

少而精、驗證過才收錄的 Claude Code 實戰食譜。每則食譜聚焦一個**真實可用**的 Claude Code 能力或工作流，附可直接複製的起手式提示詞，並連到官方文件。

> 改版說明：本專案原為「每日自動生成靈感」，內容多為模型憑空發想、參考連結常失準。已轉型為**策展式食譜庫**——品質優先，並改為**每週**依官方 What's New 的真實內容自動補充（見下方「每週自動加入」）。

## 線上瀏覽

https://kaojia.github.io/claude-code-inspirations/

## 怎麼新增／修改食譜

內容的**單一真實來源**是 `recipes.json`，`index.html` 由程式產生，不要手動改 HTML。

1. 編輯 `recipes.json`（每則食譜一個物件，欄位見下）。
2. 本機重建：
   ```bash
   python scripts/build.py
   ```
   （會做欄位驗證 + 從 `scripts/template.html` 產生 `index.html`）
3. commit `recipes.json` 與 `index.html` 後 push。
   - GitHub Action（`.github/workflows/daily-update.yml`）也會在 `recipes.json` 變動時自動重建並提交，作為保險。

## 每週自動加入（What's New → 食譜）

`.github/workflows/check-docs-updates.yml` 每週一 09:00（台灣時間）執行：

1. `scripts/check_docs_updates.py` 檢查官方 What's New 有沒有比 `.docs-watch/last_week.txt` 更新的一週彙整。
2. 有新週報 → `scripts/generate_from_whatsnew.py` 抓當週**真實內容**，用 Claude API 起草 1-2 則食譜。
3. **驗證關卡**：每則必須欄位齊全、`source_link` 是**實際可達（HTTP 200）的官方文件頁**、標題不與現有重複，才會被收錄；全部沒通過就不改檔。
4. 通過的食譜寫入 `recipes.json` → 重建 `index.html` → 自動 commit + push 上線。

需要 repo secret **`ANTHROPIC_API_KEY`**（每週一次呼叫，成本極小）。可用環境變數 `CLAUDE_MODEL` 指定模型（預設 `claude-sonnet-5-5`）。

> 這是「直接 commit 上線」模式：AI 起草的食譜會自動公開，不經人工審核。驗證關卡把亂寫／死連結擋掉，但語意品質仍可能參差——不滿意時直接編 `recipes.json` 移除該則再 push 即可。

## recipes.json 欄位

| 欄位 | 說明 |
|---|---|
| `level` | 難度：`初階` / `中階` / `高階` |
| `title` | 食譜標題（簡短具體） |
| `tagline` | 一句話說明做什麼、給誰用 |
| `description` | 2-3 句說明功能、使用場景、產出物 |
| `prompt` | 可直接複製貼上的起手式提示詞 |
| `tip` | 「為什麼收錄」——這則的價值與適用對象 |
| `category` | `生產力` / `內容創作` / `資料分析` / `程式原型` |
| `duration` | 預估分鐘數 |
| `source_link` | **真實** https 連結（優先官方文件） |
| `source_label` | （選填）連結顯示文字，預設「參考連結」 |

## 收錄標準（品質門檻）

- **真的可用**：提示詞是實際跑過、能重現的，不是憑空想像的點子。
- **連結為真**：`source_link` 指向真實可達的頁面，優先官方文件 `code.claude.com/docs`。
- **少而精**：寧缺勿濫，沒有好東西就不發。

## 檔案結構

```
recipes.json          # 內容來源（唯一要編輯的內容檔）
scripts/build.py      # 從 recipes.json + 模板產生 index.html
scripts/template.html # 版面外殼（CSS / 搜尋 / 篩選 JS）
index.html            # 產物，勿手改
```

## 功能

- 即時搜尋（標題、分類、tagline）
- 難度／分類標籤一鍵篩選
- 每則食譜的起手式提示詞附「⧉ 複製」按鈕，一鍵複製整段提示詞
- 統一字體：全站正文與 UI 用 Noto Sans TC，中英文與跨作業系統顯示一致
