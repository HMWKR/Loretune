# 의도 정정 독립 재확인 — 2026-10-25

요청한 정정 범위는 **수정 확인 / 새 미해결 항목 없음**으로 닫는다. 제품 전체 준비 완료나 실제 공급자 통합 완료 판정은 아니다.

| 확인 항목 | 판정 | 직접 확인한 근거 |
|---|---|---|
| Runway 활성 선택·실행 제외 | 수정 확인 | `model_selection.py:7–28`에는 chat Anthropic / video fal만 있고 이미지 모델은 없다. 등록되지 않은 선택을 거절한다. `action_execution.py:11,56`의 provider allowlist는 fal 하나다. `runway_provider.py:6–8`은 생성 즉시 거절한다. |
| 대체 이미지 공급자 자동 활성화 방지 | 확인 | `image_pipeline.py:11–20`은 synthetic-local / fixture-image-v1 / contract-fake만 허용한다. `:95`는 job의 원래 connection을 필터링한다. `app.py:725`는 이미지 job을 video worker에서 건너뛴다. 현재 catalog는 이미지 미선택·기존 업로드를 안내한다. |
| 과거 Runway 자료 보존·비활성 표시 | 수정 확인 | `docs/qa/benchmark-provider-correction-20261025/historical-inactive/README.md:3–7`이 잘못 확장했던 과거 프로토타입, 비실행·비배포 자료임을 명시한다. 각 kit `docs/modules/spec-ms-001/20261025/runway-role-decision.md:6`에 최신 사용자 해석이 원문 예시를 대체하며 3개 슬롯·공통 도구 구조는 유지된다고 기록했다. |
| 두 문서 등록부에 SPEC-MS-001, 28FR/38AT | 수정 확인 | 양쪽 `registry/knowledge.json`의 current heads를 해석하여 Document:SPEC-MS-001, Requirement:MS-FR-01…28, Test:MS-AT01…38을 확인했다. 각 kit `catalog.json:7,280`부터 원문 행·제목/기대결과를 대조했다. 원문과 다른 항목은 0이다. |
| 등록을 제품 시험 통과로 오인하지 않음 | 확인 | 각 kit `coverage.json:3–8`을 포함한 전체 38항목 및 실제 Test heads 모두 `not_run / not_fully_verified`, Test verification_level은 `unverified`. Document/FR/AT approval은 `editorial_baseline`이다. local/fake 하위 증거는 별도로 기록됐다. MS-FR-22·28은 `not_implemented`. |
| private + 1시간 | 기존 시험 범위 유지 | `fal_provider.py:20,55–59`는 현재 제한된 fal adapter에 private/3600을 고정하고 `live_launcher.py:20–24`는 10초·1회·$1 이하 및 만료 gate를 요구한다. 현재 adapter 전체에 적용되는 고정값이지만 일반 고객·모든 공급자의 영구 정책으로 등록한 근거는 없다. 범용 정책 설정 기능 완료를 뜻하지 않는다. |
| Anthropic $50 | 기존 시험 범위 유지 | `chat_runtime.py:69–83`의 trials usage journal 누적 cap이다. `:115–121`은 승인된 모델/프로젝트·synthetic_only·문맥/프롬프트 해시를 제한한다. `ledger.py:46–68`의 별도 공급자 예산은 scope별 설정값이다. 모든 고객/공급자의 $50 예산으로 일반화되지 않았다. |

## 스냅샷과 원본 보존

- 캡처: 2026-10-25T14:37:52.053665+00:00. 파일별 mtime, bytes, SHA-256은 [snapshot-manifest.json](snapshot-manifest.json), 보관 원문은 `snapshot/`에 있다.
- 통합 `fixed-release.json`의 20개 source SHA-256과 두 registry SHA-256 모두 일치한다. 종료 시 내용 변경 여부는 [source-drift.json](source-drift.json)에 기록했다.
- 두 registry는 각각 revision 9, objects 1772, current heads 982. 이전 독립 감사 snapshot의 **기존 objects 1666개와 heads 882개의 값이 모두 그대로**다. 새 모듈의 등록 파일 hash도 모두 실제 bytes와 일치한다.
- SPEC-MS-001 원문 및 두 kit 사본 SHA-256: `962f15269eec2367df635209636a2e96baa72a5cc3331647175242a0f8c93378`.
- Master 원문, originals 사본, 이전 감사 snapshot SHA-256: `9ebc6156cea07f13a96974221902eb250ead2098af0999c140345d3f01677913`.
- private/1h 및 $50 관련 네 파일은 이전 독립 의도 감사와 내용 hash가 같다.

## 검증 범위와 남은 제품 작업

독립 실행한 것은 로컬 파일·JSON의 해시/원문행/현재 head/상태/보존 비교다. [verification.json](verification.json)에 실제 결과, [verify-snapshot.py](verify-snapshot.py)에 재현 코드를 보관했다. 스크립트는 source/사용자 DB를 변경하지 않는다. snapshot 파일을 다시 생성하므로 과거 증거를 보존하려면 별도 출력 폴더로 실행한다.

통합 보고서의 **277 tests 통과는 기능 세션의 보고 결과**이며 이번 감사에서 재실행하지 않았다. HTTP, 브라우저, 실제 공급자, 실제 청구, 사용자 DB, 키를 조회하거나 시험하지 않았다. 기존 제한된 Claude live 근거의 실행 자체도 이번에 재검증하지 않았다. 등록부가 그 하위 증거를 전체 MS-AT 통과로 확대하지 않는지를 확인했다.

실제 이미지 adapter 미구현, fal 결과 접근 차단, 전체 38 MS-AT 및 전체 제품 수용시험 미검증은 여전히 제품 작업/검증 한계다. 이번 의도 정정의 새 결함이나 거짓 pass로 분류하지 않는다. 문서 등록부와 앱 IP canonical state는 별도 범위로 유지됐다.

추가 소스 수정·사용자 확인·권한 요청 없이 이 좁은 독립 감사 범위를 종료한다.
