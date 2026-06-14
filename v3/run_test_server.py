"""启动测试服务器，提供检索测试页面"""

import asyncio
import json
import sys
import io
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# 修复 Windows 编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

print("正在初始化向量库...", flush=True)

from src.core.rag import RAGPipeline, VectorStore, create_embedding_provider

# 初始化向量库
embedding_provider = create_embedding_provider(provider="local")
vector_store = VectorStore(dimension=768)
store_path = str(Path(__file__).parent / "data" / "vector_store.json")
loaded = vector_store.load(store_path)
rag = RAGPipeline(vector_store=vector_store, embedding_provider=embedding_provider)

print(f"向量库已加载: {loaded} 个文档块", flush=True)


class TestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.serve_html()
        elif self.path.startswith("/api/search"):
            self.handle_search()
        elif self.path == "/api/stats":
            self.handle_stats()
        else:
            super().do_GET()

    def serve_html(self):
        html_path = Path(__file__).parent / "test_search.html"
        if html_path.exists():
            content = html_path.read_text(encoding="utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        else:
            self.send_error(404, "test_search.html not found")

    def handle_search(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        query = params.get("q", [""])[0]
        top_k = int(params.get("top_k", ["5"])[0])

        if not query:
            self.send_json({"error": "缺少查询参数 q"})
            return

        # 执行检索
        loop = asyncio.new_event_loop()
        results = loop.run_until_complete(rag.retrieve(query, top_k=top_k))
        loop.close()

        self.send_json({"query": query, "results": results, "count": len(results)})

    def handle_stats(self):
        stats = rag.stats()
        self.send_json(stats)

    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))


def main():
    port = 8088
    server = HTTPServer(("0.0.0.0", port), TestHandler)
    print(f"测试服务器已启动: http://localhost:{port}", flush=True)
    print("在浏览器中打开即可测试检索功能", flush=True)
    print("按 Ctrl+C 停止服务器", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
