import importlib.util, json, pathlib, socket, sys, unittest
root = pathlib.Path(__file__).parent / 'snapshot'
sys.path.insert(0, str(root))
def denied(*args, **kwargs):
    raise RuntimeError('independent QA forbids socket bind/connect')
socket.socket.bind = denied
socket.socket.connect = denied
socket.socket.connect_ex = denied
names = ['test_desktop_layout','test_desktop_refinement','test_studio_media',
         'test_media_async_lifecycle','test_comment_draft','test_save_feedback','test_studio_state']
suite = unittest.TestSuite()
for name in names:
    spec=importlib.util.spec_from_file_location(name,root/'tests'/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
result=unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
