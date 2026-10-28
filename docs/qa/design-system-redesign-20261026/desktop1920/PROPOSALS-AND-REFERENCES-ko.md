# 1920 중심 구성 가설·참조·상세 설명 형식

최초 제안 문서이며 2026-10-26 현재 미디어 수정본의1920 캡처를 수신·검토했다. 실제 판단과 수치는 [체크포인트 보고](REPORT-ko.md)에 분리했다. 아래 공간 치수는 제안으로 유지한다. 다음 평가 대상은 새 bounded-shell 고정본이다.

## 기능별 참고와 provenance

| 참고 | 실제 사용하는 근거 | 원본/촬영 맥락 | 이번 비교의 한계 |
|---|---|---|---|
| [Descript captured editor](https://refero.design/pages/7aaa7dcf-f7e2-4a12-aedf-10ce0576ba87) / [공식 timeline](https://help.descript.com/timeline/timeline-overview) |공통시간눈금과waveform/레이어정렬|연구세션이전달한Refero캡처.원본pixel크기·CSSviewport·DPR·촬영일은이번전달에미포함|정량1920live비교아님.이앱의동작이나토큰을직접측정한값으로쓰지않음 |
| Neural Frames 공식Track/Storyboard |장면별맥락·미디어중심작업단계·설정연결|저장Track3194×1494,Storyboard3210×1690.2026-04-09파일명,2026-10-25확보.공식튜토리얼설명이미지|현재계정liveeditor아님.원본파일명@2x로CSSviewport를임의로반계산하지않음 |
| [Neural Frames 공식 editor 기능](https://help.neuralframes.com/en/articles/8715740-what-do-all-the-features-on-the-video-editor-mean) |편집기기능역할설명|공식문서,연구세션제공|동일작품/viewport실험이나내부HEX증거아님 |
| [Frame.io captured review](https://refero.design/pages/afd4cddd-a493-47c7-9f65-da6b74819871) |실제asset/versionthumbnail과player/검토의인접성|연구세션제공캡처,정확한원본크기/DPR미포함|모바일공식자료를desktop1920실측으로사용하지않음 |
| [Runway captured home](https://refero.design/pages/bc5ff496-55ad-4478-a968-62f7e641b9db) |조용한prompt shell·주/보조입력위계|home캡처,원본크기미포함|timeline/편집상태의증거로사용금지 |
| [Runway Studio 공식 문서](https://help.runwayml.com/hc/en-us/articles/52685547867667-Trimming-and-Assembling-Clips-in-Studio) |manual/chat과clip조립이같은작업맥락에있는설계참고|공식문서,연구세션제공|Loretune의APIprovider와무관.실시간사용성/성능측정아님 |

NF 이미지와 출처 manifest는 이 문서 기준 `../../design-benchmark-20261025/structure/`에 있다: `neural-official-track.png`, `neural-official-storyboard.png`, `neural-source.json`. 원본 크기는 파일 헤더로 확인했다. 이번 단계에서는 경쟁사 계정을 탐색하지 않는다.

경쟁사캡처를우리화면옆에배치할때원본aspect를보존하고,서로다른viewport/시점/콘텐츠임을각caption에적는다.설명용resize는가능하지만1920동등조건비교라고부르지않는다.경쟁사내부HEX·상호작용·점수·순위를추정하지않는다.

## 1920은1280의균등확대가아니다

이전1280검토에서실제preview는736×324,타임라인은y≈682–993이었다.이는이전고정CSS5f50ef…의실측이며새CSS에대입하지않는다.1920에서는단순히중앙열이넓어졌다고media가커지거나읽기효율이오르는것이아니다.특히높이상한과contain의조합에서는검정stage만넓어지고실제영상면적은크게늘지않을수있다.

### P1 · viewport 예산부터 검토

연구가제안한예시예산은header56 + toolbar40 + upperworkspace640 + timeline312 + footer32 =1080px이다.이는**Loretune시안용가설**이며현재측정값이나경쟁사실측이아니다.각행의padding/gap을중복더하면초과하므로모든세부공간을예산안에포함한다.rail약240,inspector약320,중앙flex도같은가설이다.

실제적용순서:

1. 새1920기준상태에서shell/preview/transport/Take/timeAxis/검토의rect를먼저읽는다.
2. 정상상태에서핵심transport·전체시간축·현재time/길이가firstview안에있는지확인한다.
3. 부족하면무의미한세로gap과반복상태부터줄인다.그다음preview의가용높이와timelinelane예산을조정한다.
4. 본문을작게만들거나비용/권리/승인정보를삭제해억지로맞추지않는다.긴오류·장문·확대상태의정상scroll은허용한다.
5. 1280도같은비율로축소하지않고기능을유지하는보조회귀로확인한다.

### P2 · 중앙 media와 읽는 inspector의 균형

- 중앙stage너비와실제containframe너비를별도로본다.초대형검정여백을미디어성능향상으로세지않는다.
- portrait의좌우여백은정상이다.그여백을없애려고crop/stretch하지않는다.
- inspector는선택장면/시간→Take/version→검토상태/이유→필요행동순서를유지한다.읽는prose가가로전체로늘어나지않게한다.
- 240/320px의rail/inspector가현재한국어·assetthumbnail·모델이름에맞는지판단한다.숫자자체를통과조건으로강제하지않는다.
- 승인완료카드는차분한결과와‘검토수정’이면정상이다.빈공간을채우려primaryaction을추가하지않는다.

### P3 · timeline의 공통 좌표와 정보량

- ruler,shot boundary,waveform,playhead의x원점과px/sec를동일하게검증한다.2초블록은4초블록절반폭이어야한다.
- audiooffset·source trim·editedstart를서로다른시간영역으로표시한다.숫자만맞고frame이안따르면미디어gate실패다.
- lane높이는필요한label/상태/파형에맞춘다.동일승인상태를여러lane에반복하거나큰padding으로정보가없는공간을늘리지않는다.
- 현재구현하지않은drag/beat snap/transition을그림으로암시하지않는다.진짜파형없으면미분석을표시한다.

### P4 · 색상·타입을 선택하는 이유를 남김

- 기존중성palette는미디어의색을방해하지않고선택·focus·오류를분리할수있는baseline이다.‘새색금지’가아니라새역할이필요한지판단한다.
- 새accent제안은어떤판단을빠르게하고기존색으로왜부족한지,실제대비와다른상태와의구분을보여야한다.브랜드장식만으로점수를올리지않는다.
- 1920의글꼴은기기폭에비례해모두커지는것이아니다.주제목/본문/metadata/시간의역할·읽는거리·행길이를검토한다.
- 앱배율과browserzoom은별도변수다.20px제목이24px제안과다르다는사실만으로결함을만들지않고실제위계를본다.

## 상세 발견 작성 양식

각발견은아래연결을모두갖춘다.미확인원인은가설로남긴다.

| 항목 | 반드시 쓰는 내용 |
|---|---|
| 발견ID·우선순위·주평가축 |예:A-02/P2/구성.같은결함의중복감점축을만들지않음 |
| 관찰 |어느revision/작품/상태/viewport에서무엇이보였는지 |
| 원인 |computed/style/DOM/시간binding의근거.확정과가설분리 |
| 사용자영향 |무엇을읽기/비교/조작하기어렵고얼마나자주생기는지.실사용자시간측정없으면초단위절약주장금지 |
| 근거 |저장후열어본capture,selector/행,rect/time/색수치,재현단계 |
| 수정 제안 |최소변경과유지할계약.대안이있으면tradeoff |
| 재검증 |동일fixture/state/viewports,예상관찰값,회귀·gate,실패조건 |
| 점수 영향 |해당세부항목의앵커선정이유,다른축의중복감점여부 |

예시(아직현행1920결함아님): `preview높이상한 + 유동너비 → 실제frame은유사한데stage만확장 → 눈에보이는작업영역의효율저하가능 → 실제contain면적/viewport및timelinefold측정 → viewport예산내높이·읽기폭조정 → 같은media/상태의전후frame면적과조작가시성재검증`.이예시에는현재점수를부여하지않는다.

## 다음 실행 경계

1. 미디어3건은 독립 코드 재검증에서 종료됐다. 이제 bounded-shell 최종 고정hash를 수신한다.
2. 고정rubric해시보존후1920S01–S08측정,1280보조회귀.
3. gate와coverage를먼저보고하고점수근거를항목별로설명.
4. 필요한후속디자인만별도후보로작성;공유앱통합은기능소유세션이수행.

모바일추가작업·새provider연결·계정조작·유료생성·새승인/삭제는범위밖이다.
