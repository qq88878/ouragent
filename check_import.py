js_path = r'C:\Users\23705\IdeaProjects\ouragent\frontend\dist\assets\index-b16yT6_n.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Find ChatView import
idx = js.index('ChatView')
context = js[idx:idx+200]
print('ChatView import context:')
print(context[:200])
print()

# Find ProfilePanel reference
if 'ProfilePanel' in js:
    idx2 = js.index('ProfilePanel')
    context2 = js[max(0,idx2-30):idx2+30]
    print('ProfilePanel context:')
    print(context2)
else:
    print('ProfilePanel NOT found in index JS')
    
# Check if ProfilePanel is in the ChatView chunk
cv_path = r'C:\Users\23705\IdeaProjects\ouragent\frontend\dist\assets\ChatView-DQlPFz05.js'
with open(cv_path, 'r', encoding='utf-8') as f:
    cv_js = f.read()
print(f'\nChatView chunk size: {len(cv_js)}')
print(f'Has profile-panel: {"profile-panel" in cv_js}')
print(f'Has ProfilePanel: {"ProfilePanel" in cv_js}')
print(f'Has useProfileStore: {"useProfileStore" in cv_js}')
