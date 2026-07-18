import re, sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\23705\IdeaProjects\ouragent\frontend\src\views\ChatView.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

template_start = content.index('<template>') + len('<template>')
template_end = content.index('</template>')
template = content[template_start:template_end]

div_opens = len(re.findall(r'<div\b', template))
div_closes = len(re.findall(r'</div>', template))
print(f'<div> opens: {div_opens}, </div> closes: {div_closes}')
print(f'Balance: {"OK" if div_opens == div_closes else "MISMATCH - diff=" + str(abs(div_opens - div_closes))}')

# Show lines around ProfilePanel
lines = template.split('\n')
for i, line in enumerate(lines):
    if 'ProfilePanel' in line:
        start = max(0, i-2)
        end = min(len(lines), i+3)
        print(f'\nProfilePanel at line {i+1}:')
        for j in range(start, end):
            marker = '>>>' if j == i else '   '
            print(f'{marker} L{j+1}: {line_for_print(lines[j])}')
        break

def line_for_print(s):
    return s.strip()[:80]
