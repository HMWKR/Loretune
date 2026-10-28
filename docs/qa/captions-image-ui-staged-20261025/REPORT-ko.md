# 자막 미리보기·이미지 복구 UI — staging 완료

원본 앱 통합 전 패치다. **273개 전체 회귀 통과**, 새 14개 caption/recovery 사례 포함. Python AST와 inline JS 3개 구문 검사, baseline 대조·patch dry-run 통과. 실제 공급자 호출·키 읽기·원본 DB 변경·8773 재시작은 모두 0이다. 테스트 개수는 MVP 완성률이 아니다.

## 완료된 변경

- `caption_preview.py`, `app.py`: 완료된 렌더의 승인 timeline snapshot에서 WebVTT를 만든다. 현재 편집 중인 자막은 사용하지 않는다. MP4 체크섬·완료 상태·원본 사용권을 검사하고 같은 localhost 권한 경계에서 제공한다. Unicode/markup/빈 줄·export의 millisecond rounding을 보존한다.
- `index.html`: 결과 미리보기 video에 승인 자막 track을 연결하고 해당 출력 버전·로딩/실패 상태를 표시한다. 다른 프로젝트/임의 URL을 결과로 열지 않는다.
- `image_recovery.py`, `image_pipeline.py`, `app.py`: 연결 없음/통합 미검증/차단/사용 가능 상태를 서버 검증 사실에서 계산한다. 모의 transport를 실제 사용 가능으로 표시하지 않는다. 실제 활성화 버튼은 disabled이며 key 입력/새 연결 생성 API는 추가하지 않았다.
- 기존 이미지 job의 상태 조회와 결과 수집을 서로 별도인 **일회 복구**로 처리한다. job/request/workspace/project/connection/operation/결과 fingerprint/만료를 고정한 trusted server 허가가 필요하다. 권한 거절은 해결 근거가 없는 한 반복하지 않는다. 브라우저/모델은 허가를 만들 수 없다.
- `generation_queue.py`: 기존 receipt를 보존하며 복구 중 재시작은 재조회 필요 상태로 남긴다. 동시 worker·중복 클릭으로 다운로드/Take가 중복되지 않는다. Take 등록 직전 현재 권리와 grant를 재검사한다. 기존 선택·승인·비용 상태를 보존하며 복구가 환불이나 재생성이 되지 않는다.
- 복구 대기 중 실행 버튼이 남고, 완료된 결과에도 허가 필요 문구가 남던 UI 결함을 브라우저에서 발견해 수정했다. 최종 문구는 로컬 저장·Take 등록 완료와 별도 선택/검토를 안내한다.

## 검증과 실제 화면

`test-matrix.json`에 14개 시험 이름을 보존했다. 최종 `full-regression-final-policy.log`: **273/273, 33.673초**. 초기 전체 시험의 두 오류는 stage에 누락된 기존 synthetic fixture였으며 정확한 fixture를 반입한 뒤 통과했다. 초기 로그도 삭제하지 않았다.

| 범위 | 기대 / 관측 | 증거 수준 |
| --- | --- | --- |
| 승인 자막 고정 | v1 승인 출력 뒤 v2 미승인 수정해도 v1 두 줄만 렌더/미리보기 | 실제 FFmpeg 파일, DB, 브라우저 |
| 자막 타이밍 | 첫 줄 0–3초, 둘째 3–6초; 6초 영상·음원·mov_text·WebVTT 일치 | ffprobe, 추출 SRT/VTT, 실제 화면 |
| 권한/잘못된 출력 | 없는 job404, 미완료409, 다른 Host/제한 principal403, 변경 MP4·사용 중지 원본 거부 | localhost HTTP/Store tests |
| 연결 상태 | 네 가지 상태, fake는 available 불가, 실제 활성화 disabled | synthetic state/실제 renderer JS; live available 미검증 |
| 기존 결과 복구 | 기존 request를 사용해 수집→Take1; 선택 null; 자동 재생성 없음 | 합성 HTTP 주입 + 실제 DB/브라우저 |
| 401/403·만료 | 새 근거/일회 허가 없으면 수집 차단; 404/410은 상태 확인부터, 자동 재시도 없음 | fixture tests; 실제 과거 fal 파일 미접근 |
| 중복/재시작/권리 | worker 경합 다운로드1회, 사용한 허가 재사용 불가, grant revoke·cross-project 차단 | SQLite/파일시스템 tests |
| 비용 | 복구 후에도 uncertain/actual null을 보존 | browser fixture DB; 실청구 검증 아님 |
| F07 | 응답 대기 중 새 검토 초안과 다른 컨텍스트를 보존하는 기존 실제 JS 시험 통과 | 전체 회귀에 기존 test_comment_draft 포함 |

