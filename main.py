from http.server import HTTPServer, BaseHTTPRequestHandler
import pymysql
import json
import os
from urllib.parse import urlparse

DB = {
    'host': 'my8002.gabiadb.com',
    'port': 3306,
    'user': 'daeyuadmin',
    'password': 'asdzxcqwe123@',
    'database': 'daeyu',
    'charset': 'utf8mb4'
}

def get_db():
    return pymysql.connect(**DB)

class H(BaseHTTPRequestHandler):
    def send_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        p = urlparse(self.path).path
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_cors()
        self.end_headers()
        try:
            c = get_db()
            cur = c.cursor(pymysql.cursors.DictCursor)
            if p == '/':
                r = {'status': 'ok'}
            elif p == '/tables':
                cur.execute('SHOW TABLES')
                r = {'tables': cur.fetchall()}
            elif p == '/today':
                cur.execute('SELECT * FROM 접수 WHERE 접수일자=CURDATE() ORDER BY 접수번호 DESC')
                r = {'data': cur.fetchall()}
            elif p == '/pending':
                cur.execute('SELECT * FROM 접수 WHERE 진행상황=5 ORDER BY 접수일자 DESC')
                r = {'data': cur.fetchall()}
            elif p == '/pending_detail':
                cur.execute('SELECT a.접수번호,a.접수일자,a.품목코드,b.검사항목,b.기준규격,b.검사결과,b.적합판정 FROM 접수 a JOIN 의뢰항목 b ON a.접수번호=b.접수번호 WHERE a.진행상황=5 ORDER BY a.접수일자 DESC')
                r = {'data': cur.fetchall()}
            elif p == '/fail':
                cur.execute('SELECT * FROM 접수 WHERE 적합여부=0 ORDER BY 접수일자 DESC LIMIT 20')
                r = {'data': cur.fetchall()}
            elif p == '/summary':
                cur.execute('SELECT 진행상황,COUNT(*) as cnt FROM 접수 WHERE 접수일자>=DATE_SUB(CURDATE(),INTERVAL 7 DAY) GROUP BY 진행상황')
                r = {'data': cur.fetchall()}
            else:
                r = {'error': 'not found'}
            c.close()
        except Exception as e:
            r = {'error': str(e)}
        self.wfile.write(json.dumps(r, ensure_ascii=False, default=str).encode())

    def log_message(self, f, *a):
        pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    HTTPServer(('0.0.0.0', port), H).serve_forever()
