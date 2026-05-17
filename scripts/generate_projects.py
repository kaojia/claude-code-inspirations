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

    prompt = f"""Generate 3 Claude Code project ideas.

Existing titles to avoid: {', '.join(existing_titles[:3]) if existing_titles else 'none'}

Return this EXACT format - a Python dictionary with a "projects" key containing a list of 3 dictionaries:

{{"projects": [{{"level": "初階", "title": "終端機計時器", "tagline": "CLI計時", "description": "短說明", "prompt": "提示詞", "tip": "為何好", "category": "生產力", "duration": "25", "source_link": "url"}}, {{"level": "中階", "title": "標題", "tagline": "tag", "description": "說明", "prompt": "prompt", "tip": "tip", "category": "內容創作", "duration": "60", "source_link": "link"}}, {{"level": "高階", "title": "標題", "tagline": "tag", "description": "說明", "prompt": "prompt", "tip": "tip", "category": "程式原型", "duration": "120", "source_link": "link"}}]}}

IMPORTANT: Return ONLY the dictionary. No explanation, no markdown. Start with {{ and end with }}."""

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

    print(f"  Response keys: {list(result.keys())}")

    # Extract content from response
    if 'content' not in result:
        print(f"  ❌ No 'content' in response!")
        print(f"  Full response: {result}")
        raise ValueError("No 'content' in API response")

    content = result['content'][0]['text']
    print(f"  Content length: {len(content)}")
    print(f"  Content preview: {content[:200]}...")

    # Extract Python dict from response
    import ast
    dict_content = content.strip()

    # Try to find dict/list pattern
    dict_start = dict_content.find('{')
    dict_end = dict_content.rfind('}') + 1

    if dict_start != -1 and dict_end > dict_start:
        dict_content = dict_content[dict_start:dict_end]
        print(f"  ✓ Extracted dict from response")
    else:
        print(f"  ❌ No dict found in response")
        print(f"  Content: {dict_content[:200]}")
        raise ValueError("No dict structure found in Claude response")

    print(f"  Dict content preview: {dict_content[:100]}...")

    try:
        # Use ast.literal_eval for safer Python dict parsing
        projects_data = ast.literal_eval(dict_content)
        print(f"  ✓ Dict parsed successfully with ast.literal_eval")
        return projects_data['projects']
    except (ValueError, SyntaxError) as e:
        print(f"  ❌ Dict parse error: {e}")
        print(f"  Trying JSON fallback...")

        try:
            # Fallback to JSON
            projects_data = json.loads(dict_content)
            print(f"  ✓ JSON fallback succeeded")
            return projects_data['projects']
        except:
            print(f"  ❌ Both parsing methods failed")
            print(f"  Content: {dict_content[:300]}")
            raise ValueError("Unable to parse Claude API response")

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
