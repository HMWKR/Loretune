# 원문 기준/API 호환 체크포인트 — 13:35 UTC

이 문서가 detailed-qa 인계의 서버/시험 상태를 대체한다. 전체 구현은 계속 필요하다.

1. **서버/UI**: localhost8765 PID62571, exec62359. 최신 운영조회·검증후업로드·실제디코딩·1080p기본·납품검토·두읽기API까지 반영. 새 검증공간2/p1 유지, 사용자공간0미조작. 실제운영5건조회,불량PNG거부와입력보존,1080p출력후별도납품승인,두API실제데이터조회 완료. QA프로젝트외 미디어변경없음.
2. **회귀**: `qa_report.py`46개통과15.007초. Python AST/JS구문검사통과. `browser-cases.json`14건. 최신출력 job6c5a20d2b68b4f1ea08d491c99461b9c: 3초1920×1080/24fps/48kHz/video+audio+subtitle/별도납품승인. 결과JSON을 docs/qa/20261025/render-1080-record.json에 복사했다.
3. **추가발견/수정**: FFprobe가깨진PNG를0크기스트림으로반환해저장한문제. 현재유효크기/샘플레이트/첫프레임또는음원디코딩도검사한다. 처음실패시험에서만들어진 QA T2는사용중지;selected T1유지. assets4개그대로·임시upload폴더0 확인. 이불량QA자산은삭제하지않고근거와함께중지상태보존.

## FR 기능 기준과 출시 게이트

`acceptance_report.py`를 실행해 `criterion-decomposition.json`에96FR의 사전조건/동작/실패/정상수용/반례를 분리했다. **FR067 로컬 기능 기준6개 충족**, 전체출시게이트0. 원문createExport입력·예산·조직권한계약은아직미연결이어서전체API완료로계산하지않는다. `criterion-summary.md`에왜0인지구체설명했다. 다른FR은관련테스트만으로원문전체를통과로올리지않았다.

FR067 추가 구현: 새 프로젝트 기본landscape1080p, UI fresh도프로젝트profile사용, 명시적리사이즈/AI업스케일미지원표시. 로컬delivery_review는렌더완료와별도이고권리·출력hash검사후승인기록. unsupported4k거부·렌더실패시승인timeline보존·모든3프리셋의음원/자막/프레임률검증을test_editing에추가.

## API 변경과 정확한 한계

`contracts.py`의 getJob / listProjectVersions가 원문/v1경로를 지원한다. Store.metadata에영속workspaceUUID, UUID5 project/version IDs를 사용한다. jobrevision이상태변경마다증가한다. 로컬session token을Bearer로전달하고일치하지않으면401;foreignworkspace404;잘못된UUID/페이지400. Job/ResourceList/Error필드와실제HTTP경계를 `tests/test_contracts.py`로검증했다. 실제provider시험아닌합성계약fixture이며조직identity/RBAC/객체grant는아직미구현.따라서2개읽기부분호환이지API전체통과2개가아니다.비용은local_compute미계측이라costStatuspending,허위confirmedCost없음.

`qa_report.py`가143operation별 local_equivalent와 differences(path/schema/errors/permissions/idempotency)를생성한다. `docs/api-contract-coverage.json`두행도부분호환으로수정했다. planned Resource.data의구체도메인스키마와조직권한은남은gate다. write호환은아직없다.

## 남은 로컬 우선 작업

- createExport/estimate/예약원장의원문계약을원자적멱등성·가격버전·예산예약과함께구현. 단순endpoint추가금지.
- 실제계정연결전에도구현가능한tenant/objectgrant모델과격리fixture. 로컬token을조직인증으로표시하지않기.
- 원문FR051의예약해제·늦은콜백,FR059동기A/B,FR060편집초안/충돌복구,FR069재배포권리,삭제/복원정책과접근성전체시험.
- acceptance_report의나머지not verified를기준별실행/근거로채우기. 일부조건met는전체FR승격아님.

## 실제 외부 승인/연결 필요

제공자·모델ID가아직선택/연결되지않음. 실제생성검증요청시보낼합성음원/참고·호출수·최대금액·보관/공개정책범위를구체화해승인받아야한다. 현재키생성/설정·유료호출·결제·배포/push없음. REA추가분석reader_failure/cleanup_incomplete차단유지,프로세스조작없음. 이것이남은로컬구현의차단사유는아니다.
