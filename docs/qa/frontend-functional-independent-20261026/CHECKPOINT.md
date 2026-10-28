# 조기 체크포인트

현재고정본 HTML0bfdbbb8…/media65e2468e…에서새P2 3건을controlled VM으로재현. 실제브라우저고객시험이나보안침해를주장하지않음. 소스수정0.

1. **FQ01 · stale poll**: index.html:564. 두poll을시작하고revision3→2순서로응답하면state.revision과채팅렌더가3→2로퇴행. idle에서시작한poll이await중busy/프로젝트전환된뒤에도state를덮음. ASY01/ASY02같은원인으로묶음. 제안:in-flight/sequence+workspace/revision guard,await후busy/context재검사,인과관계가확인된snapshot만적용.
2. **FQ02 · native ended**: studio-media.js:100–108. 무음sequence의3초영상이2.95초RAF이후nativeended(paused=true)에먼저도달하면8초시점에도sequence2.95/일시정지/RAF1. 실제2.975초허용오차조건에서도2.925에멈춤. 제안:현재controller/serial에한정된ended처리및실제source종료기준cut전환/최종pause;임의재생으로stalled상태를숨기지않음. DM01–03재발이아닌별도종료순서증거.
3. **FQ03 · storage denial**: index.html:264,286,312. getItem이SecurityError를던지면startup recovery할당과actguard에서uncaught;요청0이지만graceful사용자안내로가지못함. 제안:storage이용불가를구분하는guarded adapter,미확정기존요청을없음으로간주하지않는fail-closed안내.

기존focusedsnapshot21unittest PASS. 독립VM 13case중9PASS/4FAIL(위3결함). 실제browserfaultinjection/decodedframe/perftrace는미지원으로BLOCKED. 세부최종resultmatrix작성중. 부모는위재현을기능팀에전달가능.
