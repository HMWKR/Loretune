# Aside 내부 REA MCP 경쟁사 파일럿

2026-10-25. 사용자 요청으로 Aside에 실제 위임한 제한 조사다. 기존 경쟁사 문서를 대체하거나 제품 구현 완료를 의미하지 않는다.

## 실행 및 수락

- Aside 세션: `oH2MQN6ZLPb0n35j`.
- 경로: Codex → Aside CLI → Aside 내부 `mcp__REA__binary_session`, `mcp__REA__capture_browser_scenario`, `mcp__REA__export_evidence_bundle`.
- 상태 응답: REA 6.7.0, 클라이언트 `aside-browser` 1.26.1024.24. CLI는 설치 가이드에 따라 1.26.1023.1115로 업데이트됐다.
- 공개 캡처: Chromium 149.0.7827.55, 1280×720, 익명 저장소, 페이지 탐색 후 800ms 대기, URL 및 접근성 트리. 네트워크 본문·인증 저장소·JS 번들 분석은 수행하지 않았다.
- Driver가 내보낸 JSON을 직접 읽고 세 레코드의 대상 URL, Evidence ID, 완료 상태, 소유 브라우저 종료를 확인했다. Neural Frames 입력 화면 스크린샷도 직접 확인했다.
- 수락 범위: Aside 내부 REA 호출 및 공개 화면 수집 성공. 실제 생성·샷 편집·내보내기·백엔드 구조 검증은 제외한다.

## 관찰 결과

| 제품 | 실제 관찰 | 공식 주장 및 미확인 |
|---|---|---|
| [Tunee](https://www.tunee.ai/features/music-video-generator) | REA 공개 캡처에서 음악 선택·설명 입력·모델·생성 진입 UI. Aside에서 Google 로그인 후 지정 계정 이메일 확인. 에이전트·동영상·캐릭터·프로젝트·라이브러리 탭 관찰. | 채팅으로 콘셉트·스크립트·콘티·씬 편집, 최대 6분, 통합 편집기는 공개 문구다. 실제 결과 생성·부분 수정·승인 정책은 미검증. |
| [Anijam](https://www.anijam.ai/tools/ai-music-video-generator/) | REA 공개 페이지 텍스트·입력 UI 수집. 지정 Google 계정 선택 후 Aside에서 유입 경로 설문으로 이동. 설문은 제출하지 않음. | 음악/가사/아이디어 입력, 최대 4명 캐릭터, 타임라인 수정, 출력 해상도는 업체 설명이다. 로그인 후 편집기는 미확인. |
| [Neural Frames](https://www.neuralframes.com/) | REA는 Kling 공지 모달만 수집. 별도 Aside에서 익명 `/songs` 입력 화면과 `Music → Track → Storyboard → Video`, 선택 설명·음원 업로드·템플릿·비활성 Create 관찰. 메뉴에 Login이 있어 로그인 성공으로 분류하지 않음. | REA 캡처의 complete는 요청한 캡처 완결성으로, 홈페이지 본문 전체 관찰을 뜻하지 않는다. 캐릭터 재사용·샷 수정·4K 출력은 실행 검증하지 않음. |

## Loretune 제안

1. 대화형 입력과 프로젝트 자산 탐색을 연결한다. 대화만으로 현재 선택된 곡·캐릭터·샷·take의 상태를 숨기지 않는다.
2. 입력 화면에 제작 단계를 유지하고, 다음 단계에 필요한 조건을 표시한다. Neural Frames의 익명 입력 화면처럼 실행 전 무엇이 필요한지 드러내는 방식은 참고할 수 있다.
3. 차별화 가설은 승인된 아티스트/세계관 버전의 계승, 부분 수정 영향·견적, 승인 take 보존으로 둔다. 이번 조사로 경쟁사에 해당 기능이 없다고 단정할 수 없다.

## Evidence

- Tunee: `ev_f80a467947b2efa7c6985d796bdc26c880024641f13471adbf19cb6bf5318c63`
- Anijam: `ev_f1517e70fe089e84046e5f1360508f3fc2a88634d2f127d52474c807c2c9c50f`
- Neural Frames 공지 모달: `ev_299213ed540512683d0498996e22bfdec74c8377a83b9a25cd9a153b4d117e36`
- [원본 REA 번들](/Users/leesungmin/.aside/u/0/sessions/2026-10-25_oH2MQN6ZLPb0n35j/tmp/loretune-aside-rea-20261025-evidence-bundle.json): 58,922 bytes, 3 records. Aside 임시 경로이므로 장기 보존은 보장하지 않는다.
- [직접 확인한 Neural Frames 화면](/Users/leesungmin/.aside/u/0/sessions/2026-10-25_oH2MQN6ZLPb0n35j/tmp/repl-display-KfmCTDveDYPDGGtF.png)
- [Aside 관찰 영수증](/Users/leesungmin/.aside/u/0/sessions/2026-10-25_oH2MQN6ZLPb0n35j/tmp/loretune-aside-observations.json): Driver가 세 제품 관찰, 부수 효과 보고, 조사 소유 탭 종료 기록을 확인했다. REA 원본과 별도인 에이전트 관찰 기록이다.

## 제한 및 부수 효과

Aside의 공통 지침 파일 읽기와 프로젝트 경로 내보내기는 권한 정책으로 거절됐다. 권한을 변경하지 않았으며 원본 Evidence는 허용된 Aside 세션 경로에 저장했다. 본 문서는 Driver가 작성했다.

사용자가 Google 로그인을 추가 승인했다. Tunee에서는 환영/가입 보너스 및 일일 로그인 크레딧 적립 안내가 표시됐다. Anijam은 유입 경로 설문에서 멈췄다. 업로드·프로젝트 생성·미디어 생성·결제·크레딧 소비는 수행하지 않았다. 생성 품질, 실제 처리시간, 비용 차감/환급, 승인/복구 동작은 미확인이다.
