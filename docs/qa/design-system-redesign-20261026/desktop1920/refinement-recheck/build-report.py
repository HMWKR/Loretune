from pathlib import Path
import json, hashlib, csv, io, re
from decimal import Decimal, ROUND_HALF_UP

root=Path('/Users/leesungmin/Desktop/Loretune')
base=root/'docs/qa/design-system-redesign-20261026'
out=base/'desktop1920/refinement-recheck'
old=base/'desktop1920/final-audit'
read=lambda p: json.loads(p.read_text())
start=read(out/'start.json'); end=read(out/'end.json')
score=read(old/'scorecard.json')
items={i['id']:i for a in score['axes'] for i in a['items']}
for i in items.values():
    i['previous_anchor']=i['anchor'];i['previous_earned']=i['earned']
    i['evidence_disposition']='retained_prior_direct_evidence; relevant code unchanged; not a new execution'
    i['prior_evidence']=i['evidence']
    i['evidence']=['../final-audit/'+s for s in i['evidence']]

def update(id,anchor,measurement,judgment,evidence,disposition='rechecked_current_actual_runtime'):
    i=items[id];i.update(anchor=anchor,earned=i['max']*anchor/4,status='assessed_sample',measurement=measurement,judgment=judgment,evidence=evidence,evidence_disposition=disposition)

update('A2',4,'기본·sequence·정밀 편집 문서 1080/1080px, timeline 하단1064px. 정밀 입력·버튼34개와 진단 summary1개를1920 및1280에서 Tab 이동, 중심 가림0.',
       '기존 bounded shell의 강점을 유지한다. 긴 rail/메모 스트레스는 이전 직접 증거를 유지하며 이번 새 실행으로 바꾸지 않는다. 상세는 내부 스크롤을 사용한다.',
       ['01-selected-1920.json','05-sequence-1920.json','06-expanded-sequence-1920.json','precision-keyboard.json','boundaries.json','../final-audit/long-panels.json'])
update('A4',3,'1920 실제 contain 영상: 기본718.07×403.91, sequence598.96×336.91, 정밀504.86×283.98px. 1280 정밀218.14×122.70px. 문서1080/900px.',
       '1920 정밀 영상의 면적은 이전334.12×187.95보다2.28배로 개선됐다. 하지만1280 정밀 영상은 이전291.03×163.70보다 면적 약44% 작다. 보조 viewport의 세부 미디어 판단 부담 때문에4가 아니다. 이 감점은A4에만 반영한다.',
       ['01-selected-1920.png','05-sequence-1920.png','06-expanded-sequence-1920.png','07-expanded-sequence-1280.png','geometry.json','boundaries.json'])
update('B1',4,'편집 선택01/Take1과 재생 장면02/Take1을 명시적으로 구분. sequence시각2.172/7초, 선택·승인·편집 project hash불변.',
       '정해진 장면 선택/sequence/비교 표본에서 대상 역할이 명확하고 모순이 없다. 재생이 편집 선택을 바꾸지 않는다. 이는 객체 문맥의 표본 평가이며 실제 사용자의 이해 시간을 측정한 것은 아니다.',
       ['05-sequence-1920.png','06-expanded-sequence-1920.png','02-keyboard-comparison-1920.png','end.json'])
items['B2']['judgment']='승인 완료에는 검토 수정, dirty에는 활성 저장/취소, 통제된 거절에는 수정 후 재저장, unknown에는 기존 저장 확인이 표시된다. 반려/미검토 inspector와 실제 비용 commit의 모든 변형은 이번 표본에 없으므로3을 유지한다.'
items['B2']['evidence']+=['13-controlled-rejection-ready-1920.png','14-controlled-unknown-ready-1920.png']
items['B2']['evidence_disposition']='retained plus controlled error samples'
update('B3',3,'일상 문구는 저장된 버전·승인 상태 중심. 자산 해시 검증 방식은 닫힌 검증 상세 안에서 checkVisibility=false, Enter로true. 테스트 미디어·모델 불가 이유·실행 승인 별도 안내 유지.',
       '기존 기본 노출 기술 설명 문제는 해소됐다. 진단을 삭제하지 않고 사용자가 필요할 때 열 수 있다. 계획 commit·공급자 오류 등 모든 경로의 진단 분리까지 실제 관찰하지 않았으므로 전 범위4를 선언하지 않는다. 모델 창의 공간 감점은D2에서만 다룬다.',
       ['diagnostic.json','controlled-errors.json','06-expanded-sequence-1920.png','11-model-selected-blocked-1920.png'])
