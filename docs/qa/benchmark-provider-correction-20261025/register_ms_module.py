"""Prepare native additive KB sidecars; apply only through kb.py guarded CLI."""
from pathlib import Path
import ast, hashlib, importlib.util, json, re, shutil

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent/'registry'
OUT.mkdir(exist_ok=True)
KITS=[ROOT/'docs/knowledge/project_kit',ROOT/'docs/specification/IP_Music_Video_Platform/project_kit']
spec=importlib.util.spec_from_file_location('native_kb',KITS[0]/'kb.py')
kb=importlib.util.module_from_spec(spec);spec.loader.exec_module(kb)
sha=lambda b:hashlib.sha256(b).hexdigest()
source=ROOT/'07_Chat_Directed_Multimodel_Production_Spec.md'
lines=source.read_text().splitlines()
reqs=[];tests=[];sources=[]
for n,line in enumerate(lines,1):
    if re.match(r'\| MS-FR-\d\d \|',line):
        ident,title,priority=[x.strip() for x in line.split('|')[1:4]]
        reqs.append(dict(id=ident,title=title,priority=priority[:2],tests=['MS-'+t for t in re.findall(r'AT\d\d',priority)],line=n))
    if re.match(r'\| AT\d\d \|',line):
        ident,trigger,expected=[x.strip() for x in line.split('|')[1:4]]
        tests.append(dict(id='MS-'+ident,trigger=trigger,expected=expected,line=n))
    if re.match(r'### S\d\d ',line):
        ident,title=line[4:].split(' ',1)
        url=next(x for x in lines[n:n+7] if x.startswith('https://'))
        sources.append(dict(id='MS-'+ident,title=title,url=url,line=n))
assert len(reqs)==28 and len(tests)==38 and len(sources)==21

