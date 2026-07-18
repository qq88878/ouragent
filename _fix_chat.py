with open(r'C:\Users\23705\IdeaProjects\ouragent\frontend\src\views\ChatView.vue', 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# Fix 1: Add :loading back to button
old_btn = ':icon="MapLocation"\n              \n              :disabled="messages.length === 0"'
new_btn = ':icon="MapLocation"\n              :loading="pathGenerating"\n              :disabled="messages.length === 0"'
if old_btn in content:
    content = content.replace(old_btn, new_btn)
    changes += 1
    print('1. button :loading added')
else:
    print('1. FAIL')

# Fix 2: Add pathGenerating ref
old_ref = 'let abortController = null;'
new_ref = 'const pathGenerating = ref(false);\nlet abortController = null;'
if old_ref in content:
    content = content.replace(old_ref, new_ref)
    changes += 1
    print('2. pathGenerating ref added')
else:
    print('2. FAIL')

# Fix 3a: pathGenerating = true
old_start = 'const chatMessages = messages.value.map(m => ({ role: m.role, content: m.content }));\n  try {'
new_start = 'pathGenerating.value = true;\n  const chatMessages = messages.value.map(m => ({ role: m.role, content: m.content }));\n  try {'
if old_start in content:
    content = content.replace(old_start, new_start)
    changes += 1
    print('3a. pathGenerating=true added')
else:
    print('3a. FAIL')

# Fix 3b: pathGenerating = false in catch
# Find error message line
search_term = chr(29983)+chr(25104)+chr(22833)+chr(36133)  # 生成失败
idx = content.find(search_term)
if idx >= 0:
    line_start = content.rfind('\n', 0, idx) + 1
    line_end = content.find('\n', idx)
    line = content[line_start:line_end]
    print(f'Found error line: {repr(line)}')
    new_line = line.rstrip() + '\n    pathGenerating.value = false;'
    content = content[:line_start] + new_line + content[line_end:]
    changes += 1
    print('3b. pathGenerating=false added')
else:
    print('3b. FAIL - error text not found')

if changes >= 3:
    with open(r'C:\Users\23705\IdeaProjects\ouragent\frontend\src\views\ChatView.vue', 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'SUCCESS: {changes} fixes applied')
else:
    print(f'ABORT: only {changes} fixes matched')
