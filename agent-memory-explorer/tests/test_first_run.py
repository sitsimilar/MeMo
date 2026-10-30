import unittest,json,tempfile
from core import Store,Conflict
class FirstRun(unittest.TestCase):
 def setUp(self):self.s=Store(':memory:');self.n=self.s.add({'body':'  多行中文\n<script>alert(1)</script> & "\n尾部  ','scope':'项目 A','modules':['学习','协作'],'synthetic':True})['id']
 def test_exact_text(self):self.assertEqual(self.s.graph()[0]['body'],'  多行中文\n<script>alert(1)</script> & "\n尾部  ')
 def test_snapshot_immutable(self):
  rules=[{'id':'r','version':1,'config':{'rounds':1}}];r=self.s.snapshot('trial',rules);before=self.s.db.execute('select snapshot from runs where id=?',(r['id'],)).fetchone()[0];rules[0]['config']['rounds']=2;self.s.snapshot('trial',rules);after=self.s.db.execute('select snapshot from runs where id=?',(r['id'],)).fetchone()[0];self.assertEqual(before,after)
 def test_stale_target(self):
  a=self.s.propose(self.n,'a');b=self.s.propose(self.n,'b');self.s.accept(a)
  with self.assertRaises(Conflict):self.s.accept(b)
 def test_duplicate_review(self):
  p=self.s.propose(self.n,'x');self.s.accept(p)
  with self.assertRaises(Conflict):self.s.accept(p)
  self.assertEqual(self.s.graph()[0]['content_version'],2)
 def test_two_modules_one_source(self):
  row=self.s.graph()[0];self.assertEqual(len(self.s.graph()),1);self.assertEqual(row['modules'],['学习','协作'])
 def test_restart_persistence(self):
  with tempfile.TemporaryDirectory() as d:
   s=Store(d+'/x.db');n=s.add({'body':'test','scope':'项目 A','modules':['学习','协作'],'synthetic':True})['id'];s.layout(n,{'x':10,'y':20,'z':30,'version':1});before=s.graph();s.db.close();s=Store(d+'/x.db');self.assertEqual(s.graph(),before)
