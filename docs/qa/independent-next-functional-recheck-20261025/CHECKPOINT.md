# Early checkpoint — 2026-10-25

- Snapshot: 11:47:52 UTC; app/action_assets/model_selection/action_execution/index hashes match the reported 11:40 integration.
- B03 original normal-Store reproduction: both unchanged control and chat-only switch now collect one candidate; reservation settled0; same handoff job retained, foreign-project handoff empty.
- Prior B01/B02 and bridge controls: 16/16; error/savepoint guards2/2; selected non-HTTP regression134/134.
- New independent media/rights cases26/26: real foreign-project-only asset with identical shot/take labels blocked, revoked rights/changed bytes/missing file/symlink/forged rights flags blocked; media input/model/options/price/grant changes blocked; dependency rights/current approval checked; unknown reservation retained after revocation.
- **New F07 (Medium correctness): while a comment save is awaiting its response, editing a second unsent draft succeeds in the input listener but the first request's success deletes the new sessionStorage draft and resets the form.** Exact snapshot JS functions reproduced in Node VM with fake delayed fetch (no browser/server). First submitted text remains first text; newer field becomes empty and storage is empty. `index.html:201,214,254`; evidence `ui-results.json`, `ui_controls.js`.
- F05 original disabled-button bug and F06 original refresh/failed-save/successful-save cases pass. F07 is an adjacent pending-save data-loss case, not a media approval/security failure. Suggested fix: capture submitted draft identity/content and clear/reset only if current scope and draft still match; preserve newer edits.
- No source edits, live/API/key access, listener/server or browser actions. Remaining: F/R relevant regression completion and final scoped report.
