# 공개 근거로 확인한 소유권·호출자 토큰 전달 규칙

## 확정된 계약

`initial_acl: {default: forbid, rules: []}`와3600초만료는fal공식private-to-me예제다. 파일소유자는ACL과무관하게접근가능하므로빈rules를오설정으로판정할근거가없다. human의결과URL직접다운로드와Loretune의private토큰다운로드는별개의지원경로다. 공개fallback은private권한의근본수정이아니다.

출처: https://fal.ai/docs/documentation/model-apis/file-access-controls

## 실제 공개 toolkit 코드

https://github.com/fal-ai/fal/blob/main/projects/fal/src/fal/toolkit/file/providers/fal.py

공개소스 `_caller_cdn_header()`(읽은버전89–97행)는fal현재요청의 `x-fal-cdn-token`과 `request_id`를업로드헤더에전달한다. `_object_lifecycle_headers()`는lifecycle을전달한다. 이는생성자deployment의기본자격증명만으로업로드하는것과caller의정체성/요청범위를전달하는것이다른경로라는코드근거다. **Kling2.6의실제배포가이코드/버전을사용했는지는공개자료로확인하지못했다.**

## 새로 찾은 관련 공개 이슈: Draft PR1136

https://github.com/fal-ai/fal/pull/1136
https://github.com/fal-ai/fal/pull/1136/files

이전검색에서직접관련이슈를못찾았다는보고를보완한다. 공식저장소의2026-08-11 Draft PR `fix(client): adopt the runner's re-scoped CDN token from the queue result`를확인했다. 미병합/배포미확인이다.

PR은중첩fal앱의queue result에서응답헤더의CDN토큰을채택하지않으면내부요청ID로생성된출력에접근범위가미치지않을수있다고설명한다. 변경은결과JSON반환전에 `handle_response_headers(response.headers)`를호출하는것이다. PR본문은이처리가fal app context밖에서는no-op이며일반SDK사용자는영향없다고명시한다. 따라서 **로컬Loretune에그PR을그대로붙이면고쳐진다고결론낼수없다.** 다만Kling서버내부가중첩호출을사용하는지,그경로가scope를보존하는지는fal에확인할구체적질문이됐다.

Loretune `fal_provider.py`73–76행도현재JSON본문만반환하며결과응답헤더를보존하지않는다. 이는관측정보의빈틈이다. 실제응답에해당헤더가있었는지/로컬클라이언트가이를사용해야하는계약인지/현재파일과연결되는지는미확인이다. 토큰추출·decode·헤더신규조회·다운로드재시도는수행하지않았다.

## 계정·팀 표시와 파일 소유권은 별도

공식Teams문서에따르면team API key요청은팀전체에귀속될수있다. Organizations문서는제한된요청보기에서멤버가상태·비용메타데이터는볼수있어도내용접근은달라질수있다고설명한다. 따라서Dashboard200/Cost표시만으로로그인사용자와생성파일소유자의일치를증명하지못한다.

- https://fal.ai/docs/documentation/setting-up/teams
- https://fal.ai/docs/documentation/organizations

현재실제파일owner가caller인지deployment owner인지, CDN token identity가같은팀/주체인지확인한공개자료는없다. 이는계정별사실이므로fal지원또는권한있는Dashboard의비밀없는소유권정보가필요하다. 요청메타데이터를볼수있다는것만으로owner를역추정하지않는다.

## 다음 최소 확인 항목

1. 기존키의발급계정/팀과현재Dashboard선택팀의일치여부, 비밀없는preset/권한목록(특히assets:read/auth:tokens:create). 키값/키ID/토큰을채팅으로받지않는다.
2. fal이requestID `01a171d6-bf9e-7e72-a8c8-4eb2c5f83b1d`의실제CDN object owner와인증주체를대조하고,현재ACL/만료를확인한다.
3. 해당Kling배포의output upload가caller CDN token·requestID·lifecycle을보존했는지,내부queue호출이있다면PR1136과같은scope유실가능성이있는지확인한다.
4. 로컬client에는account token교환이맞는지,특정result response token처리가필요한지fal이명시한다. 필요하다면그계약을근거로fake시험후같은기존파일접근만검증한다.

문서/소스공개열람과로컬코드대조만수행했다. 새키조회/API거절재시도/ACL변경/생성0. 이문서가새로운외부접근권한부여를의미하지않는다.
