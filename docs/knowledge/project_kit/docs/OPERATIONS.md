# 프로젝트 문서·근거·변경 운영 가이드

## 1. 이 도구가 관리하는 것

이 키트의 온톨로지는 개발 프로젝트의 지식 구조입니다. 공급자 문서, 시장 주장, 비용 가정, 제품 결정, 요구사항, 화면, API, 시험, 지표, 실험, 사업계획서와 PPT를 연결합니다. 실제 서비스가 고객 아이돌의 얼굴·세계관·활동기·선호를 기억하는 런타임 온톨로지는 별도의 제품 설계입니다. 프로젝트 CLI를 실행했다고 서비스의 지속 기억이나 영상 생성 기능이 구현되지는 않습니다.

파일이 많아질 때 필요한 첫 기능은 자동 요약보다 **현재 기준의 결정, 출처와 주장 분리, 변경의 영향 표시**입니다. 이 도구는 Markdown/JSON과 파일 바이트를 원본으로 사용합니다. Git은 과거 상태와 검토 이력을 보존합니다. 검색은 현재 레지스트리와 제한된 원문을 다시 읽으므로 검색 DB가 없습니다. 나중에 검색 색인을 추가하더라도 원본에서 재생성 가능한 캐시로 취급합니다.

## 2. 실행 환경과 처음 시작하기

Python 3.11 이상이 필요합니다. `argparse`, `json`, `hashlib`, `pathlib`, `unittest` 등 표준라이브러리만 사용합니다. 이 선택은 명령어 파싱·JSON 처리·해시·fixture 시험을 별도 패키지 없이 수행하기 위한 것입니다. Python 공식 문서에 해당 기능이 정의되어 있습니다. [S-P01, S-P02, S-P04, S-P06]

### Windows PowerShell

```powershell
Set-Location 'C:\Projects\ip-music-video\project_kit'
py -3 --version
py -3 kb.py status
py -3 kb.py validate
py -3 -m unittest discover -s tests -p 'test_kb.py' -v
```

`py -3`의 버전이 3.11 이상인지 먼저 확인합니다. `python` 명령이 그 버전으로 연결되어 있다면 아래 예시의 `python`을 그대로 사용해도 됩니다. 파일 경로에는 공백이 있으면 따옴표를 쓰고, 레지스트리에는 `/`로 구분한 프로젝트 상대경로를 저장합니다. 한국어 출력이 깨지는 오래된 콘솔은 UTF-8 환경에서 실행하고, JSON을 ANSI로 다시 저장하지 않습니다.

### macOS / Linux / Unix

```sh
cd '/path/to/project_kit'
python3 --version
python3 kb.py status
python3 kb.py validate
python3 -m unittest discover -s tests -p 'test_kb.py' -v
```

다른 폴더에서 실행할 때는 `python /path/to/project_kit/kb.py --root /path/to/project_kit status`처럼 루트를 명시할 수 있습니다. 생략하면 `kb.py`가 있는 폴더가 루트입니다. 검색 경로를 부모 폴더나 절대경로로 탈출시키는 입력은 거절합니다.

Git 저장소를 처음 만들 때는 자신이 원하는 프로젝트 루트에서 `git init`을 실행하고 원문·레지스트리·코드·운영 문서를 함께 커밋합니다. 이 키트는 원격 저장소를 만들거나 로그인·push·배포하지 않습니다.

## 3. 경로 규칙

| 경로 | 보존 방식 | 기본 문맥 포함 |
|---|---|---|
| `sources/current_spec/` | 전달된 현재 문서의 동결 사본 | 승인 head인 경우만 |
| `archive/v1/` | 이전 문서 사본, 내용 변경 금지 | 제외; 명시 옵션으로 조회 |
| `docs/` | 작성 중 초안과 새로운 버전 | draft는 명시 옵션으로 조회 |
| `registry/` | sidecar 객체·관계·승인 head | 판정의 원본 |
| `generated/context/` | 재생성 가능한 작업별 문맥·receipt | 원문이 아니라 파생물 |
| `tests/` | CLI fixture와 실행 기록 | 제품 실증과 구분 |

`current_spec` 폴더 안이라고 자동 최신 자료가 되지 않습니다. 이미 등록한 파일을 덮어쓰기보다 새 릴리스 디렉터리나 새 버전 파일을 만듭니다. 예를 들어 `sources/current_spec/release_2026-11-01/`에 다음 버전을 두고 그 폴더를 새 namespace로 가져옵니다. 이전 파일 경로와 바이트는 그대로 두고 head만 새 승인 버전으로 바꿉니다.