브라우저 자막: synthetic 440Hz/단색 fixture, MP4 6.000초 H.264 640×360, AAC48kHz, mov_text6초. 화면에서 첫 cue와 둘째 cue가 표시됨을 확인했다. 임베디드 MP4 자막만 브라우저가 자동 지원한다고 가정하지 않고 WebVTT track을 붙였다. `browser/caption-first-cue.png`, `caption-playback.png`, `caption-evidence.json`, `approved-caption-export.mp4/.srt/.vtt`에 보존했다. 첫 cue 화면의 아래 편집기는 저장 v2/승인 대기이며 출력은 v1이다.

이미지 복구: 실제 공급자 대신 합성 HTTP403 상태와 별도의 합성 해결 근거를 주입했다. 버튼 클릭 후 대기 중 재제출 버튼이 없어지고 Take1이 등록됐다. `browser/image-db-evidence.json`: job `9f4de45b-0721-43f0-bdfb-6ba4e9bfa97d`, imported, Take1개, selected=null, 사용한 복구 허가1개, 비용 uncertain/actual null. `11111111-1111-4111-8111-111111111111`는 의도적인 **가짜** provider request ID다. 실제 fal403 요청을 재시도한 것이 아니다. 마지막 화면은 테스트 데이터 복사본을 최신 코드에서 재개해 같은 Take를 읽은 결과다.

## 패치와 freeze

- 적용 파일 7개: app.py, generation_queue.py, image_pipeline.py, index.html, 새 caption_preview.py, 새 image_recovery.py, 새 tests/test_caption_image_recovery.py.
- `implementation.patch`와 `patch-files/`, 정확한 해시는 `staged-release.json`.
- main baseline 파일94개 전부 원래 해시와 일치. 8773 main HTML source=served: `4f1805f00abb1ba2b5f7d6012727b4736e97cd4c35a007942ef6550781ae30dd`.
- staging HTML source=served: `b7c2cc9a01f6aec3073c269636beb5597c8c878cf004074c95a52b4f84ba470c`.
- staging patch SHA256: `3db58b7c8b22efa9e535b1976c89d2a3bd9278c0f9f61ea9e5a640310e7e1eb2`.
- staging root는 `stage-path.txt`; image QA http://127.0.0.1:57461 (session93378), caption QA http://127.0.0.1:64576 (session64669). 두 서버는 격리 synthetic 데이터만 사용. main8773은 그대로다.
- 부모의 통합 조정 전에는 원본에 적용하지 않는다. 새 studio-pass 비교 기본값/검토 컨텍스트/상태 라벨 패치는 아직 이 baseline에 없다. 해당 변경을 중복 수정하지 않았다. 추후 그 패치와 합칠 때 F07 최신 초안·장면/Take 컨텍스트 회귀를 다시 실행해야 한다.

## 남은 정확한 경계

**현재 승인된 staging 범위는 완료**다. 실제 이미지 활성화는 별도 공급자 선택·인증/출력 정책 확인·실제 검증이 필요해 의도적으로 비활성이다. available 상태는 fake state 시험만 했고 real 활성화 성공으로 세지 않는다. 원본 앱 통합과 새 디자인 patch와의 최종 회귀는 부모의 freeze 해제 뒤 수행한다.

기존 fal Kling CDN403/후속 token403 및 실청구 기록은 수정하지 않았다. Runway 결과 URL의24–48시간은 링크 만료 안내이며 서버 파일 삭제/본인 전용 ACL이 아니다. 정확한 공식 인용과 원문 명세의 후보 지위, 인증/비용의 최소 결정은 `provider-decision-facts-ko.md`에 따로 적었다.

이번 작업은 추가 provider/API/키를 활성화하지 않았고, 자동 billing 조회를 만들지 않았다. 기존 기록 대조 hook을 유지한다. 200/400% browser zoom, 스크린리더, 실제 고객 사용성, 모든96FR/143API 및38MS-AT 전체 통과는 주장하지 않는다. 단일 사용자 로컬 범위를 다중 사용자 출시 준비로 확대하지 않았다.
