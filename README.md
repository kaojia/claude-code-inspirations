# Claude Code 精選食譜庫

少而精、驗證過才收錄的 Claude Code 實戰食譜。每則食譜聚焦一個**真實可用**的 Claude Code 能力或工作流，附可直接複製的起手式提示詞，並連到官方文件。

> 改版說明：本專案原為「每日自動生成靈感」，內容多為模型憑空發想、參考連結常失準。已轉型為**策展式食譜庫**——品質優先、有好東西才發，不再每日排程、不再燒 API 費。

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
