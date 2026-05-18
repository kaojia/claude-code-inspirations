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
    # Find the section between 今日新增 comment and 歷史收錄 comment
    # Note: comment may contain date like (5/17)
    pattern = r'<!-- ============ 今日新增.*?============ -->.*?<!-- ============ 歷史收錄 ============ -->'
    match = re.search(pattern, html, re.DOTALL)

    if not match:
        print("  ⚠️ Could not find 今日新增 section in HTML")
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

    prompt = f"""Generate 3 Claude Code project ideas in Traditional Chinese. These should be creative, practical, and detailed.

Existing titles to avoid: {', '.join(existing_titles[:5]) if existing_titles else 'none'}

Return a JSON object with a "projects" key containing exactly 3 objects. Here is the EXACT format with an example showing the expected level of detail:

{{"projects": [{{"level": "初階", "title": "個人知識閃卡產生器", "tagline": "把任何文章/PDF 丟進去，自動產出可印或匯入 Anki 的學習卡片", "description": "給 Claude Code 一份 PDF、教科書章節、會議簡報，請它幫你抽出核心概念，產出「正面問題／背面答案」的閃卡，並輸出成 CSV（可匯入 Anki）+ 可印的 PDF 兩種格式。準備證照考試、學新領域、做讀書會的人特別好用。", "prompt": "這份 PDF [拖曳檔案] 是我要學的內容。請幫我：1. 抽出 20 個最值得記住的概念 2. 每個概念做成一張閃卡：正面一個問題、背面精簡答案+記憶口訣 3. 輸出 flashcards.csv（Anki 匯入格式）和 flashcards.pdf（A4 印 6 張卡）", "tip": "讓初學者體驗 Claude「閱讀理解＋整理輸出」的能力，做完馬上能用在自己的學習上", "category": "生產力", "duration": "25", "source_link": "https://docs.anthropic.com"}}, {{"level": "中階", "title": "專案標題", "tagline": "一句話描述這個工具做什麼、給誰用", "description": "2-3 句話詳細說明這個專案的功能、使用場景、產出物。要讓讀者看完就知道做出來長什麼樣。", "prompt": "詳細的起手式提示詞，包含具體步驟、資料夾結構、預期產出格式等，讓使用者可以直接複製貼到 Claude Code 使用", "tip": "說明為什麼這個難度適合中階，會學到什麼技能", "category": "內容創作", "duration": "60", "source_link": "https://example.com"}}, {{"level": "高階", "title": "專案標題", "tagline": "一句話描述", "description": "詳細說明", "prompt": "詳細提示詞", "tip": "為何適合高階", "category": "程式原型", "duration": "120", "source_link": "https://example.com"}}]}}

STRICT RULES:
1. Return ONLY valid JSON. No explanation, no markdown code blocks.
2. Start with {{ and end with }}
3. IMPORTANT - Content must be DETAILED and RICH:
   - title: 6-12 chars, creative and specific
   - tagline: 20-50 chars, one sentence describing what it does
   - description: 80-200 chars, 2-3 sentences with use cases and output
   - prompt: 150-400 chars, detailed step-by-step instructions users can copy-paste
   - tip: 40-80 chars, explain why this difficulty level is appropriate
4. category must be one of: 生產力, 內容創作, 資料分析, 程式原型
5. source_link must be a valid https URL (use real documentation links)
6. All text in Traditional Chinese
7. Make each project unique, creative, and immediately actionable"""

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
        'max_tokens': 4096,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ]
    }

    print(f"  Sending request to {API_URL}")
    print(f"  Model: {data['model']}")
    print(f"  Max tokens: {data['max_tokens']}")
    print(f"  Headers set: {list(headers.keys())}")
    print(f"  API Key length: {len(ANTHROPIC_API_KEY)}")

    response = requests.post(API_URL, headers=headers, json=data)

    print(f"  Response status: {response.status_code}")

    if response.status_code != 200:
        print(f"  ❌ Error response body:")
        print(f"  {response.text[:1000]}")
        response.raise_for_status()

    result = response.json()
    print(f"  ✓ Response parsed successfully")

    # Check if response was truncated
    stop_reason = result.get('stop_reason', '')
    print(f"  Stop reason: {stop_reason}")
    if stop_reason == 'max_tokens':
        print(f"  ⚠️ Response was truncated (hit max_tokens limit)")

    # Extract content from response
    if 'content' not in result:
        print(f"  ❌ No 'content' in response!")
        raise ValueError("No 'content' in API response")

    content = result['content'][0]['text']
    print(f"  Content length: {len(content)}")
    print(f"  Content preview: {content[:200]}...")

    # Parse JSON from response
    dict_content = content.strip()

    # Remove markdown code block wrapper if present
    if dict_content.startswith('```'):
        dict_content = re.sub(r'^```\w*\n?', '', dict_content)
        dict_content = re.sub(r'\n?```$', '', dict_content)
        dict_content = dict_content.strip()

    # Extract JSON object
    dict_start = dict_content.find('{')
    dict_end = dict_content.rfind('}') + 1

    if dict_start != -1 and dict_end > dict_start:
        dict_content = dict_content[dict_start:dict_end]
        print(f"  ✓ Extracted JSON from response")
    else:
        print(f"  ❌ No JSON object found in response")
        print(f"  Content: {dict_content[:300]}")
        raise ValueError("No JSON structure found in Claude response")

    # Try JSON parsing first (more reliable for this use case)
    try:
        projects_data = json.loads(dict_content)
        print(f"  ✓ JSON parsed successfully")
        return projects_data['projects']
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON parse error: {e}")
        print(f"  Trying ast.literal_eval fallback...")

    # Fallback to ast.literal_eval for Python dict format
    import ast
    try:
        projects_data = ast.literal_eval(dict_content)
        print(f"  ✓ ast.literal_eval parsed successfully")
        return projects_data['projects']
    except (ValueError, SyntaxError) as e2:
        print(f"  ❌ ast.literal_eval also failed: {e2}")
        print(f"  Content (first 500 chars): {dict_content[:500]}")
        raise ValueError("Unable to parse Claude API response - likely truncated output")

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
    # The actual HTML structure uses:
    # <!-- ============ 今日新增 (date) ============ -->
    # <h3 class="section-title">...</h3>
    # [cards]
    # <!-- ============ 歷史收錄 ============ -->
    today_pattern = r'(<!-- ============ 今日新增.*?============ -->\s*<h3 class="section-title">.*?</h3>).*?(<!-- ============ 歷史收錄 ============ -->)'
    today_replacement = r'\1\n' + new_cards_html + '\n  \2'

    html = re.sub(today_pattern, today_replacement, html, flags=re.DOTALL)

    # 6. Update history section title and add new history cards
    # Actual structure: <!-- ============ 歷史收錄 ============ -->
    #                   <h3 class="section-title archive">...</h3>
    history_pattern = r'(<!-- ============ 歷史收錄 ============ -->\s*<h3 class="section-title archive">.*?</h3>)\s*'
    history_replacement = r'\1\n' + history_cards_html

    html = re.sub(history_pattern, history_replacement, html, flags=re.DOTALL)

    # 7. Update header: last update date and total count
    # Update date
    html = re.sub(
        r'📅 最後更新：[\d/]+',
        f'📅 最後更新：{long_date}',
        html
    )

    # Update total count
    total_match = re.search(r'<span id="totalCount">(\d+)</span>', html)
    if total_match:
        new_count = int(total_match.group(1)) + 3
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

    # 8. Update today's section comment and title
    # Update comment: <!-- ============ 今日新增 (old) ============ -->
    html = re.sub(
        r'<!-- ============ 今日新增.*?============ -->',
        f'<!-- ============ 今日新增 ({short_date}) ============ -->',
        html
    )
    # Update the h3 title text
    html = re.sub(
        r'(今日新增 ·) [\d/]+',
        f'\\1 {long_date}',
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
