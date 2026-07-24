from http.server import BaseHTTPRequestHandler
import socketserver
import logging
from urllib.parse import parse_qs

HOST = "127.0.0.1"
PORT = 18080
LOG_FILE = "logs/access.log"

logging.basicConfig(
    filename=LOG_FILE,
    encoding="utf-8",
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.DEBUG
)

LOGIN_PAGE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>System Admin Login</title>
</head>
<body>
<h1>System Administration</h1>
<p>管理者IDとパスワードを入力してください。</p>
<form method="POST" action="/login">
<label>User ID:</label>
<input type="text" name="username"><br><br>
<label>Password:</label>
<input type="password" name="password"><br><br>
<input type="submit" value="Login">
</form>
</body>
</html>
"""

FAILED_PAGE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>Login Failed</title>
</head>
<body>
<h1>Login Failed</h1>
<p>ユーザー名またはパスワードが正しくありません。</p>
<a href="/">戻る</a>
</body>
</html>
"""

NOT_FOUND_PAGE = """<!DOCTYPE html>
<html lang="ja">
<head><meta charset="utf-8"><title>Not Found</title></head>
<body><h1>404 Not Found</h1></body>
</html>
"""

def safe_text(text):
    """ログに改行や制御文字が入らないように整形する。"""
    text = str(text)
    text = text.replace("\r", "\\r")
    text = text.replace("\n", "\\n")
    text = text.strip()
    return text


class HoneyHandler(BaseHTTPRequestHandler):
    timeout = 5
    server_version = "SimpleWebServer/1.0"
    sys_version = ""

    def do_GET(self):
        path = safe_text(self.path)
        address, port = self.client_address

        logging.info(
            "GET address={} port={} path={}".format(address, port, path)
        )

        if self.path == "/" or self.path.startswith("/index"):
            self.send_html(200, LOGIN_PAGE)
        else:
            logging.warning(
                "Unknown path address={} path={}".format(address, path)
            )
            self.send_html(404, NOT_FOUND_PAGE)

    def do_HEAD(self):
        address, port = self.client_address
        logging.info(
            "HEAD address={} port={} path={}".format(
                address, port, safe_text(self.path)
            )
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        address, port = self.client_address
        content_length_text = self.headers.get("Content-Length", "0")

        if not content_length_text.isdigit():
            logging.warning(
                "Invalid Content-Length address={} value={}".format(
                    address, safe_text(content_length_text)
                )
            )
            self.send_html(400, "<h1>400 Bad Request</h1>")
            return

        content_length = int(content_length_text)

        if content_length > 4096:
            logging.warning(
                "POST too large address={} size={}".format(
                    address, content_length
                )
            )
            self.send_html(413, "<h1>413 Payload Too Large</h1>")
            return

        post_bytes = self.rfile.read(content_length)

        try:
            post_text = post_bytes.decode("utf-8")
        except UnicodeDecodeError:
            logging.warning(
                "Decode error address={} port={}".format(address, port)
            )
            self.send_html(400, "<h1>400 Bad Request</h1>")
            return

        form_data = parse_qs(post_text)
        username = form_data.get("username", [""])[0]
        password = form_data.get("password", [""])[0]

        username = safe_text(username)
        password = safe_text(password)

        logging.debug(
            "LOGIN address={} port={} user='{}' password='{}' path={}".format(
                address,
                port,
                username,
                password,
                safe_text(self.path)
            )
        )

        self.send_html(403, FAILED_PAGE)

    def send_html(self, status_code, html_text):
        response_bytes = html_text.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", "{}".format(len(response_bytes)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(response_bytes)

    def log_message(self, format, *args):
        # 標準エラーへの既定ログをaccess.logへまとめる
        logging.info(
            "HTTP address={} message={}".format(
                self.client_address[0], safe_text(format % args)
            )
        )


socketserver.TCPServer.allow_reuse_address = True

if __name__ == "__main__":
    with socketserver.TCPServer((HOST, PORT), HoneyHandler) as httpd:
        print("*** START HTTP HONEYBOT ***")
        print("URL: http://{}:{}".format(HOST, PORT))
        logging.info("HTTPハニーボット起動 host={} port={}".format(HOST, PORT))

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutdown...")
            logging.info("HTTPハニーボット停止")
