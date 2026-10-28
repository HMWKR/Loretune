import pathlib,json,hashlib,subprocess
out=pathlib.Path(__file__).resolve().parent
before=json.loads((out/'original-preservation-before.json').read_text())
original=hashlib.sha256(pathlib.Path(before['path']).read_bytes()).hexdigest()
assert original==before['sha256']==hashlib.sha256((out/'input/chair.glb').read_bytes()).hexdigest()
renderer=hashlib.sha256(pathlib.Path('scene_renderer.py').read_bytes()).hexdigest()
assert renderer==before['renderer_sha256']
c=json.loads((out/'preflight.json').read_text())['environment'];cid=json.loads((out/'container.json').read_text())['id']
p=subprocess.run(['docker','--host','unix://'+c['LORETUNE_3D_DOCKER_SOCKET'],'inspect',cid],capture_output=True,text=True,timeout=30)
assert p.returncode!=0 and 'no such object' in p.stderr.lower()
(out/'preservation-and-cleanup-check.json').write_text(json.dumps({'original_sha256':original,'copy_equal':True,'renderer_sha256':renderer,'renderer_unchanged':True,'container_absent':True,'inspect_exit':p.returncode,'stderr':p.stderr.strip(),'checker_recovery':'Initial case-sensitive No such object assertion failed on lowercase Docker message; corrected lowercase comparison. Render and cleanup had succeeded.'},indent=2))
settings=json.loads((out/'output/settings.json').read_text());cases=json.loads((out/'output/case-receipts.json').read_text());pixels=json.loads((out/'pixel-analysis.json').read_text());execution=json.loads((out/'execution.json').read_text());geo=json.loads((out/'geometry-source-check.json').read_text())
assert len(cases)==4 and len({x['geometry_sha256'] for x in cases})==1 and geo['exact_vertex_and_face_order_equal']
assert execution['state']['ExitCode']==0 and not execution['state']['OOMKilled']
for case in cases:
 for suffix in ['.png','.exr','-linear.npy']:assert (out/'output'/(case['case']+suffix)).stat().st_size>0
summary={}
for region in ['seat_interior','backrest_interior']:
 pairs=pixels['regions'][region]['comparisons'];summary[region]={'A_inverse_srgb_linear_Y_percent_change':pairs[1]['linear_Y_mean_percent_change'],'B_emission_linear_Y_percent_change':pairs[2]['linear_Y_mean_percent_change']}