## 4. 최초 문서와 구조화 카탈로그 등록

`ingest`는 파일을 Document로 등록합니다. `import-catalogs`는 Document 등록에 더해 지원하는 JSON의 실제 FR·SCR·AT·IT·TCH·NFR·MET·EXP·Source·API를 객체와 관계로 가져옵니다. 원래 JSON의 본문을 대량 변경하지 않고 sidecar와 JSON pointer를 추가합니다.

다음 명령은 **빈 registry의 revision 0**부터 시작하는 예시입니다. 이미 통합된 패키지에서는 먼저 `status`로 현재 revision을 확인해야 합니다.

```sh
python kb.py import-catalogs sources/current_spec --namespace SPEC2
python kb.py import-catalogs sources/current_spec --namespace SPEC2 --apply --expected-revision 0 --actor project-maintainer
python kb.py promote --namespace SPEC2 --reason "현재 문서 편집 기준선 검토; 요구 채택·실험 검증과 분리" --apply --expected-revision 1 --actor project-maintainer
python kb.py import-catalogs archive/v1 --namespace SPEC1 --archive
python kb.py import-catalogs archive/v1 --namespace SPEC1 --archive --apply --expected-revision 2 --actor project-maintainer
python kb.py validate
```

`--apply`가 없으면 dry run이며 레지스트리가 변하지 않습니다. 성공한 쓰기마다 revision이 1 증가합니다. 실패하거나 dry run인 경우 증가하지 않습니다. 승인 head가 이미 있는 canonical key의 새 버전을 승격하려면 영향을 먼저 검토한 뒤 `--replace-heads`를 명시합니다.

파일만 등록하려면 `python kb.py ingest docs/business-v3.md --namespace BUSINESS3 --canonical-key Document:business-plan --task business pitch`를 사용할 수 있습니다. 첫 dry run에서 나온 Document ID를 기록하고, 현재 revision을 넣어 등록한 뒤 그 ID를 별도로 승격합니다. `--canonical-key`는 한 파일을 등록할 때만 허용합니다.

OpenAPI는 표준 JSON export의 `.openapi.json`을 파싱합니다. YAML을 읽기 위해 별도 패키지를 설치하지 않으므로 YAML만 있으면 요구서·수용 시험에서 찾은 API 참조를 `reference_only`로 등록합니다. 전체 operation 목록이 필요하면 원본 YAML의 내용과 동등한 OpenAPI JSON을 함께 제공해야 합니다.

## 5. 일상적인 읽기 명령

```sh
python kb.py status
python kb.py freshness --as-of 2026-11-30
python kb.py validate
python kb.py validate --strict
python kb.py search "생성 비용" --task business
python kb.py search "FR-001" --task product
python kb.py search "기억" --full-text --limit 30
python kb.py search "가격" --include-archive
python kb.py search "사업계획" --include-drafts
python kb.py impact FR-001
```

`validate`는 오류가 없으면 종료 코드 0입니다. 해시 불일치·깨진 ID·JSON pointer 불일치·순환 같은 오류가 있으면 1입니다. `--strict`는 재검토 기한 경과 등 경고도 실패로 취급합니다. 잘못된 명령·형식·잠금·revision 충돌은 2입니다. `context-check`는 문맥이 현재와 맞지 않으면 1입니다.

`search`는 기본적으로 승인된 현재 head만 찾습니다. 오래된 승인 자료도 결과에 남을 수 있지만 경고 라벨이 붙습니다. `context`는 이보다 엄격하여 stale 자료를 기본 제외합니다. `--include-archive`, `--include-drafts`, `--include-stale`를 쓴 결과에는 해당 상태가 명시됩니다. 과거 자료를 보려는 것과 현재 근거로 채택하는 것은 다릅니다.

`--full-text`는 제한된 텍스트를 추가 검색합니다. PDF·DOCX·PPTX의 본문 추출이나 OCR을 수행하지 않습니다. 큰 문서의 모든 부분을 검색했다는 보장도 하지 않습니다. 이 파일들은 내용이 대응하는 Markdown/JSON 원문을 연결하고 바이너리 해시로 관리합니다. 외부 URL의 접속 가능성이나 웹페이지의 최신 가격은 이 CLI가 확인하지 않습니다.

## 6. 사업·제품·PPT용 문맥 만들기

