import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\23705\IdeaProjects\ouragent\frontend\src\views\ChatView.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

# Find all structural elements in the template
template_start = 0
template_end = 0
for i, line in enumerate(lines):
    if '<template>' in line:
        template_start = i
    if '</template>' in line:
        template_end = i
        break

print(f'Template spans lines {template_start+1} to {template_end+1}')
print()

# Show the indentation-based structure
indent_stack = []
for i in range(template_start+1, template_end):
    line = lines[i]
    stripped = line.strip()
    if not stripped:
        continue
    
    # Calculate indent level (2 spaces per level in Vue convention)
    indent = len(line) - len(line.lstrip())
    level = indent // 2
    
    # Show important structural elements
    if any(kw in stripped for kw in ['<div class="chat-page"', '</div>', '<ProfilePanel', '<el-dialog', '<!-- 用户画像', '<!-- 学习路径弹窗']):
        print(f'L{i+1:4d} [lvl{level}] {stripped[:90]}')

# Now show just the critical area
print('\n=== Critical area around ProfilePanel ===')
for i, line in enumerate(lines):
    stripped = line.strip()
    if 'ProfilePanel' in stripped or '用户画像右侧' in stripped or '学习路径弹窗' in stripped:
        for j in range(max(0, i-3), min(len(lines), i+4)):
            stripped_j = lines[j].rstrip()
            marker = '>>' if j == i else '  '
            print(f'{marker} L{j+1:4d}: {stripped_j[:100]}')
        print()
