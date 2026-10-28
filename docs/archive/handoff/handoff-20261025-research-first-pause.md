# 조사 우선 전환 — 구현 중단 인계

2026-10-25. 최신 사용자 지시: 경쟁사 무료 한도 내 심층 UI/UX·동작 조사 전체 완료 → 통합 계획 → 구현. 부모가 조사/계획 완료를 전달하기 전까지 이 실행은 추가 구현·테스트 데이터 변경·서버 변경을 중단하고 읽기 전용 대기한다. 이 문서가 중단 시점 마지막 쓰기다.

## 현재 실행 상태

- 작업 경로 /Users/leesungmin/Desktop/Loretune, Git 저장소 아님.
- 127.0.0.1:8765 Python PID89770 LISTEN을 lsof로 재확인. exec session64945. 최신 백엔드 활성화. 서버 유지, 종료하지 않음.
- SQLite revision38,작품3개. jobs 8b2857ebeb8f48319f1ce680aaedfece 및 4f56279ca5ea4022ae3899180c352493 모두 completed. 대기/진행 작업 없음.
- 실행 중 테스트/검증 명령 없음. Ego Lite space1,p2는 Loretune,p1은 이전 Krea 공개탭. 부모 인계에서 이어받은 공간이며 finish/종료하지 않음.
- .env/.codex 비밀 파일 읽기/수정 없음. 외부 결제·유료생성·push·배포·자격증명/보안 설정 변경 없음.

## 이 실행의 변경

- app.py/loretune.py: 프로젝트별 채팅 지시·줄단위 초안·검토 후 샷 추가, 원래 요청ID 재조회, 로컬 다중IP와 설정스냅샷 분리, 설정 후보/근거/승인/거절/정정경합, 자산 사용중지/재개·이력·큐취소/렌더/다운로드 제한.
- index.html: 동등한 채팅/작업대 진입과 공통 컨트롤·상태, 실제 음원/이미지 업로드·검토·타임라인·렌더 결과 연결, 수동 음악 구간, 파형, 설정후보/IP/사용권 관리, IP·승인take 자산 필터, 출력 준비 안내. IndexedDB에 원래 입력/ID를 저장해 응답유실·전송실패 복구. 저장전 busy 고정으로 연속제출 방지. jobs변경시에만 갱신해 버튼 클릭 방해 방지.
- music.py: 수동 선택구간/구조 버전·출처, 기존편집보존, 실제PCM8kHz모노 간이진폭·최대첫600초·낮은음량 표시. 비트/BPM/AI분석 아님.
- editing.py: 저장된 타임라인 preflight(승인/선택/댓글/음원길이 안내).
- backup.py: 서버종료 상태 해시/SQLite검증 백업, 새폴더만 복원, 자산경로 재배치, 변조/경로이탈/활성job차단. 운영 RPO/RTO/암호화 미검증.
- 새 tests/test_chat.py,test_music.py,test_settings.py,test_ips.py,test_backup.py; 기존 tests/test_app.py,test_editing.py 확장.
- build_matrix.py 및 docs/implementation-matrix.md/json: 부분기능 갱신,전체수용완료0 유지.
- README.md,docs/chat-checkpoint-20261025.md,docs/design-ux-benchmark-ko.md,docs/direct-mv-competitor-extension-ko.md. 직접경쟁사문서는 부모 보고서의 축약 정리본임을 명시.

## 실제 검증

- 최신 전체33개 unittest 통과(12.849초,skip없음). Python 코드 이후 변경 없음. 마지막 JS busy수정은 node --check 통과와 실제 연속submit 대화1회 저장 확인.
- 브라우저: 채팅2장면→검토→샷추가→음원/이미지→take선택/승인→다른샷재사용(승인미상속)→타임라인승인→실제6초MP4. ffprobe video+audio/6.000초. 모드왕복·실제reload 보존.
- 원곡32초 이전 무음/이후톤인 실제음원을 32~47초 렌더,15초길이와 출력초기PCM유음 시험 통과.
- 375/1024/1280/1440 작업대 가로넘침 없음,375/1280캡처 직접검토. 채팅390px도 확인. 전체접근성/성능검증 완료 아님.
- 음악구간99초 오류/0~6초수동저장,기존timeline승인유지. 새음원v2 실제파형표시,타임라인v1음원보존.
- 설정후보UI 저장/승인,검증전용IP생성/선택목록반영.
- 이미지사용중지→기존MP4HTTP403→근거남긴재개→ready복원.
- 응답유실: 실제저장후응답만오류→reload→서버조회복구1회. 전송전단절→reload→원payload/ID재시도1회. 연속제출1회.
- 서버종료 상태 실제data를 /tmp/loretune-backup-20261025-1111로 백업,/tmp/loretune-restored-20261025-1111로 복원.3작품/2job/7자산참조 해시전부유효. 원본보존.
- 검증샘플 작품 '채팅 회귀 검증 1054',IP 'UI 검증 IP 1111',분기 ui-regression-only 추가. 기존 작품은 수정하지 않음. 검증 이미지권리는 재개상태로 복귀.

## 증거와 REA

/tmp/loretune-chat-1054.png,/tmp/loretune-chat-mobile.png,/tmp/loretune-workbench-375.png,/tmp/loretune-workbench-1280.png,/tmp/loretune-waveform.png를 직접 열어 검토했다.

부모 회수자료 /tmp/aside-rea-recovered-nlsd1z2x/reports/rea-public-ui-report.md 읽음. 보고서/파일색인/6스크린샷/REA evidence/매니페스트를 docs/benchmark-evidence/rea-public-ui-20261025/로 보존. MusicMV,BeatViz,Anijam 이미지3개 직접 열어 확인. 설계 반영을 새로 시작하기 전에 최신 중단 지시를 받았으므로 구현하지 않음.

Aside 환경의 mcp__REA__binary_session 6.7.0 성공 및 Evidence요약조회 성공은 해당보고서 근거다. NeuralFrames JS3파일분석은 cleanup_incomplete,workerPID84658 소유권확인오류로 부분실패. 해당프로세스/자원에 조작·종료·재분석 없음. 이 실행의 ALL_TOOLS 재검색에는 REA/binary_session/inspect_analysis_view 0개. 서로 다른 실행환경 상태를 혼동하지 않는다. 5개 경쟁사의 로그인 이후 제작/유료/무료생성 실행은 이 실행에서 하지 않았다.

## 아직 미완료

전체계정/조직/인증/권한·RLS,세계관 관계/취향우선순위,실제AI공급자·예약/원장/결제,143명세API직접호환,물리삭제/외부전파,자동음악/가사/비트,reference역할/첫프레임승인,완전한자동채팅제작,전체접근성/운영/품질평가. 로컬규칙을 AI로 표시하지 않음. 외부가격/크레딧은 실제API원가가 아님.

사용중지는 신규job결과와 신규legacy출력의 참조추적에 적용. 과거legacy출력에는 참조기록 소급미적용. 이미다운로드된 사본의 회수/외부삭제는 지원하지 않음.

다음 행동은 조사·통합계획 완료 후 부모의 재개 통지가 필요하다. 그 전에는 파일/서버/테스트데이터를 변경하지 않는다.
