# Check if the build produced any warnings that would explain the issue
# Read the ProfilePanel source for potential issues
path = r'C:\Users\23705\IdeaProjects\ouragent\frontend\src\components\ProfilePanel.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Check for potential issues
issues = []

# 1. Check for el-tag usage (needs Element Plus)
if 'el-tag' in content and 'import' not in content:
    issues.append('el-tag used without explicit import')

# 2. Check for el-skeleton
if 'el-skeleton' in content:
    issues.append('el-skeleton used (needs Element Plus)')

# 3. Check for v-model on non-input elements
# 4. Check for duplicate attributes
# 5. Check for undefined refs

# Check CSS for potential issues
style_start = content.index('<style scoped>')
style = content[style_start:]

# Check for syntax errors in CSS
# Look for missing brackets
opens = style.count('{')
closes = style.count('}')
print(f'CSS brackets: {opens} open, {closes} close, diff: {opens - closes}')

# Check for common CSS issues

# Let me check the most important thing: does the template have proper v-if/v-else-if/v-else chain?
template_start = content.index('<template>') + len('<template>')
template_end = content.index('</template>')
template = content[template_start:template_end]

# Count v-if, v-else-if, v-else
vif_count = template.count(' v-if=')
velseif_count = template.count(' v-else-if=')
velse_count = template.count(' v-else')
print(f'v-if: {vif_count}, v-else-if: {velseif_count}, v-else: {velse_count}')

# Check for the profileStore.loading && !profileStore.hasProfile pattern
if 'profileStore.loading && !profileStore.hasProfile' in template:
    print('Loading check pattern: OK')
if 'profileStore.error && !profileStore.hasProfile' in template:
    print('Error check pattern: OK')
if '!profileStore.hasProfile' in template:
    print('Empty check pattern: OK')

print('\nNo obvious template issues found.')
