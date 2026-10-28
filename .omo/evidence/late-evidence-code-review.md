# Late evidence independent code review

- Date: 2026-10-27
- Scope: `ledger.py`, `contracts.py`, `app.py`, `late-evidence-ui.js`, `index.html`, focused tests.
- Status: CLEAR for the scoped code review; recommendation: APPROVE. Actual browser verification remains the parent owner's acceptance step.
- No Git repository or baseline diff was available. Current scoped code and actual tests were reviewed; unrelated changes were not certified.

## Findings

### CRITICAL / HIGH

None established in the reviewed scope.

### MEDIUM — found and resolved in this review

1. **LE-REVIEW-01 — Invalid successful HTTP responses become saved-review claims.** `late-evidence-ui.js:17` swallows JSON parsing errors; `:74–76` ignores the response receipt and locally increments the review revision. A 200 response with truncated JSON displays a saved record without a validated receipt. Reproduction: run the existing Node UI harness with the POST fixture changed to `ok:true,json:async()=>{throw Error('truncated json')}`. The entire harness still passes, including its success-message assertion. Require valid matching id/state/revision or an authoritative reread before success; malformed/mismatched receipts must remain uncertain.

2. **LE-REVIEW-02 — The conflict decision lacks evidence the user can compare.** `ledger.py:74–80` exposes only receipt presence and usage field status. `late-evidence-ui.js:35–43` offers a conflict decision without the observed values or a user-understandable related task. Input usage 12 versus 120000 produces the same visible valid-status explanation. Preserve the compact list, but disclose meaningful safe task/evidence values on explicit detail access, or defer the conflict decision until such information exists. This is not a reason to expose internal identifiers or auto-settle billing.

3. **LE-REVIEW-03 — The stale-project test asserts an absent unrelated label.** `tests/late_evidence_ui.cjs` uses a `chat_usage` fixture while checking that `생성 요청 접수 관측` is absent after the scope changes. That generation label is never rendered by this fixture, so the assertion does not establish stale-response isolation. Use a distinguishable old-project result and assert that it cannot replace current-project content after deferred responses resolve.

### Re-review disposition

- LE-REVIEW-01 resolved: the POST result must match the requested id, decision, and next revision before success. Malformed JSON and mismatched id/decision/revision all retain an uncertain result; tests exercise authoritative reread and an in-flight double-click guard.
- LE-REVIEW-02 resolved for the current narrow workflow: the unsupported conflict-decision button was removed. The remaining action acknowledges seeing the observation and explicitly leaves billing and held budget unchanged. Full invoice/evidence comparison is still not implemented or claimed.
- LE-REVIEW-03 resolved: the test checks the actual chat-usage label and the absence of details after the old-project response arrives.
- Independently reran `node tests/late_evidence_ui.cjs` after all three changes: PASS. No remaining blocker found in the scoped review.

### LOW

No additional confirmed defect. Detail-fetch recovery and native details/focus behavior remain browser-verification targets rather than claimed passes.

## Verified evidence and limits

- Independently executed `PYTHONPATH=tests:. python3 -m unittest test_late_observations_http test_late_evidence_ui -q`: 6 tests, OK. Log: `/tmp/loretune-late-evidence-independent-review.log`.
- HTTP tests exercise bearer and billing permission refusal, cross-project/workspace isolation, keyset pagination, idempotent replay, concurrent stale writes, restart, unchanged unknown attempt/uncertain reservation, and append-only review records.
- The shell post-test command initially used zsh's read-only `status` variable and failed after tests; the complete log was separately read and confirms the test result. No shell failure is represented as a clean command completion.
- No actual supplier request, invoice reconciliation, multi-user authorization proof, or real-browser visual/interaction verification was performed by this reviewer.
- `omo-agent-toolkit ulw-loop status --json` failed because bun and the node fallback were unavailable. This report uses the prescribed fallback evidence path. No toolkit installation or configuration change was made.

## Skill-perspective check

`remove-ai-slops` and `programming` were absent from the active skills catalog and filesystem searches of personal skills and plugin cache. Their prompt-provided criteria were applied manually. The focused HTTP tests verify substantive behavior rather than deletion-only or implementation-constant assertions. LE-REVIEW-03 is a false-confidence/overfit test defect; LE-REVIEW-01 is missing boundary validation where required by the response contract. No needless framework or abstraction was established in this bounded implementation.

## Document gate

Before this report, read-only check returned blocked: one unclassified AI-3D research document and 52 stale-context warnings. After creation, the checker also lists this review report as unclassified. No registration or promotion was performed. The parent should include this report in the subsequent document classification review; this artifact is evidence, not a new source of product authority.