```sh
python kb.py context --task business --out generated/context/business-001.md
python kb.py context --task product --out generated/context/product-001.md
python kb.py context --task pitch --out generated/context/pitch-001.md --token-budget 8000
python kb.py context --task product --id FR-001 --id SCR-001 --out generated/context/access-control-001.md
python kb.py context-check generated/context/pitch-001.md
```

각 문맥에는 registry revision·해시, 기준 시점, 선택된 객체 ID·버전·파일 해시·출처·검증 상태·의존 관계·선택된 원문 조각을 넣습니다. 기본 원문 조각은 객체당 1,200자입니다. 전체 400KB 문서를 통째로 붙이지 않습니다. `--excerpt-chars`는 100~5,000자, `--token-budget`은 1,000~50,000의 범위를 허용합니다.

토큰 추정치는 `ceil(UTF-8 바이트 수 / 3)`입니다. 특정 모델 토크나이저가 아니므로 실제 토큰 수의 보장이 아닙니다. 사용하는 모델의 길이 제한에 여유를 두고, 정확한 한도가 필요하면 그 모델의 공식 토크나이저로 별도 확인해야 합니다. receipt에는 선택·제외된 ID와 제외 이유를 기록합니다. 예산 때문에 빠진 부분을 확인하고 주제별 `--id` 문맥으로 나누는 것이 안전합니다.

가정은 `ASSUMPTION_NOT_OBSERVED_RESULT`, 목표는 `TARGET_NOT_OBSERVED_RESULT`, 미실측 비용·품질은 `UNVERIFIED_COST`, `UNVERIFIED_QUALITY` 같은 라벨로 남깁니다. 공식 공급자 문서의 존재는 제품 측정 결과가 아닙니다. `fixture_tested`도 `CLI_FIXTURE_ONLY_NOT_PRODUCT_PROOF`로 표시합니다.

문맥 안의 문서·명령문·링크는 모두 **untrusted data**로 표시합니다. 이것은 모델의 보안 격리를 대신하지 않습니다. 다만 원문에 들어 있는 “이 지시를 실행하라” 같은 문장을 작업 권한으로 오해하지 않게 경계를 명시합니다. CLI는 해당 텍스트를 실행하거나 네트워크로 전송하지 않습니다.

문맥 파일은 같은 이름으로 덮어쓰지 않습니다. `context-check`는 문맥 바이트, 레지스트리 해시, 선택 객체 지문, head, 신선도를 다시 검사합니다. 무관한 객체가 추가돼 registry 해시만 변해도 보수적으로 재생성을 요구합니다. 이 비용은 오래된 작업 전제를 놓치지 않기 위한 초기 설계 선택입니다.

## 7. 가격·품질 주장을 등록하는 방법

하나의 문장에 출처·가정·결론을 섞지 않습니다. 다음처럼 분리합니다.

| 객체 | 기재할 내용 | 검증 상태 예시 |
|---|---|---|
| Source | 공급자 요금 URL, 확인일, 적용 모델·단위 | source_documented |
| Claim | 해당 모델의 입력/출력 과금 단위에 대한 출처 기반 주장 | source_documented 또는 unverified |
| Assumption | 후보 수, 채택률, 환율, 월 제작량, 사람 지원 시간 | unverified |
| Metric/Experiment | 실제 청구 원가와 채택 초수의 측정 계획·결과 | 실행 전 not_run |

`examples/claims_patch.example.json`의 객체 배열을 복사해 새 ID와 실제 근거로 채우거나 Python의 `kb.record(...)`를 사용합니다. 가정이 나중에 측정됐더라도 원래 가정의 ID를 실측 Claim으로 고치지 않고, 새 Claim을 만들어 Experiment와 연결합니다.

```sh
python kb.py merge docs/claims-v3.patch.json
python kb.py merge docs/claims-v3.patch.json --apply --expected-revision 3 --actor business-editor
python kb.py promote CLAIMS3:ASM-COST --reason "가정값의 편집 검토, 실측 아님" --apply --expected-revision 4 --actor business-editor
```

위 숫자는 예시입니다. sidecar의 `status`를 approved로 직접 넣는 것보다 draft로 등록하고 promote의 감사 기록을 남깁니다. `promote`는 decision_state와 verification_level을 바꾸지 않습니다. 로컬 actor 문자열은 본인 확인이나 외부 결재 시스템을 대신하지 않습니다.

## 8. 변경이 발생했을 때

예를 들어 공급자 원가나 후보 수 가정이 바뀌었다면 다음 순서를 따릅니다.

