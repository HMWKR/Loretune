import json,unittest,sys
from pathlib import Path
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root))
blocked=set(json.loads((Path(__file__).parent/'blocked-http-tests.json').read_text()))
def flatten(suite):
 for case in suite:
  if isinstance(case,unittest.TestSuite):yield from flatten(case)
  else:yield case
suite=unittest.defaultTestLoader.discover(str(root/'tests'))
selected=[t for t in flatten(suite) if t.id() not in blocked]
print('Excluded already-denied listener tests:',len(blocked),flush=True)
r=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(selected));sys.exit(not r.wasSuccessful())
