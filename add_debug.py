path = r'C:\Users\23705\IdeaProjects\ouragent\frontend\src\components\ProfilePanel.vue'
with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Add a bright debug border to the profile-panel
old = '.profile-panel {\n  width: 280px;\n  min-width: 280px;\n  background: var(--color-bg-card, #fff);\n  border-left: 1px solid var(--color-border, #E8ECF3);'
new = '.profile-panel {\n  width: 280px;\n  min-width: 280px;\n  background: var(--color-bg-card, #fff);\n  border-left: 3px solid #F56C6C;\n  outline: 2px dashed #F56C6C;'
content = content.replace(old, new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Debug border added')
