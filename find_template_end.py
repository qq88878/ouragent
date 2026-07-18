path = r'C:\Users\23705\IdeaProjects\ouragent\frontend\src\views\ChatView.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Find all occurrences of </template>
import re
for m in re.finditer(r'</template>', content):
    pos = m.start()
    line_num = content[:pos].count('\n') + 1
    # Show context
    start = max(0, pos - 50)
    end = min(len(content), pos + 50)
    context = content[start:end].replace('\n', '\\n')
    print(f'</template> at line {line_num}, pos {pos}')
    print(f'  Context: ...{context}...')
    print()
