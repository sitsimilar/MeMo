import unittest,tempfile
from core import Store,Conflict
class Contracts(unittest.TestCase):
 def setUp(self):
  self.s=Store(':memory:');self.n=self.s.add({'scope':'A','body':'学习实践','modules':['学习','项目'],'synthetic':False})['id']
 def test_migration_repeat(self):
  with tempfile.TemporaryDirectory() as d:
   Store(d+'/x.db');s=Store(d+'/x.db');self.assertEqual([r[0] for r in s.db.execute('select version from schema_version order by version')],[1,2])
 def test_scope(self):self.assertEqual(self.s.graph('B'),[])
 def test_layout_independent(self):
  p=self.s.propose(self.n,'更新');self.s.layout(self.n,dict(x=1,y=2,z=3,version=1));self.s.accept(p);self.assertEqual(self.s.graph()[0]['content_version'],2)
 def test_layout_conflict(self):
  self.s.layout(self.n,dict(x=1,y=2,z=3,version=1))
  with self.assertRaises(Conflict):self.s.layout(self.n,dict(x=1,y=2,z=3,version=1))
 def test_edited_accept_validates(self):
  p=self.s.propose(self.n,'合法')
  with self.assertRaises(ValueError):self.s.accept(p,{'content':''})
  self.assertEqual(self.s.graph()[0]['content_version'],1)
 def test_source_conflict(self):
  p=self.s.propose(self.n,'更新');self.s.db.execute('update sources set revision=2')
  with self.assertRaises(Conflict):self.s.accept(p)
 def test_org_only_if_depended(self):
  p=self.s.propose(self.n,'更新',True);self.s.db.execute('update organization set version=2')
  with self.assertRaises(Conflict):self.s.accept(p)
 def test_org_unrelated(self):
  p=self.s.propose(self.n,'更新');self.s.db.execute('update organization set version=2');self.s.accept(p)
 def test_pause_auto(self):
  p=self.s.propose(self.n,'更新')
  with self.assertRaises(Conflict):self.s.accept(p,actor='policy')
 def test_deleted(self):
  p=self.s.propose(self.n,'更新');self.s.db.execute('update sources set deleted=1')
  with self.assertRaises(Conflict):self.s.accept(p)
 def test_snapshot(self):
  r=self.s.snapshot('trial',[{'id':'budget','version':1,'config':{'calls':100,'rounds':1}}]);self.assertEqual(r['effective']['calls'],0);self.assertEqual(r['effective']['rounds'],1);self.assertTrue(r['trace'])
 def test_synthetic_explicit(self):
  with self.assertRaises(ValueError):self.s.add({'scope':'A','body':'x'})
 def test_human_inference_preserved(self):
  self.s.db.execute("update nodes set epistemic='inferred'");self.s.accept(self.s.propose(self.n,'推断'))
  self.assertEqual(self.s.graph()[0]['epistemic'],'inferred')
if __name__=='__main__':unittest.main()