items['C1']['judgment']='기존 선택 면/왼쪽 표식, focus 점선, 승인 기호의 역할을 유지한다. 이번에는 오류 면과 비활성 저장의 실제 픽셀도 확인했다. forced-colors와 모든 반려/실행 상태는 미검증이므로3을 유지한다.'
items['C1']['evidence']+=['13-controlled-rejection-ready-1920.png','14-controlled-unknown-ready-1920.png']
items['C2']['measurement']+=' 현재 오류#FFB49D/오류면#28201E도 opacity1 실제쌍으로9.325:1 확인.'
items['C2']['evidence']+=['controlled-error-clean-captures.json','contrast-addendum.csv']
items['C3']['judgment']='선택·승인·focus의 기존 비색상 단서를 유지하며 오류 문구/왼쪽 경계, unknown의 비활성 저장과 활성 조회를 추가로 확인했다. 모든 provider/권리/계획 오류의 비색상 단서는 표본 밖이므로3을 유지한다.'
items['C3']['evidence']+=['13-controlled-rejection-ready-1920.png','14-controlled-unknown-ready-1920.png']
update('D2',4,'미선택 모델창 외곽 높이559.09px; 실제 모델 미검증/차단 선택은657.09px, 합성 긴 이름은683.28px. 긴 이름67.20px 줄바꿈, 가로overflow0.',
       '기존 미선택 사실을 세 줄로 반복하던 공간 문제가 해결됐다. 관련 label/select/현재 이유와 상세가 한 그룹이고, 긴 이름은 필요한 때만 전체를 보여준다. 이번 표본에서 간격·정렬의 의미 있는 잔여는 재현되지 않았다. 타입 굵기/아이콘 미감은D1/D4에서 별도 평가한다.',
       ['04-model-empty-1920.png','11-model-selected-blocked-1920.png','12-model-long-unavailable-1920.png','model-states.json'])
items['F1']['measurement']='이전 dirty→단계 전환→취소를 보존. 이번 controlled unknown에서 장면02 초안/오류 오염0,01복귀 초안 보존. receipt 응답 대기 중 새 문자를 입력한 뒤 committed 합성 응답에도 새 초안 유지.'
items['F1']['judgment']='새 비동기/장면 전환 표본은 안정적이다. 프로젝트 간 전환·브라우저 종료 후 미확정 요청 복구·실제 서버 저장 지연은 이번 독립 시험에서 실행하지 않았다. 전체 상태전이 최고앵커가 아니라3을 유지한다.'
items['F1']['evidence']=['controlled-errors.json','10-newer-draft-preserved-1920.png','keyboard-initial.json','end.json']
items['F1']['evidence_disposition']='new controlled browser evidence plus retained old cancel evidence'
update('F2',4,'reload한 초기BODY에서 Tab/Enter/Arrow/문자입력/Escape만으로 미리보기·비교·닫기·검토 수정·초안 취소·출처·모델창 여정 완료. 52관측/8목표. 정밀 구간35Tab 모두 가시.',
       '고정 H3에 정의된 핵심 여정을 처음부터 키보드만으로 완료하고 비교/모델/취소의 focus 복귀를 확인했다. 정밀 폼 구간만 summary 명시focus 진입을 사용했으며 이를 초기 여정과 구분한다. 모든 native 영상 메뉴나 스크린리더 검증은 아니다.',
       ['keyboard-initial.json','precision-keyboard.json','boundaries.json','03-keyboard-dirty-1920.png'])
update('F3',3,'2회 실행을 합쳐 변경POST4건·기존조회GET4건 모두 브라우저에서 가로챔. 400거절=입력 유지/다시 저장 가능. unknown=새 저장 disabled/기존 조회. 조회 응답 후 새 초안 보존. DB 전달0.',
       '실패 영향과 다음 행동을 실제 UI에서 확인했으므로U에서 평가 가능으로 변경한다. 다만unknown 안내의 “연결이 돌아오면”은 정상 연결의404unknown에도 원인을 네트워크로 좁혀 말한다. “잠시 후 기존 저장 확인”처럼 확인된 사실 중심 표현이 더 정확하므로3. 실제 서버 장애/청구/DB commit은 증명하지 않는다.',
       ['controlled-errors.json','controlled-error-clean-captures.json','13-controlled-rejection-ready-1920.png','14-controlled-unknown-ready-1920.png'],
       'new controlled browser response test; not real server fault')
items['G2']['measurement']='현재 앱200% 본문28px, flow, 문서2505px,가로1920px/넘침0; 눈금 겹침0. 1280 정밀 문서900px와35Tab 접근 보존. 이전150%표본은 역사적 유지.'
items['G2']['judgment']='큰 글자에서는 의도적으로 페이지 reflow/스크롤을 허용한다. 이는 기본1920 무스크롤 요구와 충돌하지 않는다. 실제 browser200/400%zoom·screenreader·사용자 text-spacing은 미검증이며 앱배율로 대체하지 않는다.'
items['G2']['evidence']=['15-app-text200-1920.png','boundaries.json','07-expanded-sequence-1280.json','../final-audit/09-app150-1920.png']
items['G2']['evidence_disposition']='current app200 and1280; retained previous app150'
items['G1']['measurement']='동일 primitive/semantic 역할과 컴포넌트 토큰 유지. 현재 CSS '+str(len((root/'studio.css').read_text().splitlines()))+'행; 이번 변경은 기존 bounded rule 조정 및 model/transport 규칙 추가.'
items['G1']['judgment']='토큰 역할은 유지되고 current computed 값에서 충돌은 재현되지 않았다. selector/조건별 override 추적 부담은 남는다. 중복이 곧 기능 결함이라는 뜻은 아니며 코드 축약을 새 필수 목표로 추가하지 않는다.'

