import re

with open(r'E:\Python-Project\ouragent\frontend\src\App.vue', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove all conflict markers, keep OUR side (HEAD)
# Strategy: replace <<< HEAD ... ======= ... >>> theirs with just the HEAD portion

def resolve_conflict(text):
    pattern = r'<<<<<<< HEAD\n(.*?)=======\n(.*?)>>>>>>> [^\n]+\n'
    def replacer(m):
        ours = m.group(1)
        theirs = m.group(2)
        # For menu/sidebar: keep ours
        if 'el-aside' in ours:
            # Take their wider width
            result = ours.replace('width="200px"', 'width="240px"')
            return result
        # For imports: merge both
        if 'import' in ours or 'WarningFilled' in ours:
            # Get unique imports from both
            our_items = [x.strip() for x in ours.strip().rstrip(',').split(',')]
            their_items = [x.strip() for x in theirs.strip().rstrip(',').split(',')]
            all_items = list(dict.fromkeys(our_items + their_items))
            return '  ' + ', '.join(all_items) + ',\n'
        # Default: keep ours
        return ours
    return re.sub(pattern, replacer, text, flags=re.DOTALL)

content = resolve_conflict(content)

with open(r'E:\Python-Project\ouragent\frontend\src\App.vue', 'w', encoding='utf-8') as f:
    f.write(content)
print('App.vue resolved')
