import re

input_path = r'C:\Users\leegihwi\Desktop\Cway7\2025_해도제작\입력지침\final\adoc_Test\index.html'
output_path = r'C:\Users\leegihwi\Desktop\Cway7\2025_해도제작\입력지침\final\adoc_Test\index_test.html'

with open(input_path, encoding='utf-8') as f:
    html = f.read()

# essential
def replacer_essential(match):
    return f'<span class="essential">{match.group(1).strip()}</span>'
html = re.sub(r'#essential\s*([^<|]+)', replacer_essential, html)

def replacer_F(match):
    return f'<span class="F">{match.group(1).strip()}</span>'

# 큰따옴표(") 또는 유니코드 쌍따옴표(“, ”) 모두 매칭!
pattern = r'#F\s*[\"“]([^\"”]+)[\"”]'
html = re.sub(pattern, replacer_F, html)

# A
def replacer_A(match):
    return f'<span class="A">{match.group(1).strip()}</span>'
html = re.sub(r'#A\s*["“]([^"”]+)["”]', replacer_A, html)
# R
def replacer_R(match):
    return f'<span class="R">{match.group(1).strip()}</span>'
html = re.sub(r'#R\s*["“]([^"”]+)["”]', replacer_R, html)


# ★ 스타일 4줄만 style 끝나기 직전에 삽입!
custom_css = """
.essential { color: #d32f2f; font-weight: bold; }      /* 필수: 빨간색 */
.F         { color: #1976d2; font-weight: bold; }      /* Feature: 파란색 */
.A         { color: #388e3c; font-weight: bold; }      /* Attribute: 녹색 */
.R         { color: #ff6f00; font-weight: bold; }      /* Relation: 주황색 */
"""

# </style> 앞에만 추가
html = html.replace('</style>', custom_css + '\n</style>', 1)


with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

print('변환 완료!')