# These selectors prove only the stated local subset, never full MS-AT acceptance.
mapping={
1:['test_role_independence_preserves_existing_media_and_context'],2:['test_actual_adapter_fake_roundtrip_one_reservation_registered_take_and_safe_receipt'],
3:['test_canonical_tool_plan_final_reply_persist_and_truthful_provenance'],4:['test_context_and_plan_preserve_user_input_no_paid_work'],
5:['test_policy_precedes_execution_no_fallback_or_metadata_activation'],6:['test_policy_precedes_execution_no_fallback_or_metadata_activation'],
7:['test_policy_precedes_execution_no_fallback_or_metadata_activation'],8:['test_policy_precedes_execution_no_fallback_or_metadata_activation'],
9:['test_strict_args_never_accept_actor_endpoint_grant_or_partial_json','test_unapproved_prompt_foreign_project_and_model_authority_rejected'],
10:['test_model_cannot_grant_and_results_are_idempotent'],11:['test_incomplete_refusal_bad_args_and_builtin_tools_never_normalize'],
12:['test_malformed_tool_name_and_semantic_plan_errors_consume_repair_budget'],13:[],14:['test_grant_rights_media_and_price_rechecked_before_submit'],
15:['test_change_rejects_late_run_without_modifying_job_snapshot','test_chat_handoff_and_concurrent_dispatch_keep_same_job'],
16:['test_wrong_role_unknown_and_stale_are_atomic'],17:['test_concurrent_different_actions_cannot_exceed_budget','test_concurrent_cumulative_reservations_never_exceed_cap'],
18:['test_chat_handoff_and_concurrent_dispatch_keep_same_job','test_handoff_omits_reasoning_provider_ids_and_foreign_jobs'],
19:['test_canonical_tool_plan_final_reply_persist_and_truthful_provenance','test_cross_project_proposal_conflict_and_identity_edit'],
20:['test_role_independence_preserves_existing_media_and_context'],21:['test_dependencies_require_owned_collected_approved_output_and_keep_hash'],
22:['test_same_action_parallel_admission_reserves_once_and_survives_reopen'],23:['test_same_action_parallel_admission_reserves_once_and_survives_reopen'],
24:['test_duplicate_conflict_late_request_and_other_project'],25:['test_lost_submission_receipt_preserves_unknown_and_does_not_reissue'],
26:['test_real_adapter_transport_fake_secret_canary_never_persisted'],27:['test_strict_args_never_accept_actor_endpoint_grant_or_partial_json'],
28:[],29:['test_import_adds_unselected_take_once_and_preserves_existing_approval'],30:['test_grant_mutation_revocation_context_and_price_block'],
31:['test_policy_precedes_execution_no_fallback_or_metadata_activation'],32:['test_cancel_timeout_race_preserves_latest_result','test_cancel_contract_retains_unconfirmed_cost_after_submit'],
33:['test_wrong_role_unknown_and_stale_are_atomic'],34:['test_grant_rights_media_and_price_rechecked_before_submit'],
35:['test_permission_denial_and_invalid_video_never_register_or_resubmit'],36:[],37:['test_policy_precedes_execution_no_fallback_or_metadata_activation'],
38:['test_three_protocols_preserve_call_link_and_do_not_execute','test_handoff_omits_reasoning_provider_ids_and_foreign_jobs']}
blocks={13:'7초 생성/편집/끝 프레임/박자 capability 전체 계약 미구현·미검증.',28:'생성 오디오 별도 트랙 보존 경로 미구현. 현재 Kling 시험은 무음이며 로컬 원곡 합성만 검증.',
36:'3 chat × 2 image × 2 video 실제 12조합 미실행; 공급자 선택/계정/개별 실행 승인 필요.',
17:'채팅 시험 원장과 미디어 원장은 분리됨. 전체 제품 공통 예산 및 부모-자식 통합은 미완료.',
20:'기존 embedding 필드 불변 fixture만 확인. 실제 검색/재임베딩 기반시설 미검증.',
33:'지원 종료 catalog 차단의 부분 계약만 있음. 실제 종료 모델 프로젝트 전체 재열람 여정 미검증.',
34:'로컬 grant/자료 권리 회수 fixture 검증. 실제 키 회전·BYOK 계정 전환 미실행.',
31:'silent fallback 차단만 검증. 평가된 자동 대체 실행 미구현.',
37:'정적 선택/입력 고정 부분 검증. 자동 라우팅·alias revision 제품 기능 미구현.'}
stage=Path((OUT.parent/'stage-path.txt').read_text().strip())
log=(OUT.parent/'full-regression-final.log').read_text()
selectors={}
for p in (stage/'tests').glob('test_*.py'):
    for node in ast.walk(ast.parse(p.read_text())):
        if isinstance(node,ast.FunctionDef) and node.name.startswith('test_'):
            selectors[node.name]=str(p.relative_to(stage))+':'+str(node.lineno)
for num,names in mapping.items():
    for name in names:assert name in selectors and re.search(re.escape(name)+r' .*? \.\.\. ok',log),name
evidence_paths={
 'local':'docs/qa/benchmark-provider-correction-20261025/full-regression-final.log',
 'claude':'docs/qa/claude-chat-ui-live-20261025/REPORT-ko.md',
 'receipt':'docs/qa/claude-receipt-recheck-20261025/REPORT-ko.md',
 'intent':'docs/qa/independent-intent-alignment-audit-20261025/REPORT.md',
 'contract':'docs/qa/independent-contract-final-recheck-20261025/REPORT.md',
 'bridge':'docs/qa/independent-action-bridge-recheck-20261025/REPORT.md',
 'rights':'docs/qa/independent-next-functional-recheck-20261025/REPORT.md',
}
codepaths={n:set() for n in range(1,39)}
for n,names in mapping.items():
    for name in names:codepaths[n].add(selectors[name].split(':')[0])
catalog=dict(document_id='SPEC-MS-001',source_sha256=sha(source.read_bytes()),source_declared_status='설계됨',requirements=reqs,tests=tests,sources=sources,
 scope='Document/requirement lineage, not the runtime product IP ontology.')