for a in score['axes']:
    a['coverage_max']=sum(i['max'] for i in a['items'] if i['anchor'] is not None)
    a['earned_on_assessed']=sum(i['earned'] or 0 for i in a['items'])
score.update(status='bounded_V1_V4_independent_recheck_complete',at_utc=end['utc'],source={k:v['sha256'] for k,v in end['served'].items()},coverage_max_points=sum(a['coverage_max'] for a in score['axes']),earned_on_assessed=sum(a['earned_on_assessed'] for a in score['axes']))
score['source']['app.py']=hashlib.sha256((root/'app.py').read_bytes()).hexdigest()
score['overall_score']=score['earned_on_assessed']
score['display_score']=str(Decimal(str(score['overall_score'])).quantize(Decimal('.1'),rounding=ROUND_HALF_UP))
score['coverage_definition']='26/26 items assessable via bounded current/retained evidence, not all states tested or product readiness'
score['prior_scorecard']='../final-audit/scorecard.json'
score['gates']['H1_media_seek_sync']['reason']='미디어 수명 로직은 표시 문자열 외 변경 없음. 기존 DM01–03 코드 재검증은 유지한다. 현재 sequence/비교/ready 상태는 관찰했으나 loading seek·stale event·이전 audio loop의 모든 반례를 이번 실제브라우저에서 재실행하지 않았다. 닫힌 결함의 재개가 아니다.'
score['gates']['H2_approval_cost_version']['reason']='현재 프로젝트 해시 불변, 모델 선택≠실행 승인 표시, controlled unknown/복구 분기를 확인했다. 실제 비용/실행 승인commit·실청구·실DB저장은 수행하지 않아 전체gate는U다.'
score['gates']['H3_keyboard']={'status':'PASS','scope':'고정 rubric의 정의된 핵심 keyboard 여정 및 표본 정밀 컨트롤','evidence':['keyboard-initial.json','precision-keyboard.json','boundaries.json'],'reason':'초기BODY부터 정상Tab으로 미리보기/비교/Escape/검토수정/초안취소/출처와 모델창을 완료. nativevideo 모든 메뉴/스크린리더까지 확장하지 않음.'}
score['gates']['H4_contrast']['evidence']=['../final-audit/contrast.csv','../final-audit/styles-states.json','controlled-error-clean-captures.json','contrast-addendum.csv']
score['gates']['H4_contrast']['reason']='기존 실제 필수쌍을 유지하고 오류#FFB49D/#28201E도 실제 opacity1배경쌍9.325:1로 추가 확인. 전체WCAG/nativeoverlay 인증 아님.'
assert score['overall_score']==81 and score['coverage_max_points']==100
(out/'scorecard.json').write_text(json.dumps(score,ensure_ascii=False,indent=2)+'\n')

geometry=[]
for n in ['01-selected-1920','05-sequence-1920','06-expanded-sequence-1920','07-expanded-sequence-1280']:
    d=read(out/(n+'.json'));p=d['areas']['#preview'];m=d['media'][0];w,h=m['intrinsic'];ratio=w/h
    # 1px border on each side: actual contain stage is the inner box.
    ph=p['height']-2;pw=p['width']-2;mh=min(ph,pw/ratio);mw=mh*ratio
    geometry.append({'state':n,'utc':d['utc'],'viewport':d['viewport'],'document':d['document'],'stage_width':p['width'],'stage_height':p['height'],'actual_media_width':mw,'actual_media_height':mh,'viewport_percent':100*mw*mh/(d['viewport']['width']*d['viewport']['height']),'ready':m['ready'],'timeline_bottom':d['areas']['.timeline']['bottom']})
(out/'geometry.json').write_text(json.dumps(geometry,ensure_ascii=False,indent=2)+'\n')
def lum(h):
    a=[int(h[i:i+2],16)/255 for i in (1,3,5)];a=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in a];return sum(x*y for x,y in zip(a,[.2126,.7152,.0722]))
contrast=(lum('#FFB49D')+.05)/(lum('#28201E')+.05)
(out/'contrast-addendum.csv').write_text('role,foreground,background,opacity,contrast,evidence\nerror,#FFB49D,#28201E,1,'+f'{contrast:.6f}'+',controlled-error-clean-captures.json\n')

def evlink(x):
    return f'[{x}]({x})' if (out/x).exists() else x
