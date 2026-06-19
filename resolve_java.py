import re, os

base = r'E:\Python-Project\ouragent'
files = [
    'javaarea/src/main/java/com/edu/agent/module/chat/service/impl/ChatServiceImpl.java',
    'javaarea/src/main/java/com/edu/agent/module/schedule/dto/CreateCourseRequest.java',
    'javaarea/src/main/java/com/edu/agent/module/schedule/dto/ScheduleCourseDTO.java',
    'javaarea/src/main/java/com/edu/agent/module/schedule/dto/ScheduleWeekViewDTO.java',
    'javaarea/src/main/java/com/edu/agent/module/schedule/entity/ScheduleCourse.java',
]

for f in files:
    path = os.path.join(base, f)
    with open(path, 'r', encoding='utf-8') as fh:
        content = fh.read()
    
    # Resolve all conflicts by keeping OUR side (HEAD)
    pattern = r'<<<<<<< HEAD\n(.*?)=======\n.*?>>>>>>> [^\n]+\n'
    content = re.sub(pattern, r'\1', content, flags=re.DOTALL)
    
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(content)
    
    # Verify no conflicts remain
    if '<<<<<<<' in content:
        print(f'WARNING: {f} still has conflicts!')
    else:
        print(f'Resolved: {os.path.basename(f)}')
