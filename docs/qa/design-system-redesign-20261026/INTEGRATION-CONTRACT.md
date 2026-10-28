# Design / implementation coordination contract

Current product name: **Aethon**, as explicitly chosen by the user. The existing Loretune path, protocol/storage identifiers and historical evidence remain compatible; visible-brand migration DP26-11 is complete in the UI, startup notice and README.

Updated 2026-10-26 after Aethon integration verification. Frozen HTML `d82ca93a64f31e71bf0c469b1b72b7c59c6a4bbe0403b969881349d8ec82f6e2`, CSS `4c52de6d0f28c5ac1d0259dfa1afe251dc184ebd14802224286c6f41b5db8644`, media JS `ac41a9830a18c9894fdabdf982d1999cc0afa9bf5c613957bc0db7bd9d2832c9`. [Current source/served and cleanup](../codex-cli-assessment-20261026/implementation/FINAL-MANIFEST.json), [implementation report](../codex-cli-assessment-20261026/REPORT-ko.md), [canonical plan](../codex-cli-assessment-20261026/PLAN-ko.md). 350 regressions, 8 current served states, 12 controlled form cases and isolated local synthetic export/reopen are recorded with limits. Both temporary listeners, renderer worker and space42 are closed. Sources remain frozen for the next ontology/session/prompt/motion/editing audit. No new provider calls. Earlier hashes and design results below remain historical evidence.

## Ownership

- This design task writes only `docs/qa/design-system-redesign-20261026/`.
- Shared app HTML/JS/CSS/backend/server/DB integration belongs to thread `01a170bf-5655-71b3-b6ec-6b2bcfe1a023`.
- Parent coordinates a single merge and frozen release. No concurrent edits to shared source.
- Design owns maintained requirements, reference/token specifications, methodology matrix and rubric/index in this folder. Implementation owns implementation/release reports and presentation API contracts; those reports are read-only here.
- The original user-authored07 architecture is not rewritten. Selectable chat/image/video independence, noMCP, fal image/video routing, rights/cost/approval boundaries remain authoritative.
- External research supplied the reference lock recorded in `REFERENCE-LOCK.md`. Existing neutral palette remains the baseline. No new competitor-account actions or live provider use.

## Inputs needed before candidate rendering

1. Research reference lock is received. Keep direct-observation vs captured reference vs official tutorial and measured vs proposed values distinct.
2. Integration source checkpoint/hash and relevant new presentation fields. Do not regenerate from stale B if source changes.
3. Existing approved local synthetic fixture identity. Reuse multi-scene/multi-Take states rather than creating duplicate projects or changing user work.

## Presentation contracts to preserve

| Surface | Existing identity / contract | Presentation work |
|---|---|---|
| Project/steps | `#songs`, stage `data-step`, current context | compact shell, meaningful current-stage state; no project mutation from navigation |
| Current media | `#preview`, current scene/Take | reuse the existing player, retain native controls, contain ratio; no duplicate independent player on mobile |
| Rail/Take | `#shotlist`, `#takes`, `data-shot`, `data-take`, pressed state | one object identity vocabulary, selection marker and separate review symbol/text |
| Review | `#takeReviewStatus`, `#creatorSavedReason`, `#creatorEditReview`, `#creatorReviewEditor`, `#takeDecision`, `#reviewReason`, `#reviewTake`, `#discardTakeReviewDraft` | contextual card/editor; no new permission or review-state logic |
| Draft/save | `takeReviewKey`, scoped store/controller, submitted revision guard, existing receipt lookup | preserve newer drafts and request status. Styling must not force-enable a blocked/unknown request |
| Compare | `#compareDialog`, `#compareLeft`, `#compareRight`, preview slots | equal contain stage, aligned identity/facts, read-only comparison; preserve distinct defaults already fixed |
| Timeline | `#track`, `draft.clips`, numeric edit controls, dirty/save/cancel | true edited-time axis, actual waveform and playhead require the functional contract below. Existing card overview becomes Storyboard. No fake waveform/drag affordance |
| Model/production | existing selected models/readiness/action and result fields | show actual user selection even if unavailable. Keep approval/model/price facts at commitment |
| Output | output request/result, approved input snapshot, music/caption versions | keep output approval separate from Take review. No false live-provider or actual billing claims |
| Scaling/accessibility | `#textScale`, `--text-scale`, native details/dialog, labels/aria | update presentation tokens while preserving the existing change handler and keyboard contracts |

