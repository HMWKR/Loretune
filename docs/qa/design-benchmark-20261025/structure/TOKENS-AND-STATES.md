# 구조 후보의 토큰·컴포넌트 계약

M = Loretune 현재 source/DOM 실측. V = 공식 tutorial 이미지 직접 관찰. R = 기존 Refero metadata. P = 우리 제품을 위한 제안. 타사의 정확한 CSS computed value는 확보하지 못했다.

|역할|Neural Frames 공식 이미지 V|Loretune 이전 M|후보 P / 유지 M|
|---|---|---|---|
|작업 배경|어두운 canvas, 작업별로 한 단계 밝은 surface|canvas #101010, panel #171717, raised #222|기존 유지 + chrome #151515, timeline work #1b1b1b|
|선·구분|상대적으로 낮은 대비의 경계, 이미지가 강한 시각 요소|많은 영역이 #414141 경계|구조 경계 #303030; 실제 입력 경계 #777 유지|
|강조|coral 실행 버튼, 보라 번호는 문서 주석|white primary, selected underline|white는 현재 검토/출력 실행; 다음 단계는 secondary|
|글자|본문/label/title 구분 관찰, 실제 family/px 미측정|14px body, 16px section, 20px title, 12px meta|유지. 현재 장면16, 상세 설명12, 입력14. 한국어 system font 유지|
|간격|개념/장면/실행 영역별 반복 간격 관찰|상단7층, 여백이 누적|shell56 / stage56 근처 / status30; workspace gap16, mobile12|
|layout|Storyboard 넓은 개념+우측 실행, 장면 grid|rail220 + center, inspector 전체폭 아래|184 / fluid / 288; 901–1150에서는148 / fluid / 260|
|media|여러 장면 이미지가 내용 대부분|preview720×405; 다음 조작이 아래로 밀림|preview height clamp220,36vh,360 / contain; rail·review·timeline 동시 노출|
|radius|중간 정도 radius 관찰, px 미측정|controls8 / panels12|controls8 유지 / media·timeline10 제안|
|motion|정지 이미지로 미확인|기존120ms color transition|새 모션 없음, reduced-motion 기존+명시 override|
|mobile|공식 제공 이미지로 미확인|desktop 요소가 긴 세로 목록|장면/미리보기/검토 panel, 모델·상태는 작품·설정 disclosure|

## 컴포넌트 상태 점검

|컴포넌트|후보 처리|검증 수준/통합 후 확인|
|---|---|---|
|선택 장면/Take|기존 active·선택 텍스트 유지. Take 선택 handler 보존|고정 fixture 선택 상태 이미지 확인. 재선택 쓰기 작업은 미실행|
|미디어|실제 img/video 유지; video native controls 유지, 이미지에 가짜 play 버튼 없음|이번 캡처는 기존 단색 이미지 fixture. video transport는 새 후보에서 미검증|
|검토 CTA|선택 Take 이유·결정·기록이 미디어 옆|버튼 위치 확인. 새 승인 요청은 안 함|
|disabled|기존 disabled 상태 유지, ID별 primary 스타일이 disabled를 덮지 않도록 override|source 검사. 최종 override의 실제 disabled pixels 미검증|
|계획/모의 실행/비용|원래 executionCards 및 모든 handler 유지, 별도 disclosure|기존 승인된 모의 카드 관찰. 새 제안/승인/실행 미실행|
|loading/error|notice role=status/aria-live 보존, 오류 색과 전체 문장 유지|기존 정상 notice 관찰. 후보 loading/error 전환은 이번 읽기 검사에서 미검증|
|timeline|기존 track/status, 숫자·음원·자막·복원·저장 ID 유지|요약 실제 데이터 확인. 세부 컨트롤 입력/저장 회귀 필요|
|mobile panels|tabpanel/aria-controls/roving tabIndex, Left/Right/Home/End 구현|resize 후 panel 전환 구조 확인. ArrowRight 선택/포커스 이동 확인. 나머지 키와 keyboard-only 전체 flow는 미검증|
|focus|기존2px outline/3px offset, 우측 inspector padding8|최종 padding 수정 및 실제 focus clipping 미검증|
|모델 dialog|원래 model dialog와 설정 handler 유지|전체 모델명 표시, Escape 닫기와 opener 복귀 확인. 저장 동작은 실행하지 않음|
|empty|기존 빈 media/빈 plans/jobs 문구 유지|새 빈 fixture를 만들지 않아 미검증|
|긴 한국어/확대|wrap·fluid width·44px mobile targets 유지|320/390 실제CSS viewport 확인. 실제200/400% zoom, screenreader 미검증|

원래 기능 함수를 수정하거나 백엔드 동작을 대체하지 않았다. 첫 검사에서 발견한 modelDefaultsBar 누락을 고쳐 최종 runtime ID 누락0/중복0을 확인했다. 핵심 원래 handler와 QA 프로젝트 fingerprint도 불변이었다. 출력 CTA는 timeline 헤더에서 첫 화면에 보인다. 전체 쓰기 workflow 회귀는 통합 후 별도 수행한다.
