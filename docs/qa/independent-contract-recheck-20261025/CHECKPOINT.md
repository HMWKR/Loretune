# 독립 재검증 체크포인트

원래 F01–F04 기대값은 새 snapshot에서 모두 충족. 그러나 F04 인접 사례에서 신규 **Medium R01: 승인된 말미 자막/음원 유실을 completed로 게시**하는 반례 재현.

- 정상 Store 경로: 0.131초 컷30개, 요청3.930초, 한국어자막3.920–3.930초, 합성 click3.925초.
- 출력3.916667초. 처음 자막은 남고 마지막 자막은 추출 SRT에서 사라짐, 말미 click peak0.
- `render_job`→`process_next` 결과 **completed**. manifest에는 사라진 끝 자막이 남아있다.
- 파일: media/store-tail-loss.mp4, media/store-tail-loss-manifest.json; 증거 store-media-evidence.json / adjacent-results.json.
- renderer.py:76의 공통 -t를 nearest-rounded video duration으로 잘라 원래 절대시간 음원/자막 말미를 버림. verify_output은 트랙 존재만 확인.
- 수정 제안: 마지막 frame boundary는 승인 audio/caption end를 포함하도록 ceiling 또는 명시적인 trim 검토/거부. 단순 tolerance 조정으로 숨기지 말 것. MS-AT28, FR056/057/067/069.

또한 R02(복구 제약): 미전송 차단으로 reservation cancelled/released인데 all generation_jobs를 합산하는 app.py:436–439 때문에 원래 gate를 복구하고 새 준비를 명시해도 max calls/cost로 거부. zero submit. 과소 허용이며 과금 누출 아님. 승인 범위 정책 명확화 필요.

불명 접수 뒤 철회는 uncertain 예약 유지, 접수 후 철회도 예약 유지. grant 복구만으로 blocked job을 재실행하지 않음. 관계 delete/provenance/restore는 과거 snapshot 보존. HTTP bind 재시도0, 외부호출0, 제품소스변경0.