## Planned deliverable sequence

1. Requirements + semantic mapping (this checkpoint; no app patch).
2. Reference lock reconciliation: only resolve evidence-backed choices; do not reopen settled palette or fixed save/disclosure bugs.
3. One bounded candidate patch from the agreed integration baseline. Exact DOM diff plus consolidated CSS, no parallel app edits. Mark every preview as candidate.
4. Functional owner integrates and verifies local regression. Then freeze source/served hash.
5. Design capture of actual integrated packet and independent same-rubric review. No score promise and no additional features merely to raise a number.

## Required functional presentation fields before interactive candidate

- Timeline: clip identity, scene/Take, duration, source trim, composition start/end, sequence duration and current saved/dirty version.
- Playback: preview mode (`sequence` / `selected-shot` / temporary audition), actual clock domain/time, ready/running/paused/ended/error, playable bounds, supported seek/play/pause. Switching preview does not commit a Take or approval.
- Audio: actual measured waveform samples, source time range/sample spacing, offset and analysis availability. Absence must be explicit; no synthesized decorative waveform.
- Poster: actual asset/version identity plus available/pending/unavailable state and safe local image URL. No cross-version stale thumbnail.
- Recovery: existing save/unknown/committed-refresh-failure state and scoped draft guard remain authoritative.

The design task owns labels/layout/tokens and a candidate consuming these fields. The implementation thread owns media timing, transport, sampling, poster extraction and persistence. If a field is not ready, mark the candidate capability as unavailable instead of guessing a backend contract.

## Required acceptance packet — current1920 scope

-1920×1080 CSS viewport/app100: populated approved workspace, sequence/selected preview, precise-edit disclosure open, long inspector content and output view; document scrollHeight≤clientHeight+1 while required controls remain reachable.
- Panel scrolling: record client/scroll height and focused control visibility at both ends; no overflow:hidden-only pass.
- Mixed-aspect comparison and read-only audition; selected/approved/timeline state unchanged.
- Existing unreviewed/rejected state where available; unsaved local dirty→cancel and existing or explicitly labelled mock error. Do not create new approvals or alter user projects to fill a screenshot quota.
- App text-scale100/150/200; reflow is allowed for large text/small windows and must preserve functions. Actual browser200/400%, screenreader and live-provider checks only when performed; otherwise unknown.
-1280×900 secondary regression. Additional320/390 mobile work and new breakpoint sampling are deferred for this pass; preserve existing contracts.
- Source/served hashes, fixture, viewport/DPR and simulation provenance for every capture. Score with the locked7-axis rubric+v1.1 addendum and separate gates/coverage, not the old5-axis score.

Saved errors/disclosure were corrected previously. Count a new defect only after reproduction against the intended frozen runtime.

## Current boundary

The initial read-only token audit encountered ERR_CONNECTION_REFUSED; that was historical and is no longer a current blocker. Subsequent integrated runtime and saved pixels were available and independently inspected. DM01–03 media lifecycle findings were closed by an independent Node VM recheck of JS ae019c88; this does not prove long-running browser sync.

The no-page-scroll shell and subsequent scoped fixes have been implemented and assessed on their dated builds. The latest header batch has exact source/served evidence and is frozen. VF01/VF02 and FQ01–03 are closed by their linked follow-up evidence in INDEX.md; old failure counts remain historical. The current dependency is explanation of the consolidated plan and completion of its explicitly unverified task/state coverage, not reimplementation of the shell. No app/server/database writes, paid calls, account actions, new approvals or media generation are permitted in this design audit.


## 2026-10-26 최종 독립 검증 상태

고정된1920 shell의 직접 화면 검토와 실제 토큰/geometry 측정을 완료했습니다. [최종 독립 보고서](desktop1920/final-audit/REPORT-ko.md)와 [항목별평가](desktop1920/final-audit/scorecard.json)를 참조하세요. 이 추가 기록은 기존 제안·과거 검증을 소급 변경하지 않습니다. 기본/sequence/정밀/긴패널/출력의1080px 문서와 상세접근을 확인했고, 실제오류·commit·전체keyboard-only·browserzoom·screenreader는 미검증 범위를 유지합니다. 앱코드와 원본07 아키텍처는 변경하지 않았습니다.

Maintenance note — 2026-10-26: parent-authorized entrypoint/status correction only. Original findings, rubric, provider boundaries and source ownership remain unchanged. The historical assessment paragraph above applies to its linked build, not the newer header release.
