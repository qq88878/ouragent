with open(r'C:\Users\23705\IdeaProjects\ouragent\frontend\src\views\ChatView.vue', 'r', encoding='utf-8') as f:
    content = f.read()

# Find ProfilePanel line
marker = 'ProfilePanel'
idx = content.find(marker)
if idx < 0:
    print('ProfilePanel not found')
    exit(1)

# Find end of ProfilePanel line
line_end = content.find('\n', idx)
line_end = content.find('\n', line_end + 1)  # blank line after

overlay = '''
    <!-- \u8def\u5f84\u751f\u6210\u52a0\u8f7d\u906e\u7f69 -->
    <div v-if="pathGenerating" class="path-generating-overlay">
      <div class="generating-dialog">
        <div class="gen-spinner">
          <svg viewBox="0 0 48 48" width="64" height="64">
            <circle cx="24" cy="24" r="20" fill="none" stroke="#409EFF" stroke-width="3" stroke-dasharray="100" stroke-linecap="round">
              <animateTransform attributeName="transform" type="rotate" from="0 24 24" to="360 24 24" dur="2s" repeatCount="indefinite"/>
            </circle>
          </svg>
          <span class="gen-spinner-text">AI</span>
        </div>
        <h3>AI \u6b63\u5728\u5206\u6790\u5bf9\u8bdd\u5185\u5bb9</h3>
        <p>\u6b63\u5728\u8c03\u7528\u5927\u6a21\u578b\u5206\u6790\u5bf9\u8bdd\uff0c\u751f\u6210\u4e2a\u6027\u5316\u5b66\u4e60\u8def\u5f84...</p>
        <p class="gen-subtitle">\u8bf7\u8010\u5fc3\u7b49\u5f85\uff0c\u901a\u5e38\u9700\u8981 30-60 \u79d2</p>
        <div class="gen-bar">
          <div class="gen-bar-fill"></div>
        </div>
      </div>
    </div>
'''

content = content[:line_end+1] + overlay + content[line_end+1:]
print('Overlay added after ProfilePanel')

# Also add CSS for the overlay
# Find </style> and add CSS before it
style_end = content.rfind('</style>')
if style_end > 0:
    css = '''
.path-generating-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.6); z-index: 9999;
  display: flex; align-items: center; justify-content: center;
}
.generating-dialog {
  background: #fff; border-radius: 16px; padding: 40px 48px;
  text-align: center; max-width: 420px; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
.gen-spinner { position: relative; width: 64px; height: 64px; margin: 0 auto 20px; }
.gen-spinner-text {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
  font-size: 18px; font-weight: 700; color: #409EFF;
}
.generating-dialog h3 { font-size: 20px; font-weight: 700; color: #303133; margin-bottom: 8px; }
.generating-dialog p { font-size: 14px; color: #606266; margin-bottom: 4px; }
.gen-subtitle { font-size: 12px !important; color: #909399 !important; }
.gen-bar {
  width: 100%; height: 4px; margin-top: 20px;
  background: #E4E7ED; border-radius: 2px; overflow: hidden;
}
.gen-bar-fill {
  width: 30%; height: 100%;
  background: linear-gradient(90deg, #409EFF, #67C23A, #409EFF);
  background-size: 200% 100%;
  animation: gen-bar-slide 1.5s ease-in-out infinite;
  border-radius: 2px;
}
@keyframes gen-bar-slide {
  0% { background-position: 100% 0; width: 20%; }
  50% { background-position: 0 0; width: 80%; }
  100% { background-position: 100% 0; width: 20%; }
}
'''
    content = content[:style_end] + css + '\n' + content[style_end:]
    print('CSS added')
else:
    print('</style> not found')

with open(r'C:\Users\23705\IdeaProjects\ouragent\frontend\src\views\ChatView.vue', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