coverage=[]
for i,t in enumerate(tests,1):
    coverage.append(dict(id=t['id'],designed=True,implementation_status='partial' if mapping[i] else 'not_verified',
      acceptance_status='not_fully_verified',execution_scope='not_executed',execution_status='not_run',
      local_subset={'evidence_class':'fake_or_local_contract','status':'passed' if mapping[i] else 'not_run','selectors':[selectors[x]+' '+x for x in mapping[i]],'evidence':'local'},
      live_subset={'evidence_class':'actual_Claude_synthetic','status':'passed_subset' if i in (3,19,35,38) else 'not_run','evidence':['claude','receipt'] if i in (3,19,35,38) else [],'limitation':'One approved synthetic Claude path; fake media boundary, not cross-provider media acceptance.'},
      remaining=blocks.get(i,'로컬/fixture 부분 검증이다. 전체 MS-AT 원문 조건, 실제 계정·공급자·다중사용자 경계는 별도 검증 필요.')))
coverage_by={x['id']:x for x in coverage}
decision='''# Runway 역할 정정 — 2026-10-25\n\n사용자 최신 지시(부모가 전달한 trusted transcript, 13:56 UTC):\n> Runway는 예시이지 연결용 코드는 아니잖아 경쟁사이자 우리가 벤치마킹해야할 플랫폼인거지\n\n이 지시가 SPEC-MS-001 §1.3의 Runway 예시를 실제 연결 대상으로 확대했던 구현 해석에 우선한다. 원문 자체는 역사 자료로 보존한다. 독립 세 모델 슬롯 및 공통 제작 도구 구조는 유지하며 Runway의 catalog/선택/실행 연결만 제외한다. Runway의 실제 인증/유료 생성은 수행하지 않았다. 향후 image provider는 별도 선택 전까지 미선택이다. fal image 후보에 대한 공식 자료가 있다는 사실은 채택/활성화 승인과 다르다.\n\nprivate 1시간은 승인된 fal 시험 범위, Anthropic $50는 synthetic 개발 시험 원장 범위로 유지한다. 이 Decision은 문서/요구 계보용이며 고객 IP canon/승인 데이터를 바꾸지 않는다.\n'''
for kit in KITS:
    dest=kit/'docs/modules/spec-ms-001/20261025';dest.mkdir(parents=True,exist_ok=True)
    def write_once(path,data):
        if path.exists():assert path.read_bytes()==data,str(path)
        else:path.write_bytes(data)
    write_once(dest/'07_Chat_Directed_Multimodel_Production_Spec.md',source.read_bytes())
    write_once(dest/'catalog.json',json.dumps(catalog,ensure_ascii=False,indent=2).encode())
    write_once(dest/'coverage.json',json.dumps(coverage,ensure_ascii=False,indent=2).encode())
    write_once(dest/'runway-role-decision.md',decision.encode())
    for key,p in evidence_paths.items():write_once(dest/(key+Path(p).suffix),(ROOT/p).read_bytes())
    ns='MS20261025';objects=[]
    def record(key,kind,title,**kw):
        o=kb.record(ns+':'+key,kind,title,canonical_key=kind+':'+key,namespace=ns,aliases=kw.pop('aliases',[key]),tasks=['product','technical','validation'],**kw);objects.append(o);return o
    def doc(key,file,title):return record(key,'Document',title,file=str((dest/file).relative_to(kit)),sha256=sha((dest/file).read_bytes()))
    module=doc('SPEC-MS-001',source.name,'SPEC-MS-001 채팅 지시 기반 멀티모델 제작 확장 명세')
    module.update(summary='28 MS-FR / 38 MS-AT 설계 등록; 기능 통과·모델 활성화와 별개.',implementation_status='partial',subject_scope='product_multimodel_module',source_origin='User supplied local file; original preserved',source_original_sha256=catalog['source_sha256'])
    cat=doc('MS-CATALOG-20261025','catalog.json','원문 ID·문구·행 번호 추출 28요구/38시험/21출처')
    cov=doc('MS-COVERAGE-20261025','coverage.json','부분 구현·fake/local·실제 Claude 증거 및 남은 전체 수용 기준')
    decdoc=doc('MS-INTENT-20261025','runway-role-decision.md','최신 사용자 Runway 해석 정정')
    evidence={k:doc('MS-EVIDENCE-'+k,k+Path(p).suffix,'고정 근거: '+p) for k,p in evidence_paths.items()}
    for s in sources:
        record(s['id'],'Source',s['title'],citation_id=s['id'],url=s['url'],source_checked_at='2026-10-25',
          source_checked_at_basis='Date declared by SPEC-MS-001 §16 author, not independently revisited by this registration',
          source_observation_scope='Imported official-document citation; no current access, integration or quality proof',verification_level='source_documented',
          locator={'document_id':cat['id'],'json_pointer':'/sources/'+str(sources.index(s))},payload_sha256=kb.digest(kb.json_bytes(s)),
          links=[{'type':'derived_from','target':module['id']}],provider_role='benchmark_only' if s['id'] in ('MS-S09','MS-S10') else 'source_example_not_activation')
    correction=record('DEC-MS-RUNWAY-ROLE-20261025','Decision','Runway는 경쟁 벤치마크이며 연결 공급자가 아니다',decision_state='accepted',verification_level='source_documented',
      summary='최신 사용자 지시가 이전 구현 해석에 우선. 원문/과거 기록은 보존. 모델 아키텍처 자체는 유지.',
      supersedes_interpretation='Earlier implementation promoted the Runway example to provider catalog/adapter; historical specification is not overwritten.',
      links=[{'type':'derived_from','target':decdoc['id']},{'type':'supported_by','target':evidence['intent']['id']},{'type':'references','target':module['id']}])
    module['links']=[{'type':'references','target':correction['id']}]
    legacy={'FR-043':['01','03','04','08'],'FR-044':['06','18'],'FR-053':['17'],'FR-077':['21','25']}
    for i,r in enumerate(reqs):
        item=record(r['id'],'Requirement',r['title'],priority=r['priority'],subject_scope='product_multimodel',source_declared_status='designed',
          implementation_status='partial',acceptance_status='not_fully_verified',verification_level='unverified',
          locator={'document_id':cat['id'],'json_pointer':'/requirements/'+str(i)},payload_sha256=kb.digest(kb.json_bytes(r)),
          coverage_tests=r['tests'],links=[{'type':'derived_from','target':module['id']},{'type':'references','target':cov['id']}])
        for old,ids in legacy.items():
            if r['id'][-2:] in ids:item['links'].append({'type':'depends_on','target':'SPEC2:'+old})
        if r['id'] in ('MS-FR-01','MS-FR-25'):item['links'].append({'type':'depends_on','target':correction['id']})
    for i,t in enumerate(tests):
        c=coverage_by[t['id']]
        record(t['id'],'Test',t['trigger'],summary=t['expected'],source_declared_status='designed',verification_level='unverified',
          execution_scope='not_executed',execution_status='not_run',acceptance_status='not_fully_verified',
          aliases=[t['id'],'MS-AT-'+t['id'][-2:]],coverage=c,
          locator={'document_id':cat['id'],'json_pointer':'/tests/'+str(i)},payload_sha256=kb.digest(kb.json_bytes(t)),
          links=[{'type':'derived_from','target':module['id']},{'type':'references','target':cov['id']},{'type':'references','target':evidence['local']['id']}]+
                [{'type':'verifies','target':ns+':'+r['id']} for r in reqs if t['id'] in r['tests']]+
                ([{'type':'references','target':evidence['receipt']['id']}] if i+1 in (3,19,35,38) else []))
    record('MS-LOCAL-REGRESSION-20261025','Test','275개 로컬 회귀 실행 — 전체 MS 수용시험과 별개',verification_level='unverified',execution_scope='local_product_fixture',execution_status='passed',evidence_document_id=evidence['local']['id'],summary='source snapshot 전체 unittest 275 pass. 실제 공급자 시험·전체 MS-AT pass 의미 없음.',links=[{'type':'references','target':cov['id']}])
    sidecar={'objects':objects,'note':'Additive registration; full MS acceptance tests remain not_run; local/live subsets explicitly separated.'}
    write_once(dest/'registration.patch.json',json.dumps(sidecar,ensure_ascii=False,indent=2).encode())
    print(json.dumps({'kit':str(kit.relative_to(ROOT)),'objects':len(objects),'requirements':len(reqs),'tests':len(tests),'source_sha256':catalog['source_sha256']},ensure_ascii=False))
