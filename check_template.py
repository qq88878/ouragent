path = r'C:\Users\23705\IdeaProjects\ouragent\frontend\src\views\ChatView.vue'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the end of template
in_template = False
for i, line in enumerate(lines):
    if '<template>' in line:
        in_template = True
        continue
    if '</template>' in line:
        in_template = False
        continue
    if not in_template:
        continue
    
    # Show context around ProfilePanel
    if 'ProfilePanel' in line or 'chat-main' in line or 'chat-page' in line:
        start = max(0, i-3)
        end = min(len(lines), i+4)
        print(f'--- Lines {start+1}-{end} ---')
        for j in range(start, end):
            marker = '>>>' if j == i else '   '
            print(f'{marker} {j+1}: {lines[j].rstrip()}')
        print()

# Count div openings and closings
template_str = ''.join(lines)
template_start = template_str.index('<template>') + len('<template>')
template_end = template_str.index('</template>')
template = template_str[template_start:template_end]

import re
div_opens = len(re.findall(r'<div\b', template))
div_closes = len(re.findall(r'</div>', template))
print(f'<div> opens: {div_opens}, </div> closes: {div_closes}')
print(f'Balance: {"OK" if div_opens == div_closes else "MISMATCH!"}')
