# 세 패키지 디자인 finishing — 통합 준비 완료

**독립 presentation patch와 후보 증거를 준비했다. 실제 앱은 수정하지 않았다. 새로운 점수나90달성을 주장하지 않는다.**

- [정확한 통합 patch](integration-presentation.patch) — `index.html` 한 파일, 기능fal patch다음에 적용.
- [통합 순서·접점·해시](INTEGRATION-ko.md), [CSS 원문](production-finish.css), [표시 함수 원문](production-presentation.js).
- [19개 집중 검사](focused-tests.json), [8개 browser검사](candidate-browser-checks.json), [추가 상태·focus검사](states-metrics.json), [최종 실제 색·크기](final-metrics.json).

## 구현한 세 가지

**A. 미디어 객체** — 양쪽 comparison의 stage를288px로 제한하고 `object-fit:contain`으로 원본비율을 보존했다. square128×128와landscape640×360의 stage/facts기준선이 같고, image/video도288px로 같다. 실제 native video controls 유지. media facts의 길이에 ‘원본’을 붙여 rail의 ‘편집’ 길이와 구분했다. 새 poster를 만들지 않고 기존이미지와 일관된 ‘영상’ fallback을 쓴다.

**B. 타입·상태** — 실제 Take제목700→500, scene제목600→500, 지원metadata500→400; 장면주제목은600, 검토메모400. 기존본문도400이었다는 점을 구분한다. 모든 글자가실제로semibold였다고 단정하지 않는다. 선택은tonal면+왼쪽marker, keyboardfocus는외곽dashedring, 검토상태는기호+짧은문자다. ‘Take 승인됨’ 반복 테두리를 없애도 각객체의Take번호와검토상태는 남는다.

**C. 문맥 inspector** — 검토결과/메모/수정이 주역. 기존업로드·모델제작·이전경로/회수·테스트·참고 controls를 ‘제작 도구’ 아래로 모았다. 선택 장면의 이미지/영상모델, 연결상태, 다음준비를한맥락으로표시한다. 준비·견적·승인·회수·rights기능은기능스레드renderer/handler그대로다. 진행중/미확정/오류/미검토작업은묶음을자동으로펼친다. 저장실패피드백은원래project/scene/Take에만보존하며입력을지우지않는다.

## 저장 버튼 판정

실제8773에서 초안입력후 `disabled=false`였지만 즉시측정한 배경은#222,글자는#101010이었다. 후속측정과캡처차이를통해 disabled→enabled의색전환중중간색도관찰했다. **항상비활성인버튼이라고판정하지않았다.** 후보는활성색을명시하고저장버튼색transition을제거했다. 최종입력직후부터#f4f4f2/#101010이고boolean활성상태도맞다. 권한·유효성검사를우회해강제로enable하지않는다.

## 실제 전후·후보 packet

‘before’는1b0ab597…269b3실행본, ‘candidate’는b02db8e…bd9ec독립iframe이다. 같은기존3장면fixture를기본비교에사용한다. 혼합aspect는기존4장면QA의장면3으로분리한다. 모두허용된로컬합성미디어이며화질점수대상이아니다. 실제최신fal backend를 실행한통합후증거가아니다.

| 상태 | 이미지 | 조건 |
|---|---|---|
| 이전desktop |[before](before-desktop-1280.png)|1280×900·실제앱|
| 후보desktop |[candidate](candidate-desktop-1280.png)|1280×900·같은프로젝트/선택|
| 이전mobile |[직전실제승인](../creator-integrated-review/03-actual-approved-390.png)|390×844·동일build/fixture,이전감사캡처|
| 후보approved |[승인](candidate-approved-390.png)|390×844|
| 후보unreviewed |[미검토](candidate-unreviewed-390.png)|브라우저메모리투영,서버저장없음|
| 후보rejected |[거절](candidate-rejected-390.png)|브라우저메모리투영,서버저장없음|
| 후보dirty |[미저장](candidate-dirty-390.png)|임시메모리draft|
| 후보error |[저장확인필요](candidate-error-390.png)|act=false로컬모의,실제서버장애아님|
| 혼합aspect |[정사각형/가로](candidate-mixed-aspect-1280.png)|실제기존2개이미지|
| image/video |[영상/이미지](candidate-image-video-1280.png)|실제기존미디어/nativecontrols|
| 제작overview |[모델·상태](candidate-production-1280.png)|선택값은실제fixture,연결은미검증으로표현|

모든주요packet이미지를저장후열어검사했다. 추가`candidate-running-projection-1280.png`는마지막미세CSS조정전의계약투영보조근거이며최종시각평가packet에는넣지않는다. ‘실제공급자생성중’ 증거가아니다.

## 측정·검사

| 항목 | 이전실제본 | 최종후보 |
|---|---:|---:|
| 미리보기 |736×324,y206|동일|
| timeline하단 |867.3px|859.1px|
| 저장검토section높이 |415.5px|340.5px(도구를하위묶음으로이동)|
| square/landscape비교높이 |450/약265px|288/288px|
| 비교facts상단 |엇갈림|669.25/669.25px|
| mobile문서폭 |390px|390px|
| 저장/취소높이 |44px|44px|

관측색상쌍의대비: 활성저장17.28:1,본문12.78:1,metadata9.15:1,input경계3.72:1,secondarybutton경계3.85:1,focus13.5:1. [계산](contrast.json). 이것은검사한색상쌍이며전체접근성준수claim이아니다.

19focused: empty/savedselection/unverified/blocked/preparable/test모드/unknown모델/escaping,원래mediahandler및F07controller동일성,ID보존,comparisonnativecontrols,오류피드백scope/명령payload보존.8browser:두비교조합,Escape복귀,dirty활성,실패입력보존,취소focus,미검토불완전입력차단,선택모델표시. 추가검사:모델dialog→Escape복귀,blocked/running분리와자동노출,준비버튼disabled유지.4개script문법통과.

최종기능staging `b094f68a…da7a`에patch dry-run/격리실제apply모두exit0. 병합script4개문법통과. staging은읽기전용,병합검사는이디렉터리의복사본에서만했다. 기능326tests는기능스레드근거이며여기서재실행한결과로합산하지않는다.

## 남은 수용 단계

[유한한동일rubric기준](ACCEPTANCE-90-ko.md)을통합본에서확인한다. 이전70/독립71은현재후보의점수가아니다. 이번후보에는새점수를주지않는다. 통합후지정packet과행동만재검증하고독립pixel평가로90달성여부를판단해야한다. 테스트개수로90을만들지않는다.

실제200/400%zoom,screenreader,고객사용성시험은미검증. 모든provider가사용가능하다는claim없음. source/servedHTML은16:41:52UTC에도1b0ab597…269b3불변. 서버재시작/공유소스/프로젝트데이터변경/외부호출0. 후보fetch변경요청과runtimeerror0. 전용Ego18종료완료. Ego0.6.0.20업데이트알림은확인했지만설치·설정변경은하지않았다.

차단된통합계약없음. 두검증스크립트의초기waitselector/전역함수참조오류는동일공간에서원인을확인후수정했고제품오류로집계하지않았다. 현재실행/전송blocker없음.
