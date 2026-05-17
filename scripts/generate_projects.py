#!/usr/bin/env python3
"""
Generate new Claude Code inspiration projects and update index.html
"""

import os
import re
import json
from datetime import datetime
import requests

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
HTML_FILE = 'index.html'
API_URL = 'https://api.anthropic.com/v1/messages'

# Debug: Print API Key status at module load time
print(f"[DEBUG] ANTHROPIC_API_KEY environment variable:")
if ANTHROPIC_API_KEY:
    print(f"  ✓ Set (length: {len(ANTHROPIC_API_KEY)}, starts with: {ANTHROPIC_API_KEY[:20]}...)")
else:
    print(f"  ✗ NOT SET or empty")

def get_today_date():
    """Get today's date in formats needed"""
    today = datetime.now()
    long_date = today.strftime('%Y/%m/%d')
    short_date = today.strftime('%-m/%-d').replace('-m', 'm').replace('-d', 'd')
    # Handle Windows format differences
    if '-' in short_date:
        short_date = f"{today.month}/{today.day}"
    return long_date, short_date

def read_html():
    """Read current HTML file"""
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        return f.read()

def extract_today_cards(html):
    """Extract today's 3 cards from 「今日新增」section"""
    # Find the section between <!-- ============ 今日新增 ============ --> and <!-- ============ 歷史收錄 ============ -->
    pattern = r'<!-- ============ 今日新增 ============ -->.*?<!-- ============ 歷史收錄 ============ -->'
    match = re.search(pattern, html, re.DOTALL)

    if not match:
        return []

    section = match.group(0)
    # Extract all article tags
    cards = re.findall(r'<article class="card searchable".*?</article>', section, re.DOTALL)
    return cards

def extract_history_count(html):
    """Extract the highest badge number from history section"""
    # Find badge numbers in history section
    history_section_match = re.search(
        r'<!-- ============ 歷史收錄 ============ -->.*',
        html,
        re.DOTALL
    )

    if not history_section_match:
        return 0

    history_section = history_section_match.group(0)
    badges = re.findall(r'<span class="badge">(\d+)</span>', history_section)

    if badges:
        return max(int(b) for b in badges)
    return 0

def generate_projects_with_claude(existing_titles):
    """Call Claude API to generate 3 new projects"""

    # Debug: Check API key
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set!")

    print(f"✓ API Key present (length: {len(ANTHROPIC_API_KEY)})")

    prompt = f"""你是「Claude Code 專案靈感集」的內容設計者。

現在已有的專案標題清單（避免重複）：
{', '.join(existing_titles)}

請生成 3 個新的 Claude Code 專項靈感（初階/中階/高階各一個），格式如下的 JSON：

```json
{{
  "projects": [
    {{
      "level": "初階",
      "title": "專案標題",
      "tagline": "一句話 slogan",
      "description": "1-2 句話白話說明",
      "prompt": "直接貼到 Claude Code 的起手式提示詞（含參數與結構）",
      "tip": "為什麼是好的初階專案",
      "category": "生產力",
      "duration": "20",
      "source_link": "https://example.com"
    }},
    {{
      "level": "中階",
      "title": "...",
      "tagline": "...",
      "description": "...",
      "prompt": "...",
      "tip": "...",
      "category": "內容創作",
      "duration": "60",
      "source_link": "https://example.com"
    }},
    {{
      "level": "高階",
      "title": "...",
      "tagline": "...",
      "description": "...",
      "prompt": "...",
      "tip": "為什麼是好的高階專案",
      "category": "程式原型",
      "duration": "180",
      "source_link": "https://example.com"
    }}
  ]
}}
```

規則：
- 初階：20-30 分鐘、新手友善
- 中階：45-90 分鐘、用到 Skill 或進階技巧
- 高階：2-5 小時、用到 Subagent / MCP / Hooks
- 不可重複既有專案概念
- 類別涵蓋多元（生產力、內容創作、資料分析、程式原型）
- prompt 必須是真正可複製貼上的實用 prompt
- source_link 可以是相關參考資源或空字串

請只返回 JSON，不要其他文字。"""

    # Verify API key before sending request
    if not ANTHROPIC_API_KEY or len(ANTHROPIC_API_KEY) < 10:
        raise ValueError(f"Invalid ANTHROPIC_API_KEY: {ANTHROPIC_API_KEY}")

    headers = {
        'x-api-key': ANTHROPIC_API_KEY,
        'content-type': 'application/json',
        'anthropic-version': '2023-06-01'
    }

    data = {
        'model': 'claude-opus-4-6',
        'max_tokens': 2000,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }

    print(f"  Sending request to {API_URL}")
    print(f"  Model: claude-opus-4-6")
    print(f"  Headers set: {list(headers.keys())}")
    print(f"  API Key length: {len(ANTHROPIC_API_KEY)}")
    print(f"  Prompt length: {len(prompt)} characters")

    response = requests.post(API_URL, headers=headers, json=data)

    print(f"  Response status: {response.status_code}")
    print(f"  Response headers: {dict(response.headers)}")

    if response.status_code != 200:
        print(f"  ❌ Error response body (first 1000 chars):")
        print(f"  {response.text[:1000]}")
        response.raise_for_status()

    try:
        result = response.json()
        print(f"  ✓ Response parsed successfully")
    except Exception as e:
        print(f"  ❌ Failed to parse JSON: {e}")
        print(f"  Response body: {response.text[:500]}")
        raise
    content = result['content'][0]['text']

    # Extract JSON from response
    json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
    if json_match:
        content = json_match.group(1)

    projects_data = json.loads(content)
    return projects_data['projects']

