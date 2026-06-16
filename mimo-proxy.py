"""TLS forward proxy - runs on host, forwards HTTP -> HTTPS to MIMO API using urllib3"""
import http.server
import json
import sys
import urllib3

urllib3.disable_warnings()

http_pool = urllib3.PoolManager(
    cert_reqs="CERT_NONE",
    assert_hostname=False,
    timeout=urllib3.Timeout(connect=10, read=60),
    retries=1,
)

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        auth = self.headers.get("Authorization", "")

        try:
            resp = http_pool.request(
                "POST",
                f"https://token-plan-cn.xiaomimimo.com{self.path}",
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": auth,
                },
            )
            self.send_response(resp.status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(resp.data)
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 18080
    httpd = http.server.HTTPServer(("0.0.0.0", port), ProxyHandler)
    print(f"MIMO TLS proxy on port {port}")
    httpd.serve_forever()
