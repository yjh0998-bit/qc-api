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
            elif p == '/report':
                cur.execute('SELECT (SELECT COUNT(*) FROM 접수 WHERE 접수일자=CURDATE()) as 오늘접수, (SELECT COUNT(*) FROM 접수 WHERE 진행상황=5) as 결재대기, (SELECT COUNT(*) FROM 접수 WHERE 진행상황=5 AND DATEDIFF(CURDATE(),접수일자)>30) as 초과30일, (SELECT COUNT(*) FROM 의뢰항목 b JOIN 접수 a ON a.접수번호=b.접수번호 WHERE a.진행상황=5 AND b.적합판정=0) as 부적합건수')
                summary = cur.fetchone()
                cur.execute('SELECT a.접수번호, a.접수일자, a.품목코드, a.시험구분, a.시험담당자, a.접수비고, DATEDIFF(CURDATE(),a.접수일자) as 경과일, GROUP_CONCAT(CASE WHEN b.적합판정=0 THEN CONCAT(b.검사항목,":",b.검사결과) END SEPARATOR " | ") as 부적합항목 FROM 접수 a LEFT JOIN 의뢰항목 b ON a.접수번호=b.접수번호 WHERE a.진행상황=5 GROUP BY a.접수번호 ORDER BY a.접수일자 DESC')
                pending = cur.fetchall()
                r = {'요약': summary, '결재대기목록': pending}
            elif p == '/summary':
                cur.execute('SELECT 진행상황,COUNT(*) as cnt FROM 접수 WHERE 접수일자>=DATE_SUB(CURDATE(),INTERVAL 7 DAY) GROUP BY 진행상황')
                r = {'data': cur.fetchall()}
            elif p == '/latest_by_items':
                codes = self.path.split('codes=')[1].split(',') if 'codes=' in self.path else []
                if not codes:
                    r = {'error': 'codes parameter required, e.g. /latest_by_items?codes=200106,200095'}
                else:
                    placeholders = ','.join(['%s'] * len(codes))
                    result_list = []
                    for code in codes:
                        cur.execute(f'SELECT 접수번호, 접수일자, 품목코드, 시험구분, 적합여부, 시험담당자, 검사완료일 FROM 접수 WHERE 품목코드=%s AND 진행상황=6 ORDER BY 접수일자 DESC LIMIT 1', (code,))
                        latest = cur.fetchone()
                        if latest:
                            cur.execute('SELECT 검사항목, 기준규격, 검사결과, 적합판정 FROM 의뢰항목 WHERE 접수번호=%s', (latest['접수번호'],))
                            items = cur.fetchall()
                            latest['검사상세'] = items
                        result_list.append({'품목코드': code, '최근검사': latest})
                    r = {'data': result_list}
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
