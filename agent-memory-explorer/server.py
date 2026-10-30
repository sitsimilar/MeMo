import json,os,argparse
from pathlib import Path
from http.server import HTTPServer,BaseHTTPRequestHandler
from core import Store,Conflict
ROOT=Path(__file__).parent
class Handler(BaseHTTPRequestHandler):
 def send(self,code,data,typ='application/json; charset=utf-8'):
  raw=json.dumps(data,ensure_ascii=False).encode() if typ.startswith('application/json') else data
  self.send_response(code);self.send_header('Content-Type',typ);self.send_header('Content-Length',str(len(raw)));self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)
 def do_GET(self):
  if self.path=='/api/graph':return self.send(200,store.graph())
  if self.path=='/api/health':return self.send(200,{'schema':2,'model_calls':False})
  if self.path in ('/','/app.js','/style.css'):
   name={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}[self.path];typ={'/':'text/html; charset=utf-8','/app.js':'text/javascript; charset=utf-8','/style.css':'text/css; charset=utf-8'}[self.path]
   return self.send(200,(ROOT/'web'/name).read_bytes(),typ)
  self.send(404,{'error':'not found'})
 def do_POST(self):
  try:
   # Browsers may only write from this server; no CORS or external origins.
   origin=self.headers.get('Origin');expected='http://'+self.headers.get('Host','')
   if origin and origin!=expected:return self.send(403,{'error':'origin denied'})
   if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send(415,{'error':'JSON required'})
   size=int(self.headers.get('Content-Length','0'))
   if not 0<size<=100000:raise ValueError('request size')
   d=json.loads(self.rfile.read(size))
   if not isinstance(d,dict):raise ValueError('请求必须是JSON对象')
   if self.path=='/api/sources':return self.send(201,store.add(d,self.headers.get('Idempotency-Key')))
   if self.path.startswith('/api/layout/'):
    store.layout(self.path.rsplit('/',1)[1],d);return self.send(200,{'saved':True})
   if self.path=='/api/runs':return self.send(201,store.snapshot(d['kind'],d['rules']))
   self.send(404,{'error':'not found'})
  except Conflict as e:self.send(409,{'error':str(e)})
  except (ValueError,KeyError,TypeError) as e:self.send(400,{'error':str(e)})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);p.add_argument('--db',default=str(ROOT/'data/explorer.sqlite'));a=p.parse_args()
 Path(a.db).parent.mkdir(parents=True,exist_ok=True);store=Store(a.db)
 print(f'Open http://127.0.0.1:{a.port}',flush=True);HTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
