import sqlite3,json,uuid,math
from pathlib import Path
class Conflict(ValueError): pass
class Store:
 def __init__(self,path):
  self.db=sqlite3.connect(path,check_same_thread=False,isolation_level=None)
  self.db.row_factory=sqlite3.Row
  self.db.execute('PRAGMA foreign_keys=ON')
  self.db.executescript((Path(__file__).parent/'migrations/001.sql').read_text())
  self.db.executescript((Path(__file__).parent/'migrations/002.sql').read_text())
  self.db.execute("INSERT OR IGNORE INTO settings VALUES('auto','false',1)")
 def tx(self,fn):
  self.db.execute('BEGIN IMMEDIATE')
  try:
   result=fn();self.db.execute('COMMIT');return result
  except Exception:self.db.execute('ROLLBACK');raise
 def add(self,d,key=None):
  if not isinstance(d,dict):raise ValueError('请求必须是JSON对象')
  if key is not None and (not isinstance(key,str) or not 1<=len(key)<=128):raise ValueError('幂等键格式错误')
  body=d.get('body','');scope=d.get('scope','')
  if not isinstance(body,str) or not isinstance(scope,str):raise ValueError('正文与范围必须是字符串')
  scope=scope.strip()
  if not body.strip() or not scope or len(body)>20000:raise ValueError('正文与范围必填；正文最多20000字符')
  if type(d.get('synthetic')) is not bool:raise ValueError('必须明确合成／非合成')
  mods=d.get('modules',[])
  if not isinstance(mods,list) or any(not isinstance(x,str) or len(x)>40 for x in mods):raise ValueError('模块格式错误')
  canonical=json.dumps({'scope':scope,'body':body,'modules':mods,'synthetic':d['synthetic']},sort_keys=True,ensure_ascii=False)
  sid=uuid.uuid4().hex;nid=uuid.uuid4().hex
  def work():
   if key is not None:
    prior=self.db.execute('SELECT payload,result FROM source_requests WHERE key=?',(key,)).fetchone()
    if prior:
     if prior['payload']!=canonical:raise Conflict('幂等键已用于不同内容')
     return json.loads(prior['result'])
   self.db.execute('INSERT INTO sources(id,scope,body,synthetic) VALUES(?,?,?,?)',(sid,scope,body,int(d['synthetic'])))
   self.db.execute("INSERT INTO nodes(id,source_id,content,epistemic,review) VALUES(?,?,?,'explicit','unreviewed')",(nid,sid,body))
   self.db.execute('INSERT INTO organization(node_id,modules) VALUES(?,?)',(nid,json.dumps(mods)))
   n=self.db.execute('SELECT count(*) FROM nodes').fetchone()[0];a=n*2.39996
   self.db.execute('INSERT INTO layouts(node_id,x,y,z) VALUES(?,?,?,?)',(nid,math.cos(a)*120,math.sin(a)*100,(n%7-3)*40))
   result={'id':nid,'source_id':sid}
   self.db.execute('INSERT INTO content_history SELECT id,content_version,content,epistemic,review FROM nodes WHERE id=?',(nid,))
   if key is not None:self.db.execute('INSERT INTO source_requests VALUES(?,?,?)',(key,canonical,json.dumps(result)))
   return result
  return self.tx(work)
 def graph(self,scope=None):
  rows=self.db.execute('SELECT n.*,s.scope,s.body,s.synthetic,s.revision AS source_version,o.modules,o.version AS organization_version,l.x,l.y,l.z,l.version AS layout_version FROM nodes n JOIN sources s ON s.id=n.source_id JOIN organization o ON o.node_id=n.id JOIN layouts l ON l.node_id=n.id WHERE s.deleted=0').fetchall()
  return [dict(r,modules=json.loads(r['modules'])) for r in rows if scope is None or r['scope']==scope]
 def layout(self,nid,d):
  vals=[d[k] for k in ('x','y','z')]
  if any(not isinstance(x,(float,int)) or not math.isfinite(x) or abs(x)>10000 for x in vals):raise ValueError('坐标错误')
  cur=self.db.execute('UPDATE layouts SET x=?,y=?,z=?,version=version+1 WHERE node_id=? AND version=?',(*vals,nid,d['version']))
  if cur.rowcount!=1:raise Conflict('布局版本冲突')
 def snapshot(self,kind,rules):
  if kind not in ('organization','trial','call'):raise ValueError('运行类型错误')
  caps={'rounds':3,'depth':2,'proposals':8,'calls':0}
  merged={'recall_raw':True,'auto_apply':False,**caps};trace=[]
  for rule in rules:
   if set(rule)!={'id','version','config'}:raise ValueError('规则需包含id、version、config')
   for k,v in rule['config'].items():
    if k in caps:
     if type(v)!=int or v<0:raise ValueError('预算须为非负整数')
     chosen=min(merged[k],v)
    elif k in ('recall_raw','auto_apply'):
     if type(v)!=bool:raise ValueError('规则须为布尔值')
     chosen=merged[k] and v if k=='recall_raw' else (v if not any(t['field']==k for t in trace) else merged[k] and v)
    else:raise ValueError('未知规则')
    trace.append({'rule':rule['id'],'field':k,'before':merged[k],'requested':v,'chosen':chosen});merged[k]=chosen
  snap={'rules':rules,'effective':merged,'trace':trace,'auto_state':dict(self.db.execute("SELECT value,version FROM settings WHERE key='auto'").fetchone())}
  rid=uuid.uuid4().hex;self.db.execute('INSERT INTO runs VALUES(?,?,?)',(rid,kind,json.dumps(snap)));return {'id':rid,**snap}
 def propose(self,nid,content,depends_org=False):
  row=next(x for x in self.graph() if x['id']==nid)
  deps={'content_version':row['content_version'],'source_version':row['source_version']}
  if depends_org:deps['organization_version']=row['organization_version']
  pid=uuid.uuid4().hex
  self.db.execute('INSERT INTO proposals(id,node_id,payload,deps) VALUES(?,?,?,?)',(pid,nid,json.dumps({'content':content}),json.dumps(deps)));return pid
 def accept(self,pid,edited=None,actor='human'):
  def work():
   p=self.db.execute('SELECT * FROM proposals WHERE id=?',(pid,)).fetchone()
   if not p or p['status']!='pending':raise Conflict('提案不存在或已提交')
   rows=[x for x in self.graph() if x['id']==p['node_id']]
   if not rows:raise Conflict('来源已删除')
   row=rows[0]
   if any(row[k]!=v for k,v in json.loads(p['deps']).items()):raise Conflict('依赖版本变化')
   if actor=='policy' and self.db.execute("SELECT value FROM settings WHERE key='auto'").fetchone()[0]!='true':raise Conflict('自动应用已暂停')
   if actor not in ('human','policy'):raise ValueError('接受者错误')
   payload=edited if edited is not None else json.loads(p['payload'])
   if set(payload)!={'content'} or not isinstance(payload['content'],str) or not payload['content'].strip() or len(payload['content'])>20000:raise ValueError('候选内容不合法')
   self.db.execute("UPDATE nodes SET content=?,content_version=content_version+1,review='accepted' WHERE id=?",(payload['content'],p['node_id']))
   self.db.execute('INSERT INTO content_history SELECT id,content_version,content,epistemic,review FROM nodes WHERE id=?',(p['node_id'],))
   self.db.execute("UPDATE proposals SET status='accepted',accepted_by=? WHERE id=?",(actor,pid))
  return self.tx(work)
