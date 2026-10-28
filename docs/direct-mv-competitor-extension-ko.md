# Loretune 직접 AI 뮤직비디오 경쟁사 벤치마크 확장

검증일: 2026-10-25. 부모가 전달한 확장 보고서의 로컬 구현용 정리본. 원문 조사자는 부모이며 이 실행이 직접 로그인·생성을 검증한 결과가 아니다. 기존 design-ux-benchmark-ko.md, design-reference-lock.md를 함께 적용한다.

## 바로 적용할 결론

1. 빠른 제작과 감독 모드는 동일 프로젝트·승인·타임라인을 공유한다. 첫 화면은 음원·구간·비율·대표 이미지 중심이며 복잡한 모델 선택을 강제하지 않는다.
2. 음악 분석은 수정 가능한 버전 데이터다. 자동 분석 엔진이 없으면 수동 입력으로 표시한다. 가짜 파형·BPM·확신도 금지.
3. 캐릭터 정체성, 실제 시작 프레임, 스타일 참고, 끝 프레임의 역할을 분리한다. 첫 프레임 검토를 고비용 영상 생성보다 앞에 둔다.
4. 부분 수정은 대상 샷·보존 요소·영향·예상 비용을 실행 전에 보여준다. 새 take의 생성 성공과 승인을 분리한다.
5. 캐릭터 저장 자체를 차별점으로 주장하지 않는다. Neural Frames의 이전 캐릭터 검색, Anijam의 다음 에피소드 계승이 이미 문서화돼 있다. 승인된 아티스트·세계관 버전, 변경 영향, 곡 간 계승·복구가 Loretune의 검증 후보다.

이는 Loretune 설계 제안(P)이며 경쟁사 비공개 시스템을 확인한 사실이 아니다.

## 증거 등급과 범위

O: 공식 문서 UI 이미지·공개 페이지 텍스트 관찰. 로그인 앱 조작과 다르다.
D: 공식 가이드·요금표 주장. 품질·성공률 실험이 아니다.
P: Loretune 제안. U: 미확인(기능 부재를 의미하지 않음).

Refero에서 12개 도메인 첫 검색 페이지에 정확 일치 제품을 찾지 못했다는 부모 기록은 전체 수록 부재 증명이 아니다. 직접 경쟁사에는 공식 문서 이미지, 공통 패턴에는 기존 Runway·Boords·Hello Ivy를 쓴다. REA와 Refero는 별개다. 이 보고서에 REA 분석이나 로그인 생성 실험은 없다. 부모의 direct-competitors 이미지·JSON 경로는 Mac으로 전달되지 않았다.

## 제작 흐름 비교 (별도 O 표시 외 D)

