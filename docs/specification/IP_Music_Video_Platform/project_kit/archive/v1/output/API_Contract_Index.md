# 내부 API 계약 목록

외부 공급자 API가 아니다. core는 상세 내부 계약 초안이며 planned는 완성형 계획 경로다. 둘 다 미구현이다. planned의 공통 응답 Resource는 구현 전 자원별 응답 필드를 확정해야 한다. 핵심 비용·승인·작업 계약을 우선 구체화했으며 실제 HTTP 검증은 수행하지 않았다.

| 기능 | 요청 | 권한 | 계약 | 연계 요구 |
|---|---|---|---|---|
| 내 작업공간 목록 | GET /v1/workspaces | membership.read | planned | FR-001 |
| 독립 작업공간 생성 | POST /v1/workspaces | workspace.create | planned | FR-001 |
| 작업공간 조회 | GET /v1/workspaces/{workspaceId} | workspace.read | planned |  |
| 작업공간 설정 변경 | PATCH /v1/workspaces/{workspaceId} | workspace.manage | planned | FR-095 |
| 구성원 목록 | GET /v1/workspaces/{workspaceId}/members | members.read | planned |  |
| 기존 principal을 작업공간에 추가 | POST /v1/workspaces/{workspaceId}/members | members.manage | planned | FR-002 |
| 역할·IP 범위 변경 | PATCH /v1/workspaces/{workspaceId}/members/{memberId} | members.manage | planned |  |
| 접근 권한 철회 | DELETE /v1/workspaces/{workspaceId}/members/{memberId} | members.manage | planned | FR-003 |
| 객체별 세부 권한 부여 | POST /v1/workspaces/{workspaceId}/grants | members.manage | planned | FR-002 |
| 객체 권한 철회 | DELETE /v1/workspaces/{workspaceId}/grants/{grantId} | members.manage | planned | FR-003 |
| 접근 가능한 IP 목록 | GET /v1/workspaces/{workspaceId}/ips | ip.read | planned |  |
| 새 IP 생성 | POST /v1/workspaces/{workspaceId}/ips | ip.manage | core | FR-007 |
| IP 메타데이터 조회 | GET /v1/workspaces/{workspaceId}/ips/{ipId} | ip.read | planned |  |
| IP 메타데이터 수정 | PATCH /v1/workspaces/{workspaceId}/ips/{ipId} | ip.manage | planned | FR-095 |
| 활동기·캠페인 목록 | GET /v1/workspaces/{workspaceId}/ips/{ipId}/eras | ip.read | planned |  |
| 활동기·캠페인 생성 | POST /v1/workspaces/{workspaceId}/ips/{ipId}/eras | ip.manage | planned | FR-009 |
| 세계관 분기 목록 | GET /v1/workspaces/{workspaceId}/ips/{ipId}/branches | knowledge.read | planned |  |
| 고정 스냅샷에서 분기 생성 | POST /v1/workspaces/{workspaceId}/ips/{ipId}/branches | knowledge.manage | core | FR-010 |
| 타입별 엔티티 검색 | GET /v1/workspaces/{workspaceId}/ips/{ipId}/entities | knowledge.read | planned |  |
| 실존자·역할 등 엔티티 후보 | POST /v1/workspaces/{workspaceId}/ips/{ipId}/entities | knowledge.propose | core | FR-008, FR-019 |
| 엔티티의 불변 새 버전 | POST /v1/workspaces/{workspaceId}/entities/{entityId}/revisions | knowledge.propose | core | FR-008 |
| 승인된 관계 타입 조회 | GET /v1/workspaces/{workspaceId}/ips/{ipId}/predicates | knowledge.read | planned |  |
| 타입이 있는 관계 정의 | POST /v1/workspaces/{workspaceId}/ips/{ipId}/predicates | knowledge.manage | planned | FR-019 |
| 범위·분기별 사실 조회 | GET /v1/workspaces/{workspaceId}/ips/{ipId}/assertions | knowledge.read | planned | FR-021 |
| 출처가 있는 사실·관계 후보 | POST /v1/workspaces/{workspaceId}/ips/{ipId}/assertions | knowledge.propose | core | FR-019, FR-036 |
| 사실 수정·retcon 후보 | POST /v1/workspaces/{workspaceId}/assertions/{assertionId}/revisions | knowledge.propose | core | FR-017, FR-024 |
| 대상별 독립 승인 사건 | POST /v1/workspaces/{workspaceId}/approvals | target_specific.approve | core | FR-020, FR-028, FR-041, FR-063, FR-068 |
| 겹치는 사실·관계 충돌 목록 | GET /v1/workspaces/{workspaceId}/ips/{ipId}/conflicts | knowledge.read | planned | FR-022 |
| 충돌을 시간·분기·수정으로 해소 | POST /v1/workspaces/{workspaceId}/ips/{ipId}/conflicts/resolutions | knowledge.approve | planned | FR-022 |
| 승인·후보 취향 규칙 조회 | GET /v1/workspaces/{workspaceId}/ips/{ipId}/preferences | preferences.read | planned |  |
| 근거를 가진 취향 후보 | POST /v1/workspaces/{workspaceId}/ips/{ipId}/preferences | preferences.propose | core | FR-025 |
| 취향 수정·만료·반대 증거 반영 | POST /v1/workspaces/{workspaceId}/preferences/{preferenceId}/revisions | preferences.propose | planned | FR-027, FR-028, FR-076 |
| 검역 업로드 세션 생성 | POST /v1/workspaces/{workspaceId}/uploads | assets.create | core | FR-013, FR-086 |
| 업로드 완료·검사 작업 요청 | POST /v1/workspaces/{workspaceId}/uploads/{uploadId}/complete | assets.create | core | FR-013 |
| 승인 도메인 URL 자료 수집 | POST /v1/workspaces/{workspaceId}/imports/url | assets.create | core | FR-015 |
| 자산 상태·권리·버전 조회 | GET /v1/workspaces/{workspaceId}/assets/{assetId} | assets.read | planned | FR-011 |
| 자산 원본·프록시 버전 목록 | GET /v1/workspaces/{workspaceId}/assets/{assetId}/revisions | assets.read | planned |  |
| 권한 확인 후 짧은 다운로드 URL | POST /v1/workspaces/{workspaceId}/assets/{assetId}/download-links | assets.read | core |  |
| 권리·허용용도·철회 기록 | PATCH /v1/workspaces/{workspaceId}/assets/{assetId}/rights | assets.rights.manage | planned | FR-016 |
| 접근 가능한 곡 목록 | GET /v1/workspaces/{workspaceId}/songs | projects.read | planned |  |
| 음원과 가사 버전 등록 | POST /v1/workspaces/{workspaceId}/songs | projects.create | core | FR-031 |
| 곡과 분석 상태 조회 | GET /v1/workspaces/{workspaceId}/songs/{songId} | projects.read | planned |  |
| 샘플 기준 구간·가사 정렬 | GET /v1/workspaces/{workspaceId}/songs/{songId}/segments | projects.read | planned |  |
| 음원 분석 경계 수동 수정 | PATCH /v1/workspaces/{workspaceId}/songs/{songId}/segments | projects.edit | core | FR-033 |
| 음원 구간·박자·가사 분석 | POST /v1/workspaces/{workspaceId}/songs/{songId}/analysis | production.plan | planned | FR-032 |
| 접근 가능한 프로젝트 목록 | GET /v1/workspaces/{workspaceId}/projects | projects.read | planned |  |
| 곡·분기·출력 목표로 프로젝트 생성 | POST /v1/workspaces/{workspaceId}/projects | projects.create | core | FR-035, FR-037 |
| 프로젝트·현재 버전 조회 | GET /v1/workspaces/{workspaceId}/projects/{projectId} | projects.read | planned |  |
| 프로젝트 메타데이터 변경 | PATCH /v1/workspaces/{workspaceId}/projects/{projectId} | projects.edit | planned |  |
| 권한·시점·출처를 고정한 컨텍스트 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/context-snapshots | projects.edit | core | FR-021, FR-027, FR-045 |
| 실제로 적용한 기억·자산 조회 | GET /v1/workspaces/{workspaceId}/context-snapshots/{snapshotId} | projects.read | core | FR-023, FR-045 |
| 콘셉트·장면 계획 버전 목록 | GET /v1/workspaces/{workspaceId}/projects/{projectId}/plans | projects.read | planned | FR-038 |
| 콘셉트·장면 계획 생성 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/plans | production.plan | core | FR-035, FR-036, FR-038, FR-039 |
| 샷별 키프레임·참조 시트 생성 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/storyboards | production.plan | planned | FR-040 |
| 계획한 용도와 자산 권리 검증 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/rights-checks | projects.edit | planned | FR-068 |
| 문서·실측 상태가 있는 모델 능력 | GET /v1/workspaces/{workspaceId}/model-capabilities | production.plan | core | FR-043 |
| 가격·최소과금·후보 상한 견적 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/estimates | production.generate | core | FR-044 |
| 예산 예약 후 샷 생성 요청 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/generations | production.generate | core | FR-044, FR-046 |
| 기억·자산 변경의 영향 샷 확인 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/impact-preview | projects.edit | core | FR-018, FR-024, FR-053 |
| 승인한 영향 샷만 새 후보 생성 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/regenerations | production.generate | core | FR-053 |
| 지원 모델에서 선택 영역 편집 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/mask-edits | production.generate | planned |  |
| 작업·접수·원가 확인 상태 | GET /v1/workspaces/{workspaceId}/jobs/{jobId} | jobs.read | core | FR-049, FR-052 |
| 재연결 가능한 진행 이벤트 | GET /v1/workspaces/{workspaceId}/jobs/{jobId}/events | jobs.read | core | FR-049 |
| 미제출 중단·지원 시 공급자 취소 | POST /v1/workspaces/{workspaceId}/jobs/{jobId}/cancel | jobs.cancel | core | FR-051 |
| 확인된 실패에 대한 후속 실행 | POST /v1/workspaces/{workspaceId}/jobs/{jobId}/retry | production.generate | core | FR-050, FR-052 |
| 장면·버전 목록 | GET /v1/workspaces/{workspaceId}/projects/{projectId}/shots | projects.read | planned |  |
| 수동 장면 추가 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/shots | projects.edit | planned |  |
| 장면 길이·구도·설정 새 버전 | POST /v1/workspaces/{workspaceId}/shots/{shotId}/revisions | projects.edit | core | FR-039 |
| 후보·실패·원가 목록 | GET /v1/workspaces/{workspaceId}/shots/{shotId}/takes | projects.read | planned | FR-059 |
| 제작 후보 선택과 이유 기록 | POST /v1/workspaces/{workspaceId}/takes/{takeId}/selection | production.approve | core |  |
| 타임라인 버전 목록 | GET /v1/workspaces/{workspaceId}/projects/{projectId}/versions | projects.read | planned | FR-071 |
| 선택 컷·음원·레이어 불변 버전 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/versions | projects.edit | core | FR-047, FR-055, FR-056, FR-057, FR-058, FR-060 |
| 두 버전의 장면·기억·비용 비교 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/version-comparisons | projects.read | planned | FR-041, FR-059 |
| IP·팀 편집 프리셋 목록 | GET /v1/workspaces/{workspaceId}/presets | projects.read | planned |  |
| 검증된 타임라인·자막 프리셋 저장 | POST /v1/workspaces/{workspaceId}/presets | projects.edit | planned | FR-091 |
| 버전별 시간대 검토 목록 | GET /v1/workspaces/{workspaceId}/projects/{projectId}/reviews | review.read | planned |  |
| 시간대 코멘트 작성 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/reviews | review.comment | planned | FR-062 |
| 검토 해결·재개 | PATCH /v1/workspaces/{workspaceId}/reviews/{reviewId} | review.comment | planned | FR-062 |
| 검토 승인·수정 요청 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/review-decisions | review.approve | planned | FR-063 |
| 범위·만료가 있는 리뷰 링크 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/share-links | review.share | planned | FR-061 |
| 리뷰 링크 철회 | DELETE /v1/workspaces/{workspaceId}/share-links/{shareLinkId} | review.share | planned |  |
| 내보내기 이력 | GET /v1/workspaces/{workspaceId}/projects/{projectId}/exports | projects.read | planned |  |
| 승인 버전 렌더·출력 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/exports | production.export | core | FR-047, FR-058, FR-067, FR-092 |
| 출력 파일·검증 상태 | GET /v1/workspaces/{workspaceId}/exports/{exportId} | projects.read | planned | FR-069 |
| 별도 배포 승인 후 납품 사건 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/releases | release.approve | planned | FR-070 |
| 채택·거절 이유·범위 기록 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/feedback | review.comment | core |  |
| 다음 작업을 위한 기억 후보 | GET /v1/workspaces/{workspaceId}/ips/{ipId}/memory-proposals | knowledge.read | planned |  |
| 피드백으로 취향·설정 후보 생성 | POST /v1/workspaces/{workspaceId}/ips/{ipId}/memory-proposals | preferences.propose | planned | FR-026, FR-072, FR-076 |
| 시도·수정시간·기억 효과 분석 | GET /v1/workspaces/{workspaceId}/ips/{ipId}/analytics | analytics.read | planned | FR-030, FR-073, FR-075 |
| 통화별 실제·예약·불명 원가 | GET /v1/workspaces/{workspaceId}/billing/usage | billing.read | planned | FR-073, FR-081, FR-083 |
| 고객 청구와 공급자 원가 계정 | GET /v1/workspaces/{workspaceId}/billing/accounts | billing.read | planned |  |
| 프로젝트·월 사용 한도 변경 | PATCH /v1/workspaces/{workspaceId}/billing/budgets | billing.manage | planned | FR-080 |
| 중복 방지 원장 조회 | GET /v1/workspaces/{workspaceId}/billing/ledger | billing.read | planned | FR-081, FR-083 |
| 접근·승인·변경 감사 | GET /v1/workspaces/{workspaceId}/audit-events | audit.read | planned | FR-005, FR-066, FR-088 |
| 접근 차단과 저장소별 삭제 전파 | POST /v1/workspaces/{workspaceId}/deletion-requests | data.delete | core | FR-006, FR-018, FR-087 |
| 삭제 진행·외부 예외·보존 사유 | GET /v1/workspaces/{workspaceId}/deletion-requests/{deletionRequestId} | data.delete | planned | FR-087 |
| 이동 가능한 IP·프로젝트 묶음 | POST /v1/workspaces/{workspaceId}/data-exports | data.export | planned | FR-069, FR-078 |
| 고객이 범위·시간을 정한 지원 접근 | POST /v1/workspaces/{workspaceId}/support-access | workspace.manage | planned | FR-085 |
| 지원 접근 즉시 철회 | DELETE /v1/workspaces/{workspaceId}/support-access/{supportAccessId} | workspace.manage | planned |  |
| 이동용 타임라인·NLE 교환 가져오기 | POST /v1/workspaces/{workspaceId}/timeline-imports | projects.edit | planned | FR-092 |
| 외부 연결과 권한 목록 | GET /v1/workspaces/{workspaceId}/integrations | integrations.read | planned |  |
| OAuth 외부 연결 시작 | POST /v1/workspaces/{workspaceId}/integrations | integrations.manage | planned |  |
| 외부 연결 토큰·동기화 철회 | DELETE /v1/workspaces/{workspaceId}/integrations/{integrationId} | integrations.manage | planned |  |
| 최소 권한·만료 API 키 생성 | POST /v1/workspaces/{workspaceId}/api-keys | integrations.manage | planned | FR-093 |
| 외부 자동화 키 철회 | DELETE /v1/workspaces/{workspaceId}/api-keys/{apiKeyId} | integrations.manage | planned |  |
| 공급자별 서명 검증 후 원문을 inbox에 저장 | POST /v1/provider-webhooks/{provider} | provider.signature.valid | planned | FR-093 |
| 만료·범위가 있는 구성원 초대 | POST /v1/workspaces/{workspaceId}/invitations | members.manage | planned | FR-002 |
| 수락 전 초대 철회 | DELETE /v1/workspaces/{workspaceId}/invitations/{invitationId} | members.manage | planned |  |
| 조직 제작·보관·승인 정책 | GET /v1/workspaces/{workspaceId}/policies | workspace.read | planned | FR-004 |
| 모델·예산·승인 정책 변경 | PATCH /v1/workspaces/{workspaceId}/policies | workspace.manage | planned | FR-004, FR-094 |
| 조직 소유권 인계 요청 | POST /v1/workspaces/{workspaceId}/ownership-transfers | workspace.transfer | planned | FR-006 |
| 권한·분기·시간 필터가 있는 통합 검색 | POST /v1/workspaces/{workspaceId}/ips/{ipId}/search | knowledge.read | planned | FR-011, FR-023 |
| 다음 프로젝트용 인계 요약 | POST /v1/workspaces/{workspaceId}/ips/{ipId}/handoffs | projects.read | planned | FR-012, FR-066 |
| 중단 업로드의 유효 part·만료 조회 | GET /v1/workspaces/{workspaceId}/uploads/{uploadId} | assets.create | planned | FR-013 |
| 자료에서 근거가 있는 후보 추출 | POST /v1/workspaces/{workspaceId}/assets/{assetId}/extractions | knowledge.propose | planned | FR-014, FR-017 |
| 기억 적용·미적용·새 연출 비교 | POST /v1/workspaces/{workspaceId}/ips/{ipId}/preference-experiments | production.generate | planned | FR-029, FR-030 |
| 멤버 파트와 화면 등장 범위 | PATCH /v1/workspaces/{workspaceId}/songs/{songId}/parts | projects.edit | planned | FR-034 |
| 누락 자료·제작 능력·권리 점검 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/preflight | production.plan | planned | FR-042, FR-086 |
| 기술 결함과 정체성 평가 근거 | GET /v1/workspaces/{workspaceId}/takes/{takeId}/quality-reports | projects.read | planned | FR-048 |
| 조직 한도 안에서 큐 우선순위 | PATCH /v1/workspaces/{workspaceId}/jobs/{jobId}/priority | jobs.manage | planned | FR-054 |
| 작업 초안 자동 저장·충돌 검사 | PATCH /v1/workspaces/{workspaceId}/projects/{projectId}/draft | projects.edit | planned | FR-060 |
| 허용 샷에 대한 외주 작업 배정 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/assignments | review.assign | planned | FR-064 |
| 제출·수락·배정 회수 | PATCH /v1/workspaces/{workspaceId}/assignments/{assignmentId} | review.assign | planned | FR-064 |
| 권한 범위 안의 변경 알림 | GET /v1/workspaces/{workspaceId}/notifications | membership.read | planned | FR-065 |
| 본인 알림 읽음 상태 | PATCH /v1/workspaces/{workspaceId}/notifications/{notificationId} | membership.read | planned |  |
| 승인한 외부 공개를 예약 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/release-schedules | release.publish | planned | FR-070 |
| 아카이브 버전에서 프로젝트 복제 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/clones | projects.create | planned | FR-071 |
| 보류 평가셋으로 모델·기억 검증 | POST /v1/workspaces/{workspaceId}/evaluations | evaluation.manage | planned | FR-074, FR-077 |
| 고객별 기억·학습 허용 정책 | GET /v1/workspaces/{workspaceId}/learning-policy | workspace.read | planned |  |
| 학습·평가 참여·보관 정책 | PATCH /v1/workspaces/{workspaceId}/learning-policy | workspace.manage | planned | FR-078 |
| 플랜·기능·가격 버전 조회 | GET /v1/workspaces/{workspaceId}/billing/plans | billing.read | planned | FR-079 |
| 구독 변경과 권한 적용 요청 | POST /v1/workspaces/{workspaceId}/billing/subscription | billing.manage | planned | FR-079, FR-084 |
| 현재 구독·해지 확정·이용 권한 조회 | GET /v1/workspaces/{workspaceId}/billing/subscription | billing.read | planned | FR-079, FR-084 |
| 실패·중복과금 환불 검토 요청 | POST /v1/workspaces/{workspaceId}/billing/refund-requests | billing.manage | planned | FR-082 |
| 결제사업자 호스팅 결제 세션 | POST /v1/workspaces/{workspaceId}/billing/checkout-sessions | billing.manage | planned | FR-084 |
| 고객 지원 사건 접수 | POST /v1/workspaces/{workspaceId}/support-tickets | membership.read | planned | FR-085 |
| 제어·생성·렌더 상태와 공개 사건 | GET /v1/workspaces/{workspaceId}/service-status | membership.read | planned | FR-054, FR-088, FR-089, FR-090 |
| 템플릿 기반 반복 제작 배치 | POST /v1/workspaces/{workspaceId}/batch-runs | production.generate | planned | FR-091 |
| 검증된 도메인의 기업 인증 설정 | POST /v1/workspaces/{workspaceId}/enterprise-auth | workspace.manage | planned | FR-094 |
| 고급 립싱크·모션·다인물·3D 제작 | POST /v1/workspaces/{workspaceId}/projects/{projectId}/performance-jobs | production.generate | planned | FR-096 |
| 구독 자동갱신 해지·적용 시점 지정 | POST /v1/workspaces/{workspaceId}/billing/subscription/cancel | billing.manage | planned | FR-079, FR-084 |
| 명시적 재동의로 재구독 또는 해지 예약 철회 | POST /v1/workspaces/{workspaceId}/billing/subscription/resubscribe | billing.manage | planned | FR-079, FR-084 |
| 서명 검증된 결제 사건을 저장하고 현재 구독 주기와 대사 | POST /v1/payment-webhooks/{provider} | payment_provider.signature.valid | planned | FR-079, FR-084 |