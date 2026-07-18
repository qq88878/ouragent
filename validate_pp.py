path = r'C:\Users\23705\IdeaProjects\ouragent\frontend\src\components\ProfilePanel.vue'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

has_template = '<template>' in content and '</template>' in content
has_script = '<script setup>' in content and '</script>' in content
has_style = '<style scoped>' in content and '</style>' in content

print(f'template: {has_template}')
print(f'script setup: {has_script}')
print(f'style scoped: {has_style}')

import_start = content.index('<script setup>')
import_end = content.index('</script>')
script = content[import_start:import_end]

checks = ['useProfileStore', 'useAuthStore', 'ElMessage', 'computed', 'defineProps']
for c in checks:
    print(f'{c}: {c in script}')

# Check template structure
template_start = content.index('<template>')
template_end = content.index('</template>')
template = content[template_start:template_end]

vif = template.count('v-if')
velseif = template.count('v-else-if')
velse = template.count('v-else')
print(f'v-if/v-else-if/v-else: {vif}/{velseif}/{velse}')
print(f'v-for: {template.count("v-for")}')

# Root element
lines = template.split('\n')
for i, line in enumerate(lines[:5]):
    print(f'  L{i+1}: {line.strip()[:80]}')
