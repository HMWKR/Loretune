# Design / implementation coordination contract

2026-10-26. Baseline final B HTML SHA256 `a59b8c494770d23000973c1c1b702c39d8fcb955e38ed04f045ccc4c94373c1b`.

## Ownership

- This design task writes only `docs/qa/design-system-redesign-20261026/`.
- Shared app HTML/JS/CSS/backend/server/DB integration belongs to thread `01a170bf-5655-71b3-b6ec-6b2bcfe1a023`.
- Parent coordinates a single merge and frozen release. No concurrent edits to shared source.
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

## Required acceptance packet

- populated desktop with timeline and currently selected object;
- mixed-aspect Take comparison;
- mobile current media + approved review;
- mobile unreviewed or rejected;
- mobile dirty and simulated save error, input retained;
- app text-scale100/150/200 per-role numeric measurements;
- viewport320/390/1280 plus one901/1150 breakpoint boundary;
- keyboard focus and disclosure/dialog return;
- actual browser200/400%, screenreader and live-provider verification only if actually performed, otherwise explicitly unknown.

Report source/served hash, viewport, fixture and simulation provenance for each image. Saving errors/disclosure were corrected in final B; a new failure must be reproduced against the new frozen runtime before being counted again.

## Current boundary

The read-only audit could not open localhost8773 (`ERR_CONNECTION_REFUSED`). This design task will not start or restart it. Source and saved B pixels support requirements; candidate or integrated UI validation remains pending an accessible coordinated runtime.