|제품|음원·계획|캐릭터·수정·재사용|공식 근거|
|---|---|---|---|
|Neural Frames|Music→Track→Storyboard→Video, 파형·가사 타이밍 교정|최대3 주요 캐릭터, @지정·이전 검색, 씬 재생성; 세계관 승인 계승 U|[4단계](https://help.neuralframes.com/en/articles/12038142-handbook-the-four-stages-of-autopilot), [캐릭터](https://help.neuralframes.com/en/articles/12022762-what-is-multiple-character-consistency)|
|Freebeat|음원 분석→샷 계획, 8차원·6에이전트는 업체 주장|Character Bible·최대2명·선택 샷 재생성, 최대6분 홍보; 정밀 타임라인·곡 간 승인 계승 U|[제작](https://freebeat.ai/music-video-production/music-video-ads-brand)|
|VisionStory|음원·영상·Suno 링크→15초~10분 구간→캐릭터→비용|저장 아바타,9:16/16:9,720p/1080p/2K; 수동 프레임 편집 아님, 모든 비트 적중 보장 없음|[MV 가이드](https://www.visionstory.ai/tutorials/how-to-make-an-ai-music-video)|
|1MV|이미지+음원→비율→생성, 사용자 콘티 없이 구성|감독 스타일·입력 리믹스; 샷 수정·지속 기억 U. Free20초/Starter3분/Pro6분, 유료4K 표기; 공유 기본값 주의|[한국어 제품](https://1mv.ai/ko)|
|MusicMV|5초~6분 음원+1~2장 사진→전체/후렴→분석→컷 콘티|렌더 전 프레임 수정·다시 그리기,MP4 최대1080p·5비율. 공개 예시 구간/가사/프롬프트/카메라 O. 완성 샷 교체·곡 간 계승 U|[제품](https://musicmv.ai/)|
|Anijam|음원·가사·아이디어→콘셉트→분석→샷→타임라인; 파형·BPM·키 공식 UI O|캐릭터/스타일·장면 교체·타이밍·가창/비가창 경로. Next Episode O, 가이드 계승 D, 얼굴 유지 품질 U|[가이드](https://www.anijam.ai/blog/how-to-make-ai-music-video/),[기능](https://www.anijam.ai/tools/ai-music-video-generator/)|
|Tunee|음원 또는 Tunee곡→대화→콘셉트/스크립트/콘티/씬; 공개 이미지 분석 작업 O|프로젝트에 노래·캐릭터·자산·편집,최대6분·내장 편집기 주장. 승인 규칙·정확 트림 U|[제품](https://www.tunee.ai/features/music-video-generator)|
|Kaiber|Montage=한 주체/세계/스타일,Sequence=여러 행동·장소를 곡 구조에 배치|Generate/Reference/Restyle,Media Library. Sequence30초~4분·5비율·1080p, 별도 Timeline Editor. 샷 승인정책 U|[Montage](https://helpcenter.kaiber.ai/en/help/articles/2522505-music-video-montage-turn-audio-into-a-music-video-in),[Sequence](https://helpcenter.kaiber.ai/en/help/articles/5844253-music-video-sequence-create-music-videos-shaped-by-your-sound)|
|Revid|업로드/링크→구간→Lyrics/Beats→비주얼,가사/사운드웨이브 분리|Characters·가창 비중·씬 수정/컷 이동/자막 교정,MP4. 배포 기능은 무단 게시 승인 아님|[가이드](https://www.revid.ai/university/how-to-make-ai-music-video)|
|OiiOii|음원/가사→구조/정서→트리트먼트/샷→캔버스,서사/비주얼/퍼포먼스|캐릭터 재사용·샷별 수정,MP4·샷최대30초 홍보. URL지원 설명과 곧 출시 FAQ 충돌: 파일 업로드만 확정|[MV](https://www.oiioii.ai/en/music-video),[FAQ](https://www.oiioii.ai/faq)|
|BeatViz|Workflow:음원→모드→방향/스토리→첫 프레임→클립|시작/끝 프레임·참고 구분,라이브러리는 Workflow 범위. Compose 순서합성,임의 시간 배열은 별도 Editor 모델|[참고 역할](https://beatviz.ai/help/workflow/first-frames-vs-reference-images),[재생성](https://beatviz.ai/help/workflow/regenerate-video-clips),[합성](https://beatviz.ai/help/workflow/export-music-video)|
|Rotor|음원/구간→자체/스톡→스타일→비율/필터/텍스트|생성형 캐릭터 제품과 다른 기존영상 편집 대체재. 미리보기 후 다운로드 구매|[제품](https://rotorvideos.com/musicvideos)|

## 시각 증거와 적용

Anijam 공식 분석 UI(O): 중성 다크, 프로젝트/에피소드·단계 탭, 왼쪽 레일, 중앙 분석 카드, 오른쪽 대화, 파형 구간·BPM·키·길이. 정확 CSS/폰트와 라이브 동작 U. 타임라인 이미지(O)는 큰 프리뷰·영상/음원 트랙·시간코드·요약·다음 에피소드. P: 고정 음악 요약+샷 목록, 접는 대화, 다음 곡은 계승 버전 선택 후 음악/승인 새로 시작.

VisionStory 공식 주석 이미지(O): 파형 양끝 핸들·선택영역 이동·숫자 시간·재생 확인, 출력 이미지에는 음원/인물·비율/해상도/견적. P: 선택 구간·샷 수·생성초·립싱크초·비용을 실행 전에 함께 보여주고 숫자 입력 대안을 제공.

Tunee 공개 이미지(O)는 입력자산과 분석 작업을 대화에 연결한다. 문장 스트림만으로 완료하지 않고 실제 객체/작업 상태를 제공한다.

공통 UI 근거: [Runway 진행](https://refero.design/pages/0f45fd53-dee9-457a-8d37-b2155b970077),[Boords](https://refero.design/pages/439138ac-c66b-42b4-9b6e-6dce25e5cd3e),[Hello Ivy](https://refero.design/pages/bf2a4956-c059-48c1-9709-b08fd5541630). 직접 MV 기능 증거로 전용하지 않는다.

Freebeat의 Director/Character/Timeline 파일은 추상 유리 아트로 편집기 증거에서 제외. BeatViz/MusicMV 이미지 403,Neural Frames 직접 다운로드403(웹 텍스트 가능). 제한 우회 없음. 부모 이미지 파일 anijam-ui-step2.webp,anijam-ui-step5.webp,visionstory-ui-02-select-the-clip.webp,visionstory-ui-04-output-and-cost.webp 및 tunee-workspace.webp는 로컬 존재 미확인.

## 비용·한도 (D; 구매 견적이나 API 원가 아님)

크레딧 단위는 서비스 간 동등하지 않다. 세금·지역·재생성 제외, 할인/연간환산/주간 구분. 실제 생성 버튼 견적이 최종 기준.

|제품|부모가 확인한 공식 가격·단위|주의·출처|
|---|---|---|
|Neural Frames|월 Knight $39/2,400,Ninja $99/7,200,Nirvana $299/24,000|모델별 Autopilot;미채택도 과금,frame-by-frame1credit/초를 전체 MV 요율로 쓰지 않음. [가격](https://www.neuralframes.com/pricing),[단위](https://help.neuralframes.com/en/articles/10507175-how-are-credits-used-for-each-tool)|
|Freebeat|프로모션 Basic$4.99/주1,990,Pro$26.99/월10,000,Ultimate$39.99/월19,000|Basic/Pro720p,Ultimate1080p;4K단정 금지. 일부 무제한은 웹수동 전용(API/배치 금지). [가격](https://freebeat.ai/pricing)|
|VisionStory|MV720p/1080p/2K=올림초당1/2/5credits,유료구독. 일반Pro$9.99/120,Advanced$29.90/480,Ultra$99.90/1,920|일반아바타1credit/4초와 다름. [가격](https://www.visionstory.ai/pricing),[MV](https://www.visionstory.ai/tutorials/how-to-make-an-ai-music-video)|
|1MV|Starter$9.90/월900·3분,Pro$29.90/월3,600·6분,480p1credit/초부터|가격 직접읽기 실패,공식색인/랜딩 교차. 고해상도 요율U,Free20초720p워터마크. [가격](https://1mv.ai/ko/pricing)|
|MusicMV|일회성$9.90/240,$29.90/800,$79.90/2,400;768p초당1,1080p2,프레임재작성1|구독아님. 실패프레임 재시도무료,무료결과 다운로드불가. 콘티폐기 미리보기수수료 제외반환. [가격](https://musicmv.ai/pricing)|
|Anijam|연간환산 Beginner$16/월($192/년),Creator$26($312),Master$58($696),MasterPro$166($1,992);월3천/6천/1.6만/5만credits|모델/이미지/초/곡별 차감. 네이티브720p/1080p와 업스케일·premium4K 소개 불일치. [가격](https://www.anijam.ai/pricing/)|
|Tunee|모델/길이/설정 견적,실패미과금,성공재시도 새작업|무제한수정≠무료재생성,플랜 금액본문 확정불가. [가격](https://www.tunee.ai/pricing)|
|Kaiber|도움말 Starter$10/월500,Creator$29/1,500,Pro$99/5,000|4개월전 도움말,동적가격본문 U.$5체험5일후유료전환. [공식](https://helpcenter.kaiber.ai/en/help/articles/6291249-kaiber-plans-what-you-need-to-know)|
|Revid|프로모션 Growth$39/월2,000;MV Base/Pro/Ultra5초당15/50/100|180초 최초540/1,800/3,600 단순산술,재시도제외. [가격](https://www.revid.ai/pricing),[가이드](https://www.revid.ai/university/how-to-make-ai-music-video)|
|OiiOii|구독·모델별credits,즉시/출석보너스 분리|통화/기간/동적값 달라 고정USD확정안함,최대초 보장아님. [가격](https://www.oiioii.ai/price)|
|BeatViz|첫프레임Standard3/Pro·Premium5;Fast720p8초35,Pro1080p5초60;립싱크별도20/초|컷올림·차감시점 분리,짧은마지막컷 전체비용,성공재생성 재과금. [비용](https://beatviz.ai/help/workflow/credits)|
|Rotor|1credit$9.99,5$44.99,10$79.99,50$299.99;MV3/가사4. Video연$179.88(월환산$14.99)|Streaming월환산$9.99는Canvas/AppleMotion,전체MV무제한아님. 구독아티스트수/PAYG다운로드 조건. [가격](https://rotorvideos.com/pricing)|

P: 견적은 이미지계획/요청클립/립싱크/재시도/합성/업스케일로 분해. 무료·포함·추정·실사용·미확정 구분. 실제 엔진 없이 가상 크레딧을 결제처럼 표시하지 않는다.

## 화면·상태 계약(P)

- 새 작품: 음원,전체/후렴/숫자구간,비율,대표이미지,서사/퍼포먼스/비주얼라이저. 권리와 외부전송 별도;미구현 립싱크를 가창완료로 표시 금지.
- 음악: 파일명·길이·선택구간·재생·분석출처. 구간/가사/비트의 값별 출처·수동수정·버전. 확정 후 변경은 관련 매핑/자막/가창 stale이며 기존 영상 삭제 금지.
- 콘티: 샷번호·음악구간·시작끝·가창·생성/검토상태. 참고역할별 지원 사유,얼굴/의상/배경/구도 검토. 프레임 재생성과 움직임 재생성 분리.
- 준비부족: 누락항목과 이동. 대기: 제출시각·샷·설정·실제 취소지원. 진행: 단계·업데이트·이전 승인본. 성공:검토대기·소요·실사용. 실패:분류/요청ID/과금/복구. 지원안됨:제약·입력수정. 결과미확정:기존job조회,무조건재발행 금지.
- 부분수정: 대상샷/길이/유지프레임/변경범위/예상비용/승인본보존/자동선택 여부를 명시.
- 출력: 자산존재≠선택≠타임라인배치. 음악절대시간·프로젝트상대시간,누락/실패/미승인/음원길이차/비율/원본해상도 검사. 입력manifest고정. 순서합성을 정밀리플/스냅편집으로 부르지 않는다.
- 다음곡: 아티스트/의상/장소/팔레트/카메라 규칙 선택계승,음악/가사시간/샷승인/비용은 새시작. 버전/승인자/시각/출처 고정,이전곡 소급없음.
- 스타일: 기존 중성다크 유지,경쟁사 색 혼합금지. 본문14~16px/보조12~13px/시간 tabular nums는 자체 토큰. 모션120~220ms 제안은 실측아님,reduced-motion 축소. 색만으로 상태표현 금지,숫자·키보드 대안.

## 구현 객체·의존성(P)

AudioAsset(해시/길이/샘플레이트/채널), MusicAnalysisVersion(audio/start/end/sections/lyrics/beats/출처/수정/version), ArtistWorldVersion(정체성/의상/장소/스타일/참고/승인/이전버전), ShotPlanVersion(analysis/time/prompt/가창/reference역할/승인프레임), GenerationJob(provider/capability/input snapshot/idempotency/stage/error/retryable/provider job), Take(shot/job/asset/duration/parent,불변), TimelineClip(take/trim/timeline/audio매핑), Estimate/Ledger(견적유효시간/단위/예약/실차감/환급/미확정/job), ExportManifest(정확버전/설정/체크섬).

가사수정은 관련 자막/립싱크만 stale. 캐릭터참고변경은 미래기본/기존샷재계획 구분. 프레임변경은 미래생성만,선택영상보존. 선택변경은 새export필요,과거보존. 재개는 provider/DB조회 먼저. SQLite jobs 트랜잭션·UNIQUE idempotency·원자파일이동으로 시작;경쟁사사진만으로 클라우드큐 필수라 주장 금지.

## 우선순위와 수용 시나리오

P0:원본·구간·실제음원MP4,선택/승인분리,고정manifest,계승버전,미지원표시.
P1:음악/가사교정·프레임게이트·구간샷·부분수정영향/견적·세계관계승.
P2:품질/경제성 검증 후 beat snap/립싱크/최적화. 무한캔버스·에이전트시각화·자동게시를 우선하지 않음.

1. 음원32~47초→15초MP4 오프셋 일치.
2. 한국어 가사1줄 수정→관련자막/가창만stale,영상보존.
3. 첫프레임변경→승인take/export해시불변.
4. 연속클릭/새로고침→providerjob/차감중복없음.
5. 성공응답유실→provider조회,재발행금지.
6. 한샷실패→나머지승인보존,실패만재시도.
7. 24초·5초단위→마지막올림견적.
8. 렌더중선택변경→원manifest완료,새export안내.
9. 다음곡→승인아티스트계승,분석/샷승인초기화.
10. 키보드구간/선택/비교/승인/출력,오류시입력보존.

## 실제 로그인 검증 필요

Neural Frames(가사·이전캐릭터),MusicMV(콘티·결제전게이트),BeatViz(재생성·Compose·차감),Anijam(다음에피소드),Tunee(편집·부분수정). 한국어인식·얼굴/의상드리프트·비트오차·복구·대기·성공률·차감/환급은 U. 비밀번호 채팅요청 금지,대상과 목적별 안전한 직접 로그인 경로 제공. 로그인은 결제/크레딧소비/자료업로드 승인이 아니다.

부모 증거 부록 specialist-evidence-report.md, specialist-image-manifest.json, refero-coverage.json은 부모 환경에 있으며 본 Mac에 반입되지 않았다. 보고서 저장 자체는 기능 구현이나 수용 테스트 통과가 아니다.
