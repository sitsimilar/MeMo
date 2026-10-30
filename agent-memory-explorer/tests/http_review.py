import subprocess,sys,time,urllib.request,json,tempfile,pathlib,platform,hashlib
base='http://127.0.0.1:18765'
root=pathlib.Path(sys.argv[1]).resolve()
texts=[('项目 A','学习新课程时，我通常先搭知识框架。',['学习']),('项目 A','团队项目开始时，我先明确分工和接口。',['协作']),('项目 A','和同学一起复习时，我会先列知识框架并分配讲解任务。',['学习','协作']),('项目 A','项目 A 当前旅行预算为 8000 元。',['旅行']),('项目 B','项目 B 当前旅行预算为 8000 元。',['旅行'])]
def req(path,d=None):
 r=urllib.request.Request(base+path,data=json.dumps(d).encode() if d is not None else None,headers={'Content-Type':'application/json'});return json.load(urllib.request.urlopen(r))
with tempfile.TemporaryDirectory() as d:
 def start():
  p=subprocess.Popen([sys.executable,'server.py','--db',d+'/validation.sqlite','--port','18765'],cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  for i in range(60):
   try:req('/api/health');return p
   except OSError:time.sleep(.05)
  raise RuntimeError('startup failed')
 p=start()
 try:
  assert req('/api/graph')==[]
  for scope,body,mods in texts:req('/api/sources',dict(scope=scope,body=body,modules=mods,synthetic=True))
  for invalid in ([],None,'text',42):
   request=urllib.request.Request(base+'/api/sources',data=json.dumps(invalid).encode(),headers={'Content-Type':'application/json'})
   try:urllib.request.urlopen(request);raise AssertionError('expected 400')
   except urllib.error.HTTPError as e:assert e.code==400 and 'error' in json.load(e)
  print('invalid JSON shapes: structured 400 passed')
  rows=req('/api/graph');assert len(rows)==5 and sum(x['scope']=='项目 A' for x in rows)==4
  a3=rows[2];req('/api/layout/'+a3['id'],dict(x=43,y=21,z=-9,version=1));after=req('/api/graph');a=after[2];assert a['layout_version']==2 and a['content_version']==a['organization_version']==1
  p.terminate();p.wait();p=start();assert req('/api/graph')==after
  special='  多行中文\n<script>window.__xss=1</script>&"尾部  '
  req('/api/sources',dict(scope='项目 A',body=special,modules=['学习'],synthetic=True));exact=req('/api/graph')[-1]['body']==special
  payload=json.dumps(dict(scope='项目 B',body='幂等测试',modules=['学习'],synthetic=True)).encode()
  def retry_request():return json.load(urllib.request.urlopen(urllib.request.Request(base+'/api/sources',data=payload,headers={'Content-Type':'application/json','Idempotency-Key':'http-retry'})))
  once=retry_request();assert retry_request()==once
  p.terminate();p.wait();p=start();assert retry_request()==once and len(req('/api/graph'))==7
  print('HTTP idempotency including process restart passed')
  print(json.dumps({'five_sources':True,'A3_multi_modules':a3['modules'],'layout_only':True,'restart_persistence':True,'special_text_exact':exact},ensure_ascii=False))
 finally:p.terminate();p.wait()
