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

진행상황 = {0:'접수대기',1:'의뢰대기',2:'의뢰서작성중',3:'결과입력대기',4:'결과입력중',5:'결재대기',6:'검사완료'}
시험구분 = {0:'사전검사',1:'입고검사',2:'생산검사',3:'관리검사',4:'협조시험',5:'기타'}
적합여부 = {0:'부적합',1:'적합',2:'미정'}

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

            elif path == '/today':
                cur.execute("""
                    SELECT 접수번호, 접수일자, 시험구분, 진행상황, 품목코드, 
                           적합여부, 시험담당자, 접수비고
                    FROM 접수 
                    WHERE 접수일자 = CURDATE()
                    ORDER BY 접수번호 DESC
                """)
                rows = cur.fetchall()
                for r in rows:
                    r['진행상황_text'] = 진행상황.get(r.get('진행상황'), '알수없음')
                    r['시험구분_text'] = 시험구분.get(r.get('시험구분'), '알수없음')
                    r['적합여부_text'] = 적합여부.get(r.get('적합여부'), '미정')
                result = {'date': '오늘', 'count': len(rows), 'data': rows}

            elif path == '/pending':
                cur.execute("""
                    SELECT 접수번호, 접수일자, 시험구분, 진행상황, 품목코드,
                           적합여부, 시험담당자
                    FROM 접수 
                    WHERE 진행상황 = 5
                    ORDER BY 접수일자 DESC
                """)
                rows = cur.fetchall()
                for r in rows:
                    r['진행상황_text'] = '결재대기'
                    r['시험구분_text'] = 시험구분.get(r.get('시험구분'), '알수없음')
                    r['적합여부_text'] = 적합여부.get(r.get('적합여부'), '미정')
                result = {'결재대기': len(rows), 'data': rows}

            elif path == '/fail':
                cur.execute("""
                    SELECT 접수번호, 접수일자, 시험구분, 품목코드, 적합여부, 시험담당자
                    FROM 접수 
                    WHERE 적합여부 = 0
                    ORDER BY 접수일자 DESC
                    LIMIT 20
                """)
                rows = cur.fetchall()
                for r in rows:
                    r['적합여부_text'] = '부적합'
                    r['시험구분_text'] = 시험구분.get(r.get('시험구분'), '알수없음')
                result = {'부적합건수': len(rows), 'data': rows}
elif path == '/pending_detail':
                cur.execute("""
                    SELECT a.접수번호, a.접수일자, a.품목코드,
                           b.검사항목, b.기준값, b.측정값, b.적합여부, b.단위
                    FROM 접수 a
                    JOIN 의뢰항목 b ON a.접수번호 = b.접수번호
                    WHERE a.진행상황 = 5
                    ORDER BY a.접수일자 DESC
                """)
                rows = cur.fetchall()
                result = {'count': len(rows), 'data': rows}
            elif path == '/summary':
                cur.execute("""
                    SELECT 진행상황, COUNT(*) as 건수
                    FROM 접수
                    WHERE 접수일자 >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                    GROUP BY 진행상황
                """)
                rows = cur.fetchall()
                for r in rows:
                    r['진행상황_text'] = 진행상황.get(r.get('진행상황'), '알수없음')
                result = {'이번주현황': rows}

            else:
                result = {'error': 'not found', 'available': ['/today', '/pending', '/fail', '/summary']}

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