lines=[]
for a in score['axes']:
    for i in a['items']:
        lines.append(f"| {i['id']} {i['name']} | {i['max']} | {i['previous_anchor'] if i['previous_anchor'] is not None else 'U'} → {i['anchor']} | {i['earned']:g} | {i['measurement']} | {i['judgment']} | "+', '.join(evlink(x) for x in i['evidence'][:2])+' |')
axes='\n'.join(f"| {a['id']} {a['name']} | {a['max']} | {a['earned_on_assessed']:g} |" for a in score['axes'])
geo='\n'.join(f"| {x['state']} | {x['actual_media_width']:.2f}×{x['actual_media_height']:.2f}px | {x['viewport_percent']:.2f}% | {x['document']['scrollHeight']} / {x['viewport']['height']} | {x['timeline_bottom']:.0f}px |" for x in geometry)
report=f'''# Loretune V1–V4 독립 디자인 재검토

2026-10-26 · 실제 CSS viewport 1920×1080 우선 · 1280×900 보조 · 종료 {end['utc']}

## 결과

**고정된 7축·26항목 기준 81.0/100점입니다.** 26항목 모두 평가 가능한 표본을 확보해 배점 커버리지는100/100입니다. 이는 모든 상태를 시험했다는 뜻이 아닙니다. 점수는 아래 고정표에 대한 전문가 판단이며 객관적 경쟁사 순위·제품 완성률·90점 달성·접근성 인증이 아닙니다. 이전5축 점수와 비교하지 않습니다.

이번 직접 표본에서 새 사용 차단 결함은 재현되지 않았습니다. 기본1920 작업 공간의 페이지 높이1080px를 유지하면서 정밀 편집·자막 동시 화면의 실제 영상이334×188에서505×284px로 커졌습니다. 편집 선택과 재생 장면의 역할, 모델 선택의 현재 이유, 저장 거절과 미확정 결과의 다음 행동이 명확해졌습니다.

**필수 gate: H3 키보드 PASS, H4 측정 대비 표본 PASS. H1 미디어 경계 전체와 H2 실제 비용·승인 실행 구간은 UNVERIFIED입니다.** 따라서 전체수용/ready를 선언하지 않습니다. 미검증을 실패로 계산하지도 않습니다.

## 같은 평가표의 이력과 점수 변화

평가표 [v1.0](../RUBRIC-v1-ko.md)와 [무스크롤 추가 합의v1.1](../RUBRIC-v1.1-ADDENDUM-ko.md)의 가중치·앵커를 유지했습니다. 항목별0–4 정수 앵커×배점/4로 계산하며 결과를 보고 새 기준을 만들지 않았습니다. 옛 [74.25점/평가98점 보고서](../final-audit/REPORT-ko.md)와 원본scorecard는 수정하지 않았습니다.

| 이력 | 확인 가능한 배점 | 획득점 | 의미 |
|---|---:|---:|---|
| 이전 shell202ea641 |98/100|74.25 (표시74.3)|F3=U, 전체점수 보류.100점으로 환산하지 않음|
| 현재 refinement5fcc2cca |100/100|81.00 (표시81.0)|허용된 통제 오류 시험으로F3도 평가 가능. 전체 상태 커버리지는 아님|

차이6.75점 중 시각·문구 개선은 A4+1, B1+1.25, B3+1.25, D2+1로 **4.5점**입니다. F2+0.75는 키보드 증거 보강이며, F3+1.5는 기존 미검증 범위를 새로 평가한 점수입니다. 이6.75점을 모두 디자인 코드 개선률로 주장하지 않습니다.

| 축 | 배점 | 현재 획득 |
|---|---:|---:|
{axes}
| **합계** |**100**|**81.0**|

## V1–V4 실제 재검토와 시각 판단

| 항목 | 원인·기존 부담 | 현재 직접 측정/관찰 | 판단·잔여 |
|---|---|---|---|
|V1 / A4|정밀 폼과sequence·자막이 높이를 경쟁해 실제 영상188px|1920 영상283.98px높이, 면적2.28배. 문서1080px.34controls+진단summary1의Tab중심 가림0|개선됨.1280 정밀 영상은122.70px높이로 작아져 보조화면 절충이 남음. 숨긴 조작으로 만든 개선은 아님|
|V2 / B3|사용자 편집 상세에 자산hash검사 설명|닫힌 ‘검증 상세’ 안에 원문 보존. checkVisibility=false→Enter후true|기본 기술 설명 노출 해소. 모델·승인·테스트 표시와 오류는 유지. 모든 계획/공급자 경로를 재감사한 것은 아님|
|V3 / D2|모델 미선택 사실의 반복과 큰 간격|미선택 창 외곽559.09px; 선택불가 이유를 역할별 한 줄. 긴이름 전체줄바꿈/가로overflow0|현재 표본의 그룹·정렬 문제 해소. 전체 모델명은 길어야 할 때만 두 번째 영역에 제공|
|V4 / B1|편집 대상01과 재생 대상02를 사용자가 추론|‘편집 선택 · Take1’, ‘재생 장면:02…’ 명시. 선택·승인·trim 불변|현재 표본의 역할 혼동을 해소. 실제 사람의 인지시간 측정은 아님|

### 동일 과업 geometry

모든 값은 브라우저 내용영역 CSS px입니다.16:9 실제 영상 면적은 요소의전체폭이 아니라 intrinsic320×180과contain 내부영역으로 계산했고 저장 픽셀과 대조했습니다. 영상은 로컬 합성 패턴이며 실모델 생성물이 아닙니다. 테스트 화질·아름다움은 감점하지 않았습니다. 검정letterbox는 비율보존의 정상 영역입니다.

| 상태 | 실제영상 W×H | viewport 면적 | 문서/viewport높이 | timeline하단 |
|---|---:|---:|---:|---:|
{geo}

1920 정밀 편집에서 영상은 약6.91%의 viewport면적을 차지합니다(이전3.03%). 이것만으로 미감이나 작업 성공률을 추론하지 않습니다.1280의 영상 면적은 이전 동일 정밀 상태보다 약44% 작습니다. [07화면](07-expanded-sequence-1280.png)은 내부 폼이 아래로 스크롤된 상태이며 마지막 버튼 일부가 처음 프레임에 보이지 않습니다. 후속Tab35개가 모두 화면 안으로 들어오는 것을 [boundaries.json](boundaries.json)으로 확인했으므로 접근 불가능한 clipping으로 판정하지 않습니다.

## 색상·타입·형태·상태

기존 palette와token 역할을 유지합니다: canvas#101010, panel#1B1B1B, raised#242424, hover#303030; 강한문자#F4F4F2, 본문#DEDEDB, 보조#BDBDBB; 필수경계#858585, 장식선#383838. 선택면#2A2A28+왼쪽표식#D8D8D2, focus#E4DDBE 2px점선+2pxoffset, 승인은기호+텍스트로 구분합니다. 원본 computed/tokens는 이전 [tokens.csv](../final-audit/tokens.csv)와 현재 캡처JSON에 있습니다. 경쟁사의 내부HEX를 추정해 비교하지 않습니다.

기존 실제 대비 표본(본문/패널12.777:1, 보조/패널9.154:1, 제어경계/hover3.577:1, focus/hover9.669:1)을 유지합니다. 이번에는 오류의 실제전경#FFB49D·배경#28201E·조상opacity1을 확인했고 **{contrast:.3f}:1**입니다. 이전 source-only 오류쌍을 이번에는M관찰로 보강했습니다. nativevideo 반투명overlay 전체나 모든 상태를 인증한 것은 아닙니다.

제목20px/600/28px, 본문14px/400/23.8px, 메타12px와tabular시간의 읽기 층위를 유지합니다.4/8/12/16/24/32px 간격과control6/panel8/dialog12px의 형태 역할도 유지합니다. 모델 폼은 select와이유·상세를 같은 그룹으로 묶고 미선택의 불필요한 이름 행을 제거했습니다. 긴 이름의 전체문구는3줄67.20px로 읽히고, 폭을 넘어가거나 가로스크롤을 만들지 않았습니다. 글자와native아이콘의 광학무게가 완전히 같지는 않으며D4의 기존 잔여로 유지합니다.

## 직접 수행한 흐름·통제 시험과 커버리지

| 상태/검증 | 증거 등급·결과 | 하지 않은 것 |
|---|---|---|
|기본/sequence/정밀1920|O/M:01,05,06. readyState4,문서1080. 편집01/재생02|장시간동기·실음악청취 없음|
|초기 keyboard-only|O/M:BODY에서Tab/Enter/Arrow/입력/Escape,52관측/8목표. 비교/모델닫기·초안취소의focus복귀|nativevideo 모든 메뉴/스크린리더 전체 없음|
|정밀 폼1920/1280|O/M:34개input/button+진단summary.35Tab 중심가림0|이 구간은summary명시focus 진입. 초기여정과 구분|
|모델 미선택/미검증/차단|O/M:실제catalog선택을 저장 없이 표시,Escape복귀|모델 활성화/저장/호출 없음|
|긴이름 unavailable|O/M:임시in-memory catalog,전체이름·줄바꿈·overflow0,원상복원|실제등록모델/서비스상태 아님|
|400저장거절|O/M controlled:입력 보존,구체적안내,다시저장활성|실제서버400장애 아님|
|응답유실→404unknown|O/M controlled:새저장disabled,기존조회만,입력보존|새POST전달/실청구/DB저장 없음|
|장면전환/새초안 race|O/M controlled:02에01초안없음,01복귀보존;응답 대기 중 추가한새문자 유지|프로젝트간/앱재시작 후 복구는 이번 미실행|
|앱글자200%|O/M:본문28px,flow,문서2505px,가로넘침0,눈금겹침0|실제브라우저zoom200/400% 아님|
|긴panel·혼합aspect·reduced-motion|이전 독립O/M 증거를 관련코드불변으로유지|이번에 모두다시실행한것으로표시하지않음|
|회귀346/문법6·DM01–03|S:구현/독립코드팀 근거|코드테스트 수를 시각점수로 사용하지 않음|
|미실행|실제browserzoom,screenreader,forced-colors 전체,실제고객시험,livebilling,모든생성오류,모바일새QA|미검증을실패나성공으로대체하지않음|

통제 오류 시험은 두 번 수행했습니다. 첫 실행은400→unknown→장면전환→응답대기중새초안→합성committed분기를 검증했습니다. 두 번째는 첫08/09화면의native영상로딩spinner를 제외하기 위해readyState4를 기다린 깨끗한 픽셀을 확보한 것입니다. **합계 변경POST4건·조회GET4건은 모두 가로챘고 전달0,예상외변경0**입니다. 마지막committed는 클라이언트분기를 정리하기 위한 합성응답이지 실제저장증거가 아닙니다. 임시초안은취소,fetch와catalog는복원했습니다.08/09/10은해당검토상태만의증거로보존하며ready영상전달용에는13/14를사용합니다.

처음테스트harness가shots를배열로가정해wait가timeout된1건은실제객체구조를확인한뒤계수검증으로수정했습니다. 이는제품실패나저장실패가아니며점수에포함하지않습니다. 실행도구의접근거부는없었습니다.

## 필수 gate

| Gate | 상태 | 근거와 범위 |
|---|---|---|
|H1 media/seek/sync|UNVERIFIED|현재재생/정지/sequence와기존비교는확인.로딩중seek/staleevent/이전audio반례전체는이번브라우저미실행. DM01–03코드종료는유지|
|H2 승인·비용·버전|UNVERIFIED|비교/초안/모델창 전후project불변과controlled복구확인. 실제비용·승인commit/DB저장/청구는하지않음|
|H3 핵심keyboard|PASS(정의된표본)|초기정상Tab부터고정핵심여정완주. focus가시·닫기/취소복귀확인|
|H4 필수대비|PASS(측정표본)|기존쌍+실제오류9.325:1. 전체WCAG/nativeoverlay인증아님|

## 26항목별 점수·유지 강점·감점 이유

표의숫자는0–4앵커입니다. 이전U는0점이아닙니다. 동일결함을여러축에서중복감점하지않습니다. 이전근거를유지한항목은 [scorecard.json](scorecard.json)의evidence_disposition에명시했습니다.

| 항목 | 배점 | 앵커 이전→현재 | 획득 | 실제값/근거 | 판단·남은한계 | 대표파일 |
|---|---:|---:|---:|---|---|---|
'''+ '\n'.join(lines)+f'''

## 남은 실행 가능한 사항 — 새 목표 추가 아님

| 우선 | 원인→영향 | 현재근거 | 후속판단/재검증 | 점수반영 |
|---|---|---|---|---|
|P2 절충|작은viewport에서도정밀폼최소높이를유지→실영상세부판단공간감소|1280 영상218×123,문서900,Tab35접근성유지|1920배분을되돌리기보다1280조건에서폼/transport높이배분을검토. 같은작품·시간·자막과control접근유지로검증. 현재앱수정없음|A4만|
|P3 문구|unknown원인이확인되지않았는데연결복구를전제→기다려야할원인오해가능|통제404unknown에서도‘연결이돌아오면’|‘아직저장여부를확인하지못했습니다. 잠시후기존저장확인으로조회하세요’처럼확인된사실/행동중심. 입력보존/재제출차단유지|F3만|
|기존잔여|긴메모의세로읽기,작은메타·native/glyph광학차이,조건별CSS추적|이전직접자료+현재변경범위|기존표본내작업부담. 신규아이콘세트/자동요약/재설계등을이번완료의새조건으로추가하지않음|A3/D1/D4/G1각독립역할|

승인 완료에 밝은CTA가 없는 것은 결함이 아닙니다. 테스트 패턴의 화질, portraitletterbox,접근 가능한 내부scroll을미감감점으로잘못사용하지않습니다.1280작은영상과위문구외에새중대결함을만들어내지않습니다.

## 참고의 역할과 방법론 추적

| 사용자과업 | 참고근거 | 설계이유 | 구현/검증 |
|---|---|---|---|
|미디어를보며정밀시간편집|[Descript공식timeline](https://help.descript.com/timeline/timeline-overview),[ReferoDescript](https://refero.design/pages/7aaa7dcf-f7e2-4a12-aedf-10ce0576ba87)|분할작업맥락과시간좌표를유지;Loretune의px배분은우리판단|studio.css bounded높이·transport,V1,A4/Tab검증|
|선택대상과재생대상인지|[NN/g recognition](https://www.nngroup.com/articles/recognition-and-recall/),[Frame.io참조](https://refero.design/pages/afd4cddd-a493-47c7-9f65-da6b74819871)|대상/버전단서를보이게해기억부담완화|index.html상단,studio-media.js표시문구,V4/B1|
|모델선택·위험판단|[progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/),[PAIR mental models](https://pair.withgoogle.com/guidebook-v2/chapter/mental-models/)|선택/실행승인구분;기술진단은필요시열기|drawModelSettings/modelChoiceHint,closeddiagnostic,V2/V3|
|저장불확실성에서복구|[PAIR errors](https://pair.withgoogle.com/guidebook-v2/chapter/errors-failing/)|확정거절≠unknown,입력보존,같은요청조회|reviewSaveCheck/scopeddraft,F1/F3controlled시험|
|확대/키보드로작업|[W3C resize text](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html)|글자축소나hidden으로맞추지않고필요시reflow|앱200%·35Tab·H3,실제zoom은U|

경쟁사참고는원본뷰포트/시점/과업이다른captured이미지와공식자료입니다.1920라이브동일조건비교나경쟁사점수는만들지않았습니다. Runwaycapturedhome은조용한prompt shell만참고하며timeline증거로쓰지않습니다. NeuralFrames는공식tutorial Track/Storyboard이미지이며직접경쟁사계정관찰이아닙니다. Blender직접읽기402제약은이전기록그대로이며이번성공으로바꾸지않습니다. 방법론은 [적합성표](../../METHODOLOGY-FIT-MATRIX-ko.md)의채택/조건부/제외를유지합니다.

## 버전·보존·인계

| 소스 | SHA256 |
|---|---|
'''+ '\n'.join(f"|{k}|`{v}`|" for k,v in score['source'].items())+f'''

시작·종료HTTP200제공본과로컬소스해시가동일합니다. 작품JSON해시도 `{end['project_sha256']}`로불변입니다. 새서버시작/재시작·앱/DB편집·키열람·유료호출·경쟁사계정작업은하지않았습니다. 앱배율100%,pendingfalse,모든임시fetch/catalog복원후별도Ego검증공간32를종료했습니다.

변경문서는새 [재검토scorecard](scorecard.json), [geometry](geometry.json), [상태/오류증거](controlled-errors.json),현재보고서이며이전감사원본은그대로입니다. 사용자요약과방법론표는기존Library정체성으로갱신합니다. 화면전달은비민감합성자료만이며Library결과는별도receipt에기록합니다.
'''
delivery=read(out/'library-delivery.json')
image_rows='\n'.join('| '+Path(x['local_path']).name+' | `'+x['library_file_id']+'` |' for x in delivery['screenshots'])
report+='\n\n## 확인된 Library 화면 전달\n\n아래3개는현재고정본의1920×1080합성자료입니다.마지막화면은통제된클라이언트오류이며실제서버장애가아닙니다.\n\n| 파일 | 확인된 Library ID |\n|---|---|\n'+image_rows+'\n'
(out/'REPORT-ko.md').write_text(report)
report_summary=re.sub(r'\]\(([^)]+)\)',lambda m: m.group(0) if m.group(1).startswith(('https:','http:','#')) else '](desktop1920/refinement-recheck/'+m.group(1)+')',report)
history=base/'history';history.mkdir(exist_ok=True)
summary=base/'Loretune-Design-Update-20261026-ko.md'
backup=history/'summary-before-refinement-recheck-20261026.md'
if not backup.exists():backup.write_bytes(summary.read_bytes())
summary.write_text('# Loretune 최신 디자인 업데이트 — V1–V4 재검토\n\n현재 결론: **81.0/100, 26항목 평가 배점 커버리지100/100**. 실제 모든상태 검증률이 아니며 H1/H2는미검증,H3/H4는정의된표본PASS입니다. 아래현재보고서이후의이전문서는해당버전의역사적기록입니다. 기존74.3점은현재평가가아닙니다.\n\n'+report_summary+'\n\n---\n\n# 이전 문서 보존 — V1–V4 적용 전 이력\n\n아래 내용의pre-shell·202ea641점수/미검증상태는해당시점의기록으로보존합니다. 현재상태는위5fcc2cca재검토가우선합니다.\n\n'+backup.read_text())
matrix=base/'METHODOLOGY-FIT-MATRIX-ko.md'
mb=history/'methodology-before-refinement-recheck-20261026.md'
if not mb.exists():mb.write_bytes(matrix.read_bytes())
matrix.write_text('''# 방법론 적합성 표 — 2026-10-26 V1–V4 검증 보강

기존 채택/조건부/제외 결정과 공개 출처는 유지합니다. 이번 갱신은 새 방법론 도입이 아니라 고정된 과업에 대한 실제 검증 추가입니다. 아래 기존 표의 과거 미검증 문구는 당시 기록이며, 현재 검증은 이 절과 새 보고서를 우선합니다.

| 방법·fit | Loretune 과업/결정 | 구현 연결 | 이번 검증 | 불확실성 |
|---|---|---|---|---|
|과업 분석·분할 공간 / 채택|영상·시간축·검토 맥락을 유지하며 상세만 내부scroll|bounded shell/transport V1|1920 정밀505×284,문서1080;35Tab 가시|1280영상218×123의절충. 실제작업속도시험없음|
|객체정체성·recognition / 채택|편집선택과재생장면을역할로명명|V4/B1|편집01·재생02·hash불변|고객인지시간미측정|
|위험기반점진공개 / 채택|기술검증은닫힌상세;모델·비용·승인안내는보존|V2/V3|진단숨김/Enter공개,미선택/차단/긴이름/승인별도|모든plancommit/공급자오류UI는이번표본밖|
|실패계획·상태전이 / 채택|400거절≠unknown,기존조회·초안보존|scopedreview/F1/F3|controlled POST4·GET4 모두가로챔,장면전환·새초안race보존|실제서버장애·DBcommit·청구아님;연결복구문구개선여지|
|semantic role·대비 / 채택|오류는문자+면+경계,선택/focus/승인분리|기존tokens보존|오류실제opacity1쌍9.325:1|nativeoverlay/forcedcolors전체미검증|
|키보드·resize / 채택|정상Tab진입과복귀,큰문자reflow|H3/G2|초기keyboard여정완료;앱200%=28px/문서2505|실제browserzoom/스크린리더/사용자시험없음|

새점수81.0은7축26항목전문가판단이며구방법론의5축90점과비교하지않습니다.26항목평가가능과전체상태통과를구분합니다.H1/H2는U,H3/H4는범위한정PASS입니다. Blender직접자료읽기402는여전히제약이며직접성공으로수정하지않습니다.

상세: [V1–V4 독립 재검토](desktop1920/refinement-recheck/REPORT-ko.md), [점수표](desktop1920/refinement-recheck/scorecard.json), [최신 사용자 요약](Loretune-Design-Update-20261026-ko.md).

---

## 기존 방법론 선택과 출처 — 역사적 검증 문구는 해당 시점 기준

'''+mb.read_text())
index=base/'INDEX.md';s=index.read_text();s=s.replace('## 최종 독립 감사','''## 현행 V1–V4 재검토

- [현재 상세 보고서](desktop1920/refinement-recheck/REPORT-ko.md):81.0/100,항목평가배점커버리지100.전체상태통과는아님.
- [현행scorecard](desktop1920/refinement-recheck/scorecard.json),[geometry](desktop1920/refinement-recheck/geometry.json),[통제오류](desktop1920/refinement-recheck/controlled-errors.json),[종료불변](desktop1920/refinement-recheck/end.json).
- H1/H2미검증,H3키보드/H4측정대비표본PASS.앱코드/DB/서버읽기전용.

## 이전 shell 독립 감사 — 이력 보존''');index.write_text(s)
ch=base/'CHANGELOG-ko.md';ch.write_text(ch.read_text() if '## 2026-10-26 V1–V4 독립 재검토 추가' in ch.read_text() else ch.read_text()+'''\n\n## 2026-10-26 V1–V4 독립 재검토 추가

- 고정rubric/가중치/과거74.25·98점기록은수정하지않음.
- 현재5fcc2cca별도scorecard81.0·100점평가범위,26항목근거와gate갱신.
- 초기keyboard·모델4상태·통제오류/새초안race·앱200/1280회귀증거추가.
- 기존요약/방법론Library정체성보존갱신.이전문서snapshot을history에보존.
- 앱source/DB/서버·07원본명세·권리/비용/승인/noMCP/fal계약변경없음.
''')
checks={n:hashlib.sha256((base/'desktop1920'/n).read_bytes()).hexdigest() for n in ['RUBRIC-v1-ko.md','RUBRIC-v1.1-ADDENDUM-ko.md']}
assert checks['RUBRIC-v1-ko.md']=='9c1785b0075cdb8354ed93d6ec73264d114fb61c0a1eeb6020a80216a4506379'
assert checks['RUBRIC-v1.1-ADDENDUM-ko.md']=='416dbf028de1e8593ae182d37b7f0514d3252c43e96aff7a43831c84c1bd63ba'
(out/'report-validation.json').write_text(json.dumps({'score':81.0,'coverage':100,'items':len(items),'rubric_unchanged':checks,'end':end,'new_reports':[str(out/'REPORT-ko.md'),str(summary),str(matrix)]},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'score':score['display_score'],'coverage':score['coverage_max_points'],'axes':[(a['id'],a['earned_on_assessed']) for a in score['axes']],'items':len(items),'report_bytes':(out/'REPORT-ko.md').stat().st_size,'summary_bytes':summary.stat().st_size,'source_unchanged':True},ensure_ascii=False))
