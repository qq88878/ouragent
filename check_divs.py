import re, sys
sys.stdout.reconfigure(encoding='utf-8')

# Check the current file
path = r'C:\Users\23705\IdeaProjects\ouragent\frontend\src\views\ChatView.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

template_start = content.index('<template>') + len('<template>')
template_end = content.index('</template>')
template = content[template_start:template_end]

# Remove HTML comments
no_comments = re.sub(r'<!--.*?-->', '', template, flags=re.DOTALL)

div_opens = len(re.findall(r'<div\b', no_comments))
div_closes = len(re.findall(r'</div>', no_comments))
print(f'Current file: <div> opens: {div_opens}, </div> closes: {div_closes}, diff: {div_opens - div_closes}')

# Check git version
import subprocess
result = subprocess.run(['git', 'show', 'HEAD:frontend/src/views/ChatView.vue'], 
                       capture_output=True, text=True, cwd=r'C:\Users\23705\IdeaProjects\ouragent')
if result.returncode == 0:
    orig = result.stdout
    orig_template_start = orig.index('<template>') + len('<template>')
    orig_template_end = orig.index('</template>')
    orig_template = orig[orig_template_start:orig_template_end]
    orig_no_comments = re.sub(r'<!--.*?-->', '', orig_template, flags=re.DOTALL)
    orig_opens = len(re.findall(r'<div\b', orig_no_comments))
    orig_closes = len(re.findall(r'</div>', orig_no_comments))
    print(f'Original file: <div> opens: {orig_opens}, </div> closes: {orig_closes}, diff: {orig_opens - orig_closes}')
else:
    print('Could not get git version:', result.stderr)