def level_to_class(level):
    """Convert level name to CSS class"""
    mapping = {'初階': 'level-1', '中階': 'level-2', '高階': 'level-3'}
    return mapping.get(level, 'level-1')

def create_card_html(project, badge, short_date, is_new=False):
    """Create HTML for a single card"""
    level_class = level_to_class(project['level'])

    new_tag = '<span class="tag new">今日新增</span>' if is_new else ''

    html = f"""  <article class="card searchable" data-level="{project['level']}" data-category="{project['category']}" data-searchtext="{project['title']} {project['category']}">
    <div class="card-header">
      <span class="badge">{badge}</span>
      {new_tag}
      <span class="tag {level_class}">{project['level']}</span>
      <span class="tag">{project['category']}</span>
      <span class="tag time">{project['duration']} 分鐘</span>
      <span class="date-tag">{short_date}</span>
    </div>
    <h2>{project['title']}</h2>
    <div class="tagline">{project['tagline']}</div>
    <p>{project['description']}</p>
    <div class="prompt-box">{project['prompt']}</div>
    <div class="tip">
      <span class="tip-label">為什麼是好的{project['level']}專案</span>
      {project['tip']}
    </div>
    <a class="source-link" href="{project['source_link']}" target="_blank" rel="noopener">參考連結</a>
  </article>"""

    return html

def update_html(html, new_projects, long_date, short_date):
    """Update HTML with new projects and move old ones to history"""

    # 1. Extract and remove today's cards
    today_cards = extract_today_cards(html)

    # 2. Get history max badge number
    max_badge = extract_history_count(html)

    # 3. Convert today's cards to history cards
    history_cards_html = ""
    for i, card in enumerate(today_cards):
        # Replace badge number
        new_badge = max_badge + i + 1
        card = re.sub(
            r'<span class="badge">＋</span>',
            f'<span class="badge">{new_badge}</span>',
            card
        )
        # Remove "今日新增" tag
        card = re.sub(
            r'\s*<span class="tag new">今日新增</span>',
            '',
            card
        )
        history_cards_html += "  " + card + "\n"

    # 4. Create new cards for today
    new_cards_html = ""
    for project in new_projects:
        badge = '＋'
        card_html = create_card_html(project, badge, short_date, is_new=True)
        new_cards_html += card_html + "\n"

    # 5. Replace today's section
    # Find today's cards and replace them with new ones
    today_pattern = r'(<!-- ============ 今日新增 ============ -->\s*<h2>今日新增.*?</h2>).*?(<!-- ============ 歷史收錄 ============ -->)'
    today_replacement = r'\1\n' + new_cards_html + '\n  \2'

    html = re.sub(today_pattern, today_replacement, html, flags=re.DOTALL)

    # 6. Update history section title and add new history cards
    history_pattern = r'(<!-- ============ 歷史收錄 ============ -->\s*<h2>歷史收錄</h2>)\s*(.*?)(\n  </section>)'
    history_replacement = r'\1\n' + history_cards_html + r'\2\3'

    html = re.sub(history_pattern, history_replacement, html, flags=re.DOTALL)

    # 7. Update header: last update date and total count
    # Update date
    html = re.sub(
        r'📅 最後更新：[\d/]+',
        f'📅 最後更新：{long_date}',
        html
    )

    # Update total count
    new_count = int(re.search(r'<span id="totalCount">(\d+)</span>', html).group(1)) + 3
    html = re.sub(
        r'<span id="totalCount">\d+</span>',
        f'<span id="totalCount">{new_count}</span>',
        html
    )

    # Update results count
    html = re.sub(
        r'顯示全部 \d+ 個專案',
        f'顯示全部 {new_count} 個專案',
        html
    )

    # 8. Update today's section title
    html = re.sub(
        r'<h2>今日新增.*?</h2>',
        f'<h2>今日新增 · {long_date}</h2>',
        html
    )

    return html

def main():
    try:
        print("Starting daily update...")

        long_date, short_date = get_today_date()
        print(f"Date: {long_date} / {short_date}")

        # Read current HTML
        html = read_html()
        print("✓ Read index.html")
        print(f"  HTML size: {len(html)} bytes")

        # Extract existing titles to avoid duplicates
        existing_titles = re.findall(r'<h2>(.*?)</h2>', html)
        existing_titles = [t for t in existing_titles if t not in ['今日新增', '歷史收錄']]
        print(f"✓ Found {len(existing_titles)} existing projects")
        if existing_titles:
            print(f"  Titles: {', '.join(existing_titles[:5])}{'...' if len(existing_titles) > 5 else ''}")

        # Generate new projects with Claude
        print("🤖 Calling Claude API to generate projects...")
        new_projects = generate_projects_with_claude(existing_titles)
        print(f"✓ Generated {len(new_projects)} new projects:")
        for p in new_projects:
            print(f"  - {p['title']} ({p['level']})")

        # Update HTML
        print("📝 Updating HTML...")
        html = update_html(html, new_projects, long_date, short_date)

        # Write back
        with open(HTML_FILE, 'w', encoding='utf-8') as f:
            f.write(html)
        print("✓ Updated index.html")

        print("\n✅ Daily update completed successfully!")
        print(f"Projects added: {', '.join(p['title'] for p in new_projects)}")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == '__main__':
    main()
