# fal.ai 계정·키 메타데이터 확인

2026-10-25, 사용자 명시적 승인 후 정상 Aside 브라우저 UI에서 읽기 전용 확인.

- 이전 작업 세션과 fal 탭은 없어 새 Aside 작업 세션에서 같은 브라우저 프로필의 공식 Dashboard를 열었음. 기존 로그인 유지, 추가 로그인 없음.
- 지정 계정과 프로필 일치. 현재 활성 계정은 personal / Owner. Accounts 목록에 별도 팀은 표시되지 않음.
- 같은 활성 계정의 Request History에서 요청 `01a171d6-bf9e-7e72-a8c8-4eb2c5f83b1d`를 열 수 있음.
- 요청 Auth Method의 이름은 API Keys 목록의 한 키 이름과 일치. 해당 키 Access는 `API / All models`.
- 목록에는 `Full access / All models` 등 다른 권한 등급도 표시됨. 다른 키로 전환하거나 사용하지 않음.
- UI 기본 열은 Name, Access, Key ID, Expires, Tags. 이름과 Access만 읽었고 키 값은 reveal/copy하지 않음.
- `API / All models`가 `assets:read`를 포함하는지는 이 화면에 명시되지 않아 미확정. 생성 권한과 자산 읽기 권한의 세부 scope를 구별할 근거 부족.
- .env는 읽지 않았으며 요청에 사용된 로컬 키 값과의 매칭은 수행하지 않음. 이름 일치는 비밀 값 일치 증거가 아님.
- 요청이 이 개인 계정 이력에 보이는 것은 확인했으나 결과 파일 ACL owner와 실제 요청 소유자 ID의 일치까지 확정할 UI 근거 없음.

결론: 다른 팀을 잘못 선택했다는 화면 증거는 발견되지 않았음. API 권한 등급과 자산 읽기 권한의 차이는 가능한 진단 방향이지만 403의 확정 원인이 아님. 원래403은 만료 예상 전에 발생했으며 실제 만료는 확인하지 않음.

지원 문의 질문:
1. 이 요청의 결과 자산 owner가 현재 personal 계정의 principal과 일치하는가?
2. 해당 요청의 API등급 키에 assets:read가 포함되는가? 생성 성공 후 ACL GET403은 scope 부족을 의미하는가?
3. 올바른 계정 Dashboard에서도 재생 오류4 및 Download기록0인 이유와, ACL공개전환/재생성 없이 본인 결과를 회수할 공식 절차는 무엇인가?

추가 생성·결제·키수정·권한변경·ACL변경·Download재클릭 없음. 비밀 값/서명URL/전체 키 목록/계정 개인정보는 이 문서에 포함하지 않음.
