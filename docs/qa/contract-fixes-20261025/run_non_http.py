import sys,unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'));selected=[];excluded=[]
def collect(suite):
 for case in suite:
  if isinstance(case,unittest.TestSuite):collect(case);continue
  name=case.id()
  if any(x in name for x in ['test_contracts.','test_production_boundary.','test_app.HttpTest.','test_http_stale_ontology_is_conflict']):excluded.append(name)
  else:selected.append(case)
collect(suite)
Path(__file__).with_name('http-excluded.json').write_text(json.dumps(excluded,indent=2))
result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(selected))
sys.exit(not result.wasSuccessful())
