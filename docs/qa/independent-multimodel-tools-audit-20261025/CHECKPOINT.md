# Early checkpoint — MM01 / P1

Confirmed required-context gap in exact 19-file staged patch SHA256 `44cea955e8f21ac7e62cf440bb80490dc1e3ac30e06c42a04770b964dff65acd`.

`chat_protocols.py:55–60` handoff + `production_tools.py:70–72` search omit current timeline/version/approval ID and unsubmitted media action/plan/grant. `model_selection.py:60–64` emits stable shot UUID, but `fal_dispatch.py:48` resolves `p['shots'][shot]` by human-readable name. All prepare/render tools require those exact identifiers (`production_tools.py:12–19`). No other exposed tool lists them.

Reproduced with actual Store in synthetic temporary DBs: current approved render has timeline 1 + genuine grant, but neither timeline state nor grant is in any initial model context/search; made-up grant is blocked. Approved image action also has no action/grant/plan/name in model context/search. The fake model tests inject these out-of-band via fixture fields.

Evidence: `context-gap.json`; reproduction: `reproduce-context-gap.py` using pinned isolated snapshot in `snapshot.json`. No API, credential, listener, shared source or user DB access.

Minimum fix: expose a server-scoped read-only production-context result (bounded plan/action/approval handles, exact shot identifiers + revision/refs, current EDL/version/render approval, current ontology revision), or server-resolve an explicit current target while maintaining exact immutable grant binding. Internal handles can remain hidden from creator-facing cards. Add a fake workflow using only returned tool/context fields, including after model switch.

Related: MS-FR-02/05/11 (AT03/10/18; their entire acceptance criteria are not claimed tested). This is a concrete incomplete bridge, not a security bypass or a claim that all frontend integration is done.

Independent rerun: 53 focused tests passed with socket connect/bind blocked. Additional adjacent controls still in progress. Reported306 not independently rerun.
