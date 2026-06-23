#!/usr/bin/env python3
"""合并 W21-W24 四个 HTML 页面为单一可独立运行的文件"""

import re

LESSONS = ['W21', 'W22', 'W23', 'W24']
TITLES = {
    'W21': 'W21 · 老鼠的故事',
    'W22': 'W22 · 人的故事',
    'W23': 'W23 · 狐狸的故事（一）',
    'W24': 'W24 · 狐狸的故事（二）',
}

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_between(content, start_tag, end_tag):
    start = content.find(start_tag)
    end = content.find(end_tag, start)
    if start == -1 or end == -1:
        return ''
    return content[start + len(start_tag):end]

def extract_body(content):
    # 提取 <body...> 到 </body> 之间的内容
    m = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL)
    if m:
        return m.group(1)
    return ''

def extract_css(content):
    return extract_between(content, '<style>', '</style>')

def extract_js(content):
    return extract_between(content, '<script>', '</script>')

# 读取所有文件
pages = {}
for w in LESSONS:
    content = read_file(f'lessons/{w}.html')
    pages[w] = {
        'css': extract_css(content),
        'js': extract_js(content),
        'body': extract_body(content),
    }

# 生成合并后的CSS（每个页面加命名空间，公共部分只保留一份）
# W21 的 CSS 最完整，作为基础；其他页面的 CSS 作为补充
base_css = pages['W21']['css']

# 额外 CSS：其他页面有但 W21 没有的规则（粗略处理，直接包含所有）
extra_css = {}
for w in ['W22', 'W23', 'W24']:
    extra_css[w] = pages[w]['css']

# 生成合并后的 JS（每个函数加前缀，用 IIFE 隔离）
def namespace_js(js, prefix):
    """给 JS 里的函数调用加命名空间（简单处理：wrap in IIFE with window exposure）"""
    # 找出所有 function 定义，把它们挂到 window 上以供 HTML onclick 调用
    func_names = re.findall(r'function\s+(\w+)\s*\(', js)
    
    wrapped = f"""
(function() {{
{js}
// 暴露函数到全局（加前缀）
{chr(10).join(f'  window.{prefix}_{fn} = typeof {fn} !== "undefined" ? {fn} : function(){{}};' for fn in func_names)}
}})();
"""
    return wrapped, func_names

# 处理每个页面的 body，把 onclick 函数调用加前缀
def prefix_onclick(body, prefix, func_names):
    for fn in func_names:
        # onclick="fn(...)" -> onclick="prefix_fn(...)"
        body = re.sub(rf'\b{fn}\s*\(', f'{prefix}_{fn}(', body)
    return body

all_js_parts = []
modified_bodies = {}

for w in LESSONS:
    prefix = w.lower()  # w21, w22, w23, w24
    js = pages[w]['js']
    wrapped_js, func_names = namespace_js(js, prefix)
    all_js_parts.append(f'/* ===== {w} JS ===== */\n' + wrapped_js)
    modified_bodies[w] = prefix_onclick(pages[w]['body'], prefix, func_names)

# 组装最终 HTML
tabs_html = '\n'.join([
    f'<button class="tab-btn{" active" if i==0 else ""}" onclick="switchLesson(\'{w}\')" id="tab-{w}">{TITLES[w]}</button>'
    for i, w in enumerate(LESSONS)
])

pages_html = '\n'.join([
    f'<div class="lesson-page{" active" if i==0 else ""}" id="page-{w}">\n{modified_bodies[w]}\n</div>'
    for i, w in enumerate(LESSONS)
])

extra_css_combined = '\n'.join([
    f'/* ===== {w} extra CSS ===== */\n#page-{w} ' + '{ }\n' + extra_css[w]
    for w in ['W22', 'W23', 'W24']
])

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>U6《伊索寓言》下 · W21-W24 课程合集</title>
<style>
/* ===== 全局 Tab 样式 ===== */
.tab-bar {{
  position: fixed; top: 0; left: 0; right: 0; z-index: 200;
  background: #fff; border-bottom: 2px solid #E2E8F0;
  display: flex; align-items: center; padding: 0 16px; height: 48px;
  gap: 4px;
}}
.tab-btn {{
  padding: 8px 20px; border: none; background: none; cursor: pointer;
  font-size: 14px; font-weight: 600; color: #718096; border-radius: 6px 6px 0 0;
  transition: all 0.2s; white-space: nowrap;
}}
.tab-btn:hover {{ background: #EBF0FF; color: #5B7FFF; }}
.tab-btn.active {{ background: #5B7FFF; color: #fff; }}

/* ===== 页面切换 ===== */
.lesson-page {{ display: none; }}
.lesson-page.active {{ display: block; }}

/* ===== 各页面偏移（避免被 tab-bar 遮住 header）===== */
.lesson-page .header {{ top: 48px !important; }}
.lesson-page .container {{ margin-top: calc(56px + 48px) !important; }}
.lesson-page .sidebar {{ top: calc(56px + 48px) !important; height: calc(100vh - 56px - 48px) !important; }}
.lesson-page .content {{ height: calc(100vh - 56px - 48px) !important; }}
.lesson-page .materials {{ height: calc(100vh - 56px - 48px) !important; }}

/* ===== W21 基础 CSS ===== */
{base_css}

/* ===== W22/W23/W24 补充 CSS ===== */
{extra_css_combined}
</style>
</head>
<body>

<!-- Tab 导航 -->
<div class="tab-bar">
  <span style="font-size:13px;font-weight:700;color:#4A5568;margin-right:12px;">📚 U6 伊索寓言下</span>
  {tabs_html}
</div>

<!-- 各周页面 -->
{pages_html}

<script>
function switchLesson(w) {{
  document.querySelectorAll('.lesson-page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('page-' + w).classList.add('active');
  document.getElementById('tab-' + w).classList.add('active');
}}

{chr(10).join(all_js_parts)}
</script>
</body>
</html>
"""

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"生成完成，文件大小: {len(html)} 字节 ({len(html)//1024} KB)")
print("保存到: index.html")
