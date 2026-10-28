# 명시적 본인 reader 실제 시험

원래 개인계정의 Personal Profile→Username dltysl123 확인 근거: 부모 승인된 Dashboard 진단,2026-10-25T08:31:18.417Z, https://fal.ai/dashboard/account/details . 이메일/표시이름으로 추정하지 않음.

신규 요청만 default forbid + user dltysl123 allow +3600초. 기존asset ACL은 변경하지 않음. 공식문서상 owner예외는 유지되므로 provider소유자까지 배제했다는 주장은 하지 않음.

원본4423byte PNG/prompt/hash, Kling2.6Pro I2V10초 무음+safety는 종전과 동일. 새승인 scope에1USD budget,0.70 reservation으로 분리하며 이전 실패작업 비용을 지우거나 환불하지 않음. private 통제시험의 별도storage/read 실청구는 미확인. 모델 생성비 예상0.70, 공식가격 재확인. 충전/구매/자동재시도 없음.

시작 전 기존generation_jobs1개(import_blocked),reservation1개 확인. 추가scope없음 확인 후 exclusive one-attempt와DB unique request key로 신규1회만 접수. 현재 전체95테스트pass. actual request ID와상태는status.json. Keys/tokens/signedURLs는보고서에저장안함.

실제시나리오: provider완료 → 인증수신 → 전체decode/길이검증 → 원자파일저장 → Take등록 → 정상범위익명GET차단확인 → 로컬음원/한국어자막합성 → 저장후재시작조회. 단계마다분리판정. 성공해도 명시reader경로의성공이며 provider내부ownership 원인확정아님. production멀티테넌트/다중host/부하는미검증.
