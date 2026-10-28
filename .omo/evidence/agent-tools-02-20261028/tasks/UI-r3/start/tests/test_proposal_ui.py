import pathlib,re,subprocess,tempfile,unittest
class ProposalUITest(unittest.TestCase):
 def test_current_source_renderers_and_states(self):
  source=(pathlib.Path(__file__).resolve().parents[1]/'index.html').read_text();start=source.index('function timelineProposalView');end=source.index('function drawCreationProposals',start)
  code=source[start:end]+'''
const assert=require('node:assert/strict');const esc=s=>String(s).replaceAll('<','&lt;'),creatorDiagnostic=()=>'';
const p={timeline_head:1,ontology:{revision:0,graph:{entities:[]}}},x={id:'private-handle',status:'proposed',description:'<user>',base_version:1,changes:[{clip_index:0,take:1,trim:0,duration:1}],timeline:{clips:[{shot:'A'}]}};
assert.equal(timelineProposalView(p,x).canApply,true);assert.match(timelineProposalMarkup(p,x),/변경안 승인·새 버전 저장/);assert.ok(!timelineProposalMarkup(p,x).includes('<user>'));
x.base_version=0;p.timeline_head=null;assert.equal(timelineProposalView(p,x).canApply,true);assert.match(timelineProposalMarkup(p,x),/변경안 승인·새 버전 저장/);p.timeline_head=1;assert.equal(timelineProposalView(p,x).canApply,false);assert.match(timelineProposalMarkup(p,x),/기준 편집이 바뀌/);x.base_version=1;
x.status='applied';assert.equal(timelineProposalView(p,x).canApply,false);assert.ok(!timelineProposalMarkup(p,x).includes('data-proposal-decision'));
x.status='proposed';p.timeline_head=2;assert.equal(timelineProposalView(p,x).canApply,false);assert.match(timelineProposalMarkup(p,x),/기준 편집이 바뀌/);
x.base_version=2;x.commands=[{op:'remove_clips',clip_indices:[1]}];x.timeline_diff={removed_clips:[{base_clip_index:1,before:{shot:'A<scene',take:1,trim:0,duration:3}}]};const removed=timelineProposalMarkup(p,x);assert.match(removed,/기준 컷 2 · A&lt;scene · Take 1 · 원본 0초부터 3초/);assert.match(removed,/원본 장면·Take와 이전 편집 버전은 유지/);assert.match(removed,/자막 시각은 자동 이동하지 않습니다/);
x.commands.push({op:'set_clip',clip_index:2,take:1,trim:.25,duration:.5},{op:'set_captions',cues:[]});x.timeline_diff.clips=[{base_clip_index:2,before:{take:1,trim:0,duration:1},after:{take:1,trim:.25,duration:.5}}];const combined=timelineProposalMarkup(p,x);assert.match(combined,/기준 컷 3: Take 1 · 원본 0초부터 1초 → Take 1 · 원본 0.25초부터 0.5초/);assert.match(combined,/자막 전체 삭제/);
x.timeline_diff.captions={changed:false};assert.match(timelineProposalMarkup(p,x),/자막 변경 없음/);x.timeline_diff.captions={changed:true};assert.match(timelineProposalMarkup(p,x),/자막 전체 삭제/);x.commands.push({op:'set_audio_offset',audio_version:1,source_offset_seconds:1});x.timeline_diff.audio={changed:false};assert.match(timelineProposalMarkup(p,x),/원음 시작 위치 변경 없음/);x.timeline_diff.audio={changed:true,before:{source_offset_seconds:0},after:{source_offset_seconds:1}};assert.match(timelineProposalMarkup(p,x),/원음 시작: 0초 → 1초/);
x.timeline_diff={removed_clips:[]};assert.equal(timelineProposalView(p,x).canApply,false);assert.match(timelineProposalMarkup(p,x),/제외할 컷 정보를 확인할 수 없습니다/);assert.ok(!timelineProposalMarkup(p,x).includes('data-proposal-decision'));
const add={id:'add',status:'proposed',description:'추가',base_version:2,commands:[{op:'append_clips',clips:[{source_shot_id:'s',source_take_id:1,trim:0,duration:1}]}],timeline:{clips:[{shot:'A',take:1,trim:0,duration:1},{shot:'B<new',take:1,trim:0,duration:1}]},timeline_diff:{added_clips:[{proposed_clip_index:1,after:{shot:'B<new',take:1,trim:0,duration:1}}]}};
assert.equal(timelineProposalView(p,add).canApply,true);assert.match(timelineProposalMarkup(p,add),/추가: 2번 컷 · B&lt;new · Take 1/);add.timeline_diff.added_clips[0].after.take=9;assert.equal(timelineProposalView(p,add).canApply,false);assert.match(timelineProposalMarkup(p,add),/추가할 컷 정보를 확인할 수 없습니다/);

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
