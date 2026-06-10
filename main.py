from http.server import HTTPServer, BaseHTTPRequestHandler
import pymysql
import json
import os
from urllib.parse import urlparse

DB_CONFIG = {
    'host': 'my8002.gabiadb.com',
    'port': 3306,
    'user': 'daeyuadmin',
    'password': 'asdzxcqwe123@',
    'database': 'daeyu',
    'charset': 'utf8mb4'
}

def get_db():
    return pymysql.connect(**DB_CONFIG)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        try:
            conn = get_db()
            cur = conn.cursor(pymysql.cursors.DictCursor)
            if path == '/':
                result = {'status': 'ok'}
            elif path == '/tables':
                cur.execute('SHOW TABLES')
                result = {'tables': cur.fetchall()}
            elif path == '/data':
                cur.execute('SELECT * FROM 접수 ORDER BY 1 DESC LIMIT 20')
                result = {'data': cur.fetchall()}
            elif path == '/columns':
                cur.execute('DESCRIBE 접수')
                result = {'columns': cur.fetchall()}
            elif path == '/today':
                cur.execute('SELECT * FROM 접수 ORDER BY 1 DESC LIMIT 10')
                result = {'today': cur.fetchall()}
            else:
                result = {'error': 'not found'}
            conn.close()
        except Exception as e:
            result = {'error': str(e)}
        self.wfile.write(json.dumps(result, ensure_ascii=False, default=str).encode())

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), Handler)
    print(f'서버 시작 포트 {port}')
    server.serve_forever()