1. 바뀐 Source/Assumption의 기존 ID에 대해 `impact`를 실행해 사업계획·요구사항·지표·PPT의 소비 관계를 확인합니다.
2. 기존 파일을 그대로 보존하고 새로운 파일·레코드를 작성합니다. 실제 가격 확인일과 가정의 유효 시점을 구분합니다.
3. 새 레코드를 dry run으로 merge/ingest하고 현재 revision을 넣어 등록합니다.
4. 변경 이유와 새 근거를 검토한 뒤 새 버전을 `promote ... --replace-heads`로 승격합니다. 이전 버전은 superseded가 됩니다.
5. `validate`와 `impact`에서 하위 문서가 stale로 표시되는지 확인합니다. 새 기준으로 계산·사업 문장·슬라이드를 다시 만들고, 새 산출물의 관계는 새 근거 ID를 가리키게 합니다.
6. 새 사업계획과 새 PPT를 검토·등록·승격합니다. 이전 PPT는 자동으로 수정되거나 배포처에서 회수되지 않습니다.

PPT만 파일로 등록하고 근거와 연결하지 않으면 영향 추적이 약해집니다. Document의 `derived_from` 또는 `documents` 관계에 비용 Claim, 사업 결정, 사용한 요구 버전을 명시합니다. 필요한 경우 슬라이드별 파일이나 작은 Claim 묶음을 별도 Document로 관리합니다. 초기 CLI는 슬라이드 내부 텍스트를 분석해 누락된 의존 관계를 자동 생성하지 않습니다.

원본 JSON의 일부만 바뀌어도 그 컨테이너 해시가 바뀌므로 관련 객체 전체가 보수적으로 stale이 될 수 있습니다. 기존 해시를 자동 갱신해 경고를 없애지 말고, 이전 바이트를 복원하거나 새 버전으로 다시 등록합니다.

## 9. 여러 모델·여러 작업자가 동시에 작업할 때

가장 단순한 운영은 모델마다 다른 초안 파일을 쓰고 한 명의 통합 담당자가 registry를 갱신하는 것입니다. 더 큰 작업은 Git worktree로 별도 분기를 사용합니다. Git 공식 문서는 한 저장소에서 여러 working tree와 분기를 동시에 사용할 수 있음을 설명합니다. 이것이 의미 충돌을 자동 해결한다는 뜻은 아닙니다. [S-P05]

```sh
git worktree add -b work/business ../project-business
git worktree add -b work/product ../project-product
git worktree add -b work/pitch ../project-pitch
```

각 모델은 시작한 commit, registry revision, context receipt를 작업 메모에 남깁니다. 동일 ID를 서로 다른 의미로 바꾸지 않고 새로운 버전 ID를 제안합니다. 통합 담당자는 최신 기준에서 patch를 다시 적용하고 validate·영향 검토를 수행합니다.

동일 로컬 registry에 대한 쓰기는 `knowledge.lock`과 `--expected-revision`으로 보호합니다. 서로 다른 worktree의 잠금은 공유되지 않으므로 Git 통합 단계가 필요합니다. 두 분기의 감사 로그를 단순 병합하면 revision 중복을 탐지하지만, 모든 문장의 의미 충돌을 찾아내지는 않습니다. 최신 분기에서 상대 변경을 새 patch로 재적용해 연속된 감사를 남깁니다.

잠금 파일이 남았으면 기록된 PID와 실제 작업 상태를 확인합니다. 실행 중인 쓰기가 없고 중단된 작업의 결과를 점검한 뒤 **그 잠금 파일 하나만** 운영자가 제거합니다. CLI는 오래됐다는 이유로 잠금을 자동 해제하지 않습니다. 공유 네트워크 드라이브의 다중 작성 서버로 사용하지 않고, 로컬 작업 폴더와 Git 검토를 기본 운영으로 둡니다.

## 10. 보관·대체·복원

`superseded`는 새 기준으로 대체됐다는 의미, `archived`는 일상 작업에서 제외한다는 의미, retention은 파일을 얼마나 보존할지에 대한 정책입니다. archive 명령은 상태만 바꾸고 파일을 옮기거나 삭제하지 않습니다. 현재 head는 바로 archive할 수 없으므로 필요한 대체 기준을 먼저 승인합니다.

