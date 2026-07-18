# Check where useProfileStore is bundled
index_path = r'C:\Users\23705\IdeaProjects\ouragent\frontend\dist\assets\index-b16yT6_n.js'
cv_path = r'C:\Users\23705\IdeaProjects\ouragent\frontend\dist\assets\ChatView-DQlPFz05.js'

for label, path in [('index', index_path), ('ChatView', cv_path)]:
    with open(path, 'r', encoding='utf-8') as f:
        js = f.read()
    print(f'{label}: useProfileStore={("useProfileStore" in js)}, profile-panel={("profile-panel" in js)}, loadBasicProfile={("loadBasicProfile" in js)}')

# Also check if there's a separate profile chunk
import os
dist = r'C:\Users\23705\IdeaProjects\ouragent\frontend\dist\assets'
for f in os.listdir(dist):
    if f.endswith('.js'):
        fpath = os.path.join(dist, f)
        with open(fpath, 'r', encoding='utf-8') as fh:
            content = fh.read()
        if 'useProfileStore' in content or 'loadBasicProfile' in content:
            print(f'  Found in: {f} ({len(content)} bytes)')
