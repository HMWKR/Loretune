import pathlib,re,subprocess,tempfile,unittest
class ProposalUITest(unittest.TestCase):
 def test_current_source_renderers_and_states(self):
  source=(pathlib.Path(__file__).resolve().parents[1]/'index.html').read_text();start=source.index('function timelineProposalView');end=source.index('function drawCreationProposals',start)
  code=source[start:end]+'''
const assert=require('node:assert/strict');const esc=s=>String(s).replaceAll('<','&lt;'),creatorDiagnostic=()=>'';
const p={timeline_head:1,ontology:{revision:0,graph:{entities:[]}}},x={id:'private-handle',status:'proposed',description:'<user>',base_version:1,changes:[{clip_index:0,take:1,trim:0,duration:1}],timeline:{clips:[{shot:'A'}]}};
assert.equal(timelineProposalView(p,x).canApply,true);assert.match(timelineProposalMarkup(p,x),/변경안 승인·새 버전 저장/);assert.ok(!timelineProposalMarkup(p,x).includes('<user>'));
x.status='applied';assert.equal(timelineProposalView(p,x).canApply,false);assert.ok(!timelineProposalMarkup(p,x).includes('data-proposal-decision'));
x.status='proposed';p.timeline_head=2;assert.equal(timelineProposalView(p,x).canApply,false);assert.match(timelineProposalMarkup(p,x),/기준 편집이 바뀌/);
const m={id:'private',base_revision:0,graph:{entities:[{id:'m',type:'character',label:'Mira',description:'Blue',provenance:[{excerpt:'Blue coat'}]}]}};
assert.match(memoryProposalMarkup(p,m),/아직 반영하지 않음/);assert.match(memoryProposalMarkup(p,m),/Blue coat/);assert.ok(!memoryProposalMarkup(p,m).includes('data-ontology-apply'));
m.applied_revision=1;assert.ok(!memoryProposalMarkup(p,m).includes('data-open-memory'));
console.log('proposal state, context, approval separation and escaping pass');
'''
  with tempfile.TemporaryDirectory() as tmp:
   path=pathlib.Path(tmp)/'test.cjs';path.write_text(code);subprocess.run(['node',str(path)],check=True,capture_output=True)
 def test_integrated_creator_core_and_caption_handlers_preserved(self):
  root=pathlib.Path(__file__).resolve().parents[1];s=(root/'index.html').read_text();b=(root/'docs/qa/design-benchmark-20261025/creator-pass/candidate-index.html').read_text()
  for start,end in [('function createTakeReviewStore','// DOM glue.'),("const track=$('#downloadPreview track')",'function drawModelSettings')]:
   self.assertEqual(s[s.index(start):s.index(end,s.index(start))],b[b.index(start):b.index(end,b.index(start))])
  self.assertIn("$('#cancelTimelineDraft').onclick",s);self.assertIn("act('review_timeline_proposal'",s);self.assertIn('data-runtime-blocked',s)