```sh
python kb.py archive SPEC1:FR-001 --reason "v2 기준선으로 대체되어 역사 자료로 보존"
python kb.py archive SPEC1:FR-001 --reason "v2 기준선으로 대체되어 역사 자료로 보존" --apply --expected-revision 5 --actor project-maintainer
```

복원은 과거 head를 몰래 가리키게 하는 방식보다 **과거 바이트를 이용한 새 버전**으로 진행합니다. Git의 원하는 commit을 별도 worktree에서 읽고, 필요한 파일만 새 버전 경로로 복사합니다. 예를 들어 `docs/business-restored-v4.md`를 새 namespace와 기존 canonical key로 등록하고, 복원 이유·원래 commit·사용한 근거를 기록한 뒤 승격합니다. 과거 문서의 근거가 현재 만료되거나 대체됐다면 복원한 문서도 새 검토가 필요합니다.

현재 registry가 손상됐다면 작업을 멈추고 사본을 보존합니다. 마지막 정상 Git commit에서 registry와 그 해시가 가리키는 원문을 함께 복원하고 validate를 실행합니다. 이후 누락된 변경은 새 patch로 재적용합니다. 파일 하나만 과거로 되돌린 뒤 전체 상태가 맞다고 가정하지 않습니다.

## 11. 완성된 발표자료를 넘기기 전

사업계획·PPT를 만들 때 사용한 context receipt를 확인하고, 최종본을 기록할 때는 receipt의 사본을 `docs/releases/` 같은 보존 경로에 두어 Git과 함께 관리할 수 있습니다. 생성 디렉터리는 기본 ignore이므로 최종 산출물 근거를 장기 보존하려면 명시적으로 따로 보관합니다.

최종 발표자료에는 가정·실측·공식 문서 설명을 구별합니다. 예산·마진 표는 모델 단가, 과금 초수, 후보 배수, 채택률, 환율, 사람 지원 시간의 버전을 연결합니다. 제품 품질 숫자는 실제 실험 전이면 목표라고 표시합니다. 오래된 근거에 대한 stale 경고가 있는 문서는 검토 완료로 표시하지 않습니다. CLI의 로컬 문서 승격은 외부 게시 허가와 별개입니다.

## 12. 구현·시험 범위

현재 제공된 CLI는 해시 변경, 깨진 객체 관계·JSON pointer, 의존·대체 순환, 현재 head 선택, 검토 기한 전파, 후보 교체에 따른 PPT stale 전파, 문맥 예산과 미검증 라벨, 문맥 receipt 무효화, 동시 writer 충돌, 감사 revision 충돌, 실제 카탈로그 구조 import, 경로 탈출 방지를 포함한 **16개 fixture 시험**을 실제 실행해 통과했습니다. 실행 기록은 `tests/CLI_TEST_REPORT.json`에 있습니다.

이 결과는 Python CLI의 해당 입력·분기에 한정됩니다. 실제 영상 생성, 모델 공급자 요청, 결제, 플랫폼 권한, 사용자 선호 재현, 고객 수요, 실제 제작 원가, 실제 PPT 렌더를 시험하지 않았습니다. 테스트용 `.pptx` 이름 파일은 해시 영향 전파 fixture이며 실제 발표자료 생성 결과가 아닙니다.

초기 도구의 한계는 명시적입니다. 대규모 동시 사용자 서버·인증된 결재·의미 추론·웹 자동 확인·PDF/PPT 본문 분석·완전한 토크나이저·자동 슬라이드 재작성·파일 자동 삭제를 제공하지 않습니다. 필요한 근거를 연결하고, 현재성을 확인하고, 다음 작업의 문맥을 좁혀 만드는 데 집중합니다.

## 기술 근거

- [S-P01] Python argparse: https://docs.python.org/3.11/library/argparse.html
- [S-P02] Python hashlib / SHA-256: https://docs.python.org/3.11/library/hashlib.html
- [S-P03] Python os / O_EXCL / replace: https://docs.python.org/3.11/library/os.html
- [S-P04] Python json / untrusted JSON size guidance: https://docs.python.org/3.11/library/json.html
- [S-P05] Git worktree: https://git-scm.com/docs/git-worktree
- [S-P06] Python unittest: https://docs.python.org/3.11/library/unittest.html

확인일: 2026-10-23. 같은 파일시스템 내 임시 파일 교체는 부분 JSON 노출을 줄이는 구현 수단입니다. `os.replace`의 설명을 모든 OS·네트워크 드라이브의 장애 복구·분산 트랜잭션 보장으로 확대 해석하지 않습니다. [S-P03]
