# 신규 IP 음악영상 플랫폼 — 프로젝트 지식 관리 키트

사업계획·제품 요구서·개발 계약·실험·발표자료가 늘어나도 **어떤 버전이 현재 기준이며, 무엇이 가정이고, 변경이 어디에 영향을 주는지** 추적하는 로컬 도구입니다. 플랫폼 자체나 영상 생성기를 구현한 프로그램은 아닙니다.

Python 3.11 이상과 표준라이브러리만 사용합니다. 별도 `pip install`, DB, 벡터 검색, 그래프 서버, 모델 API 키가 필요하지 않습니다. Git은 버전 관리에 권장하며 CLI 읽기 명령의 실행 의존성은 아닙니다.

## 전달본의 현재 상태

이 배포본은 registry revision 3에 현재 기준 882개와 과거 기록 784개, 총 1,666개 객체를 등록한 상태입니다. 최초 import를 반복하지 않아도 됩니다. `tests/FINAL_INTEGRATION_REPORT.json`과 `tests/LOCAL_TOOL_TEST_REPORT.json`에 실제 통합·시험 결과가 있습니다.

`cost_model.json`은 실행용 사본이고 원가 Claim의 등록된 근거는 `sources/current_spec/models/`의 동결 사본입니다. 새 계산 전제는 `docs/`의 새 config를 `--config`로 사용하고 결과·가정·Claim을 새 버전으로 등록합니다. 등록하지 않은 사본 수정은 현재 승인 근거의 변경이 아닙니다.

## 먼저 실행할 명령

키트 폴더에서 실행합니다. Windows는 `python` 대신 설치된 Python Launcher의 `py -3.11`을 사용할 수 있습니다.

```sh
python kb.py status
python kb.py validate
python kb.py search "비용" --task business
python kb.py impact FR-001
python kb.py context --task pitch --out generated/context/pitch-001.md
python kb.py context-check generated/context/pitch-001.md
```

최초 빈 키트에는 등록 문서가 없습니다. 배포 패키지의 `sources/current_spec/`를 등록한 버전이라면 바로 검색·문맥 생성을 사용할 수 있습니다. 빈 키트의 최초 등록은 아래와 같습니다. `0`, `1`은 예시이므로 이미 등록했다면 `status`에 나온 현재 revision을 사용합니다.

```sh
python kb.py import-catalogs sources/current_spec --namespace SPEC2
python kb.py import-catalogs sources/current_spec --namespace SPEC2 --apply --expected-revision 0 --actor project-maintainer
python kb.py promote --namespace SPEC2 --reason "문서 편집 기준선 검토; 요구 채택과 실험 검증 아님" --apply --expected-revision 1 --actor project-maintainer
```

## 포함 항목

| 경로 | 역할 |
|---|---|
| `kb.py` | 검색·검증·영향 추적·문맥 생성·명시적 등록/승격 CLI |
| `registry/knowledge.json` | 객체·관계·현재 승인 head·감사 기록의 원본 |
| `registry/SCHEMA.md` | 실제 구현과 일치하는 레코드·관계 계약 |
| `docs/OPERATIONS.md` | Windows/Unix, 변경·복원·여러 모델 협업 절차 |
| `examples/claims_patch.example.json` | Source와 가정을 분리한 sidecar 예시 |
| `sources/current_spec/` | 현재 문서의 동결 사본. 폴더 이름만으로 현재성을 판단하지 않음 |
| `archive/v1/` | 이전 문서. 기본 검색·문맥에서 제외 |
| `generated/context/` | 재생성 가능한 문맥과 receipt |
| `tests/test_kb.py` | 프로젝트 CLI에 한정된 16개 fixture 시험 |

`cost_model.py`, `cost_model.json`, `test_cost_model.py`가 함께 제공되면 그 파일들은 별도의 산술 모델입니다. 계산 결과는 실측 공급자 청구나 고객 매출이 아닙니다. 관련 가정과 단가 출처를 레지스트리에서 따로 연결합니다.

## 상태를 읽는 방법

**편집 승인**, **요구 채택**, **실험 검증**은 별개입니다. 현재 문서가 승인됐더라도 제품은 미구현일 수 있습니다. 공급자가 기능을 설명한 공식 문서를 찾았더라도 실제 성공률은 모를 수 있습니다. 비용 계산기가 통과했더라도 실제 채택 영상 1초의 원가는 측정 전입니다.

`validate`는 해시·관계·순환·시점·선언된 검증 근거를 검사합니다. 사업성이 참이라는 판단, 문장의 의미가 옳다는 보증, 외부 웹사이트의 현재 상태 확인, 플랫폼 실행 시험은 수행하지 않습니다.

자세한 운영은 [OPERATIONS.md](docs/OPERATIONS.md), 레코드 형식은 [SCHEMA.md](registry/SCHEMA.md)를 보십시오.
