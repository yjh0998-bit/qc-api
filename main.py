from http.server import HTTPServer, BaseHTTPRequestHandler
import pymysql
import json
import os
from urllib.parse import urlparse, parse_qs

DB_CONFIG = {
    'host': 'my8002.gabiadb.com',
    'port': 3306,
    'user': 'admin',
    'password': 'admin0306',
    'database': 'daeyu',
    'charset': 'utf8mb4'
}

def get_connection():
    return pymysql.connect(**DB_CONFIG)

class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        try:
            conn = get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            if path == '/':
                result = {'status': 'ok', 'message': 'QC API 서버 정상 작동중'}

            elif path == '/tables':
                cursor.execute('SHOW TABLES')
                tables = cursor.fetchall()
                result = {'tables': tables}

            elif path == '/status':
                cursor.execute('SHOW TABLES')
                tables = cursor.fetchall()
                result = {'status': 'connected', 'tables': tables}

            else:
                result = {'error': '알 수 없는 경로'}

            conn.close()
        except Exception as e:
            result = {'error': str(e)}

        self.wfile.write(json.dumps(result, ensure_ascii=False, default=str).encode('utf-8'))

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), APIHandler)
    print(f'QC API 서버 시작 - 포트 {port}')
    server.serve_forever()
