# Check the dist index JS for ChatView reference and import structure
js_path = r'C:\Users\23705\IdeaProjects\ouragent\frontend\dist\assets\index-b16yT6_n.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Check for ChatView lazy import
imports = []
for keyword in ['ChatView', 'ProfilePanel', 'profile.js', 'chat-DQlPFz05', 'ChatView-DQlPFz05']:
    if keyword in js:
        idx = js.index(keyword)
        imports.append(f'{keyword} at pos {idx}')

print(f'JS size: {len(js)}')
for imp in imports:
    print(f'  Found: {imp}')

# Check for Vite preload hints in index.html
html_path = r'C:\Users\23705\IdeaProjects\ouragent\frontend\dist\index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()
print(f'\nIndex HTML:')
print(html)