summary['bridge_whole_frame_png_max_channel_difference']=pixels['regions']['whole_frame']['comparisons'][0]['png_channel_max_absolute_difference']
report={
 'status':'REPORTED',
 'task':'BENCH-COLOR-04 controlled native renders',
 'outcome':'네 조건의 실제 PNG·선형 EXR·float 버퍼를 확보했다. 색 전달함수 가정은 큰 차이를 만들었고, 재조명의 영향은 좌석과 등받이에서 방향이 달랐다. 모델 학습 출력의 색공간과 교정의 정답은 아직 미확인이다.',
 'methodology_sources':['../asset-color-diagnosis-20261028/report.json','Khronos glTF 2 COLOR_0 linear rule','현재 scene_renderer.py와 고정 설치본 Blender importer'],
 'cases':cases,
 'comparisons':{'A':'raw-float-pbr ↔ inverse-srgb-float-pbr: 동일 FLOAT_COLOR, inverse-sRGB 전달함수만 변경','B':'raw-float-pbr ↔ raw-float-emission: 원색·조명·표시 설정을 유지하고 표면 셰이더만 변경','bridge':'native-byte-pbr ↔ raw-float-pbr: 가져오기 BYTE_COLOR 양자화 영향을 별도로 확인'},
 'quantitative_summary':summary,
 'interpretation':'위 비율은 명시된 좌석·등받이 ROI의 동일 조건 민감도이다. 원본 입력과 결과의 차이에 대한 가산 가능한 원인 비율이나 전체 물체 품질 점수가 아니다.',
 'manual_visual_review':{'viewed':['output/raw-float-pbr.png','output/inverse-srgb-float-pbr.png','output/raw-float-emission.png'],'observation':'원색 PBR은 옅은 베이지색, inverse-sRGB는 더 어둡고 주황·갈색이며, 무조명도 같은 AgX에서 베이지색을 유지한다. 무조명 전환만으로 색 차이가 해소되지 않았다. 입력과 동일 구도 재현 품질 검증은 아니다.'},
 'actual_settings':settings,
 'geometry_source_check':geo,
 'verification':[
  {'scenario':'고정 실행 환경','invocation':'설치 트리와 바이너리 SHA 계산 + docker image inspect','observable':'모든 설정 pin과 일치','artifact':'preflight.json'},
  {'scenario':'실제 네 조건 렌더','invocation':'python3 .omo/evidence/asset-color-controlled-20261028/launch.py; container.json의 정확한 docker argv','observable':'컨테이너 exit0, OOM false, PNG4·EXR4·NPY4 존재','artifact':'execution.json / render.log / output/case-receipts.json'},
  {'scenario':'원본 기하 및 조건 간 불변','invocation':'원본 POSITION/index 해독 후 (x,-z,y) 축 변환과 순서 보존 SHA 대조','observable':'원본 및 네 조건의 정점·면 순서 해시 일치','artifact':'geometry-source-check.json'},
  {'scenario':'픽셀 비교','invocation':'기존 전용 Python3.11로 analyze.py 실행','observable':'exit0, 고정 ROI 및 전체 프레임 통계','artifact':'analysis.log / pixel-analysis.json'},
  {'scenario':'원본·제품 보존 및 종료','invocation':'원본 GLB/복사본/renderer SHA, 컨테이너 삭제 후 inspect','observable':'원본과 renderer 불변, 전용 컨테이너 없음','artifact':'preservation-and-cleanup-check.json / cleanup.json'}],
 'resources':{'container_wall_seconds':execution['wall_seconds'],'Blender_total_seconds':settings['time_total_seconds'],'Blender_process_peak_rss_bytes':settings['process_peak_rss_bytes'],'container_memory_limit_bytes':2147483648,'container_cpus':2,'wall_timeout_seconds':420,'evidence_bytes_before_report':sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),'network':'실제 컨테이너 설정 network=none 확인','container_peak_memory':'별도 측정하지 않음; 위 RSS는 Blender 프로세스 측정'},
 'failures_preserved':['analysis-attempt-1-rejected: 배경 차이 마스크가 거의 전체 화면을 선택해 대상 통계로 부적합. 결과를 보존하고 고정 ROI 분석으로 교체. 렌더 재실행 없음.','최종 컨테이너 부재 검사 문자열 대소문자 실패를 수정; 실제 렌더/정리 실패는 아님.'],
 'actual_tools_and_skills':{'skills':'같은 에이전트 세션에서 앞서 읽은 Karpathy·feature-verification 적용; 별도 가상 스킬 명령 실행 없음','tools':['exec_command','write_stdin','view_image'],'commands':['고정 docker create/start/inspect/rm','Blender --background --factory-startup --disable-autoexec --python /input/experiment.py','기존 전용 Python의 numpy/PIL 분석'],'exits':'render0, analysis0, owned container rm0'},
 'limits':['모델 학습 출력 색공간 미확인. 더 어두움·입력과 비슷해 보임은 올바른 교정의 증거가 아니다.','제품·문서·registry·context 수정, 새 모델 추론·다운로드·설치·공급자 호출 없음.','상용 Tripo 동등성 또는 플랫폼 전체 완료를 주장하지 않음.','480×270, 4 samples, 단일 seed. 노이즈 수렴·신뢰구간 미측정.','독립 진단 스크립트의 명시적 AgX·2 threads·FLOAT_COLOR·shader·EXR 설정은 제품과 차이를 가지며 settings.json에 기록.','ROI는 수동 선택한 내부 사각형이며 전체 물체 분할 또는 입력과 대응되는 영역이 아님.']}
(out/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
manifest={str(p.relative_to(out)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in out.rglob('*') if p.is_file() and p.name!='artifact-manifest.json'}
(out/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(summary,indent=2));print(json.dumps(report['resources'],indent=2));print('artifacts',len(manifest))
