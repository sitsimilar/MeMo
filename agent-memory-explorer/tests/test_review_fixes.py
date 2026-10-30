import unittest,itertools,tempfile,json,sqlite3
from core import Store,Conflict
class ReviewFixes(unittest.TestCase):
 def setUp(self):self.s=Store(':memory:');self.d=dict(body='经历',scope='项目 B',modules=['学习'],synthetic=True)
 def test_json_array(self):
  with self.assertRaises(ValueError):self.s.add([])
 def test_idempotent_retry(self):
  a=self.s.add(self.d,'retry');self.assertEqual(a,self.s.add(self.d,'retry'));self.assertEqual(len(self.s.graph()),1)
 def test_key_conflict(self):
  self.s.add(self.d,'retry')
  with self.assertRaises(Conflict):self.s.add(dict(self.d,body='different'),'retry')
  self.assertEqual(len(self.s.graph()),1)
 def test_distinct_intent(self):
  self.s.add(self.d,'one');self.s.add(self.d,'two');self.assertEqual(len(self.s.graph()),2)
 def test_deny_order_independent(self):
  for values in itertools.permutations([True,False,True]):
   rules=[dict(id=str(i),version=1,config={'auto_apply':v}) for i,v in enumerate(values)]
   self.assertFalse(self.s.snapshot('trial',rules)['effective']['auto_apply'])
 def test_history(self):
  n=self.s.add(self.d)['id'];self.s.accept(self.s.propose(n,'改后'));rows=self.s.db.execute('select version,content from content_history where node_id=? order by version',(n,)).fetchall();self.assertEqual([tuple(x) for x in rows],[(1,'经历'),(2,'改后')])
 def test_upgrade_preserves_current(self):
  from pathlib import Path
  with tempfile.TemporaryDirectory() as d:
   db=sqlite3.connect(d+'/old');db.executescript((Path(__file__).parents[1]/'migrations/001.sql').read_text());db.execute("insert into sources(id,scope,body,synthetic) values('s','A','原文',1)");db.execute("insert into nodes values('n','s','当前正文','inferred','accepted',4)");db.commit();db.close();s=Store(d+'/old');self.assertEqual(tuple(s.db.execute('select version,content from content_history').fetchone()),(4,'当前正文'))
