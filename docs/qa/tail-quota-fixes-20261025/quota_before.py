from helpers import *
with tempfile.TemporaryDirectory(dir=ROOT) as folder:
 st,call,jid,fake,sha,prep=prepared(folder);gate=deepcopy(st.generation_approval)
 st.generation_approval=None;st.process_generation();st.generation_approval=gate
 sh=st.state()['projects']['synthetic']['shots']['one']
 new=call('prepare_generation',song='synthetic',shot='one',shot_revision=sh['revision'],prompt='synthetic')['preparation']
 try:call('start_generation',song='synthetic',shot='one',preparation=new);error=None
 except ValueError as exc:error=str(exc)
 print(json.dumps(dict(submits=len(fake.calls),old_state=st.generation.get(jid)['state'],new_preparation_blocked=error is not None,error=error),ensure_ascii=False))
 assert error is not None and len(fake.calls)==0
