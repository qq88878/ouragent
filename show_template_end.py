import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\23705\IdeaProjects\ouragent\frontend\src\views\ChatView.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

# Find template end
for i, line in enumerate(lines):
    if '</template>' in line:
        # Show lines around it
        for j in range(max(0, i-8), min(len(lines), i+3)):
            stripped = lines[j].rstrip()
            print(f'L{j+1:4d}: {stripped[:120]}')
        break
