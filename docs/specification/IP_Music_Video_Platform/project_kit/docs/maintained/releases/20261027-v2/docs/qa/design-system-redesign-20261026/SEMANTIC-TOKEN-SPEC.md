# Semantic token consolidation proposal

## Later status clarification — 2026-10-27

The implementation-paused statement below belongs to the earlier documentation checkpoint. Subsequent feature work and the [435-test regression](../codex-workflow-review-20261027/regression-435-20261027.log) are recorded in the [current work record](../codex-workflow-review-20261027/REPORT-ko.md). The old CSS hash remains evidence for its original build, not a fresh token inventory or proof of current visual acceptance.

## 2026-10-27 scope and evidence boundary

**도입 방향 확정, 문서 반영 완료, 구현 미재개.** This update changes documentation only: **no token values, CSS, fonts or component code changed**. The table below retains its recorded candidate/integrated-baseline labels; it is not a freshly computed token inventory. Historical bounded-shell status below is superseded by its dated reports, not rerun here. The last verified CSS is `348e0f0fbe4bdc617ff0d94b7e7a11d4bfd3862df2020312412bc264fa65361b` in the [416 manifest](../chat-model-receipt-display-20261026/polling/FINAL-MANIFEST.json); later session source is partial/unverified.

[AD01–AD07](../../design/AETHONSAAS-ADOPTION-PROPOSAL.md) reuses current semantic roles. aethonSaaS token values/themes are not imported. Map new states before implementation:

|State/component responsibility|Existing role / required distinction|Acceptance, not completed measurement|
|---|---|---|
|Personal draft / selected conversation|quiet surface + text identity, explicit selection marker|No team badge required. Selected is not focus or approval; long CJK/context stays readable|
|Approved/rejected/pending review|review text/status role + non-color cue|Approved may remain calm with no strong CTA. Do not turn every state into a new bordered card|
|Shared candidate / reusable / executable / adopted|explicit permission/action text, progressive disclosure|Do not use one green badge to imply all permissions. ACL behavior is a separate prerequisite|
|Input omitted/unsupported, unknown/failure|warning/error role according to actual consequence, adjacent next action|Unknown is not failure or free cost. Essential reason must not live only inside diagnostics|
|Model/cost/rights at commitment|body/secondary/strong roles according to relevance|Keep actual selection and required commitment facts; raw IDs/hashes remain optional diagnostics|

Role hierarchy remains canvas→panel→raised/interaction, heading/action/body/metadata, selection/focus/review. No second scaling system or append-only theme layer. For any later value change, record actual foreground/background pairs and computed type/spacing at1920/1280, app100/150/200; separately record actual zoom capability. Text4.5:1/large3:1 and essential non-text3:1 apply to required states; decorative dividers are not automatically failures. Keyboard focus visibility, forced-colors/reduced-motion and user text-spacing survival require actual tests, not this table. [New acceptance C04–C07](../../design/AETHONSAAS-ADOPTION-PROPOSAL.md).

Status: maintained design mapping, amended2026-10-26. The original proposal is preserved in `history/initial-design-stage-20261026/SEMANTIC-TOKEN-SPEC.md`. Initial final B `a59b8c49…94373c1b` is historical, not the current release. Integrated baseline values are recorded in `desktop1920/baseline1920-tokens.csv` (CSS f6f9ebff…dd58); new bounded-shell verification is pending. Loretune values are not competitor measurements. See `AMENDMENT-20261026-DESKTOP-METHODOLOGY-ko.md` and `METHODOLOGY-FIT-MATRIX-ko.md`.

## One source of truth

Use one foundation → semantic role → optional component alias chain. Keep token names under one namespace. The existing `--text-scale` handler remains supported; do not add a second unrelated scale. Do not append a ninth overriding theme layer. Integration must remove superseded declarations with a value-preserving diff and verify all main screens.

| Proposed semantic role | Initial candidate value | Baseline / intention |
|---|---|---|
| canvas | `#101010` | preserve |
| chrome / context | `#141414` / `#151515` | distinguish only where useful |
| surface.panel | `#1B1B1B` | review and grouped working surfaces |
| surface.dialog | `#1B1B1B` in integrated baseline | initial `#171717` proposal superseded; dialog separation also uses border/backdrop |
| surface.timeline | `#1B1B1B` in integrated baseline | initial `#191919` proposal superseded; do not revive unused neutrals without a role |
| surface.inset | `#141414` | inputs/model groups |
| media.preview / media.compare | `#050505` / `#080808` | preserve media containment |
| text.strong | `#F4F4F2` | headings and actions |
| text.body | `#DEDEDB` | normal prose/review memo |
| text.secondary | `#BDBDBB` | metadata, no opacity stacking |
| text.disabled | `#A6A6A3` | candidate unified disabled text; check all controls |
| action.primary / on-primary | `#F4F4F2` / `#101010` | only a relevant enabled commitment, not permanent chrome |
| action.secondary / hover / pressed | `#242424` / `#303030` / `#3D3D3D` | lock-aligned raised and hover roles; selection still has an explicit marker |
| action.disabled / edge | `#292929` / `#555555` | no global opacity fade |
| selected.surface / marker | `#2A2A28` / `#D8D8D2` | selection is not approval |
| border.quiet | `#383838` | passive groups/dividers |
| border.control | `#858585` | essential input/control boundary; parent research reports panel4.67:1/hover3.58:1, to remeasure on candidate |
| border.action | `#858585` | when a boundary is needed for identification; not applied to passive groups |
| focus.ring | `#E4DDBE` | same focus role across inputs, buttons, details, links |
| state.approved | text.body + check + word | no extra approving frame |
| state.pending | text.secondary + circle + word | not a loading spinner |
| state.error / surface | `#FFB49D` / `#28201E` | failure/rejected/blocked distinction remains in text |
| state.warning | `#E6C58B` | only actual actionable warning |
| test.text / surface / edge | `#D5D5D1` / `#242424` / `#797977` | one concise test-media badge |

Small neutral differences are not all defects. Consolidate aliases based on component role, not a target count of colors. Preserve independent approval states and disabled explanations. Raw colors may remain in foundations; component use should consume named roles or documented exceptions.

## Typography and scaling

The table below records the initial design roles, not a claim that every value was integrated. The integrated baseline uses12/13/14/16/18/20/24px (meta/item/body/section/context/title/display), body leading1.45 token with base1.5 and memo1.7. Different role values are not automatically defects. New final computed values must be checked at1920 primary/1280 secondary. Original proposal at browser default16px and application100%:

| Role | Size / weight / line-height | Usage |
|---|---|---|
| meta |12px /400 /1.5 | time, media facts, source |
| item |14px /500 /1.45 | rail and Take identity |
| body |14px /400 /1.6 | prose, memo, form values |
| action |14px /500 /1.3 | buttons, short labels, growing height on wrap |
| section |16px /600 /1.5 | grouped content where needed |
| context |18px /600 /1.45 | selected review context when it is the main heading |
| scene |24px /600 /1.25 | desktop current scene; mobile context18px remains |

Define each size with `rem × var(--text-scale,1)`, for example `calc(.875rem * var(--text-scale,1))`. Unitless line-height, expanding control height and wrapping must accompany scale. Do not clamp text to an unscaled maximum. Existing browser font preferences and actual browser zoom remain separate from the application scale control.

Keep `system-ui,-apple-system,"Apple SD Gothic Neo","Noto Sans KR",sans-serif`; no new font download. Use tabular numerals for time/duration. Korean copy uses `word-break:keep-all` with safe long-token overflow wrapping. Do not reduce body/meta size merely to meet first-screen geometry.

## Spacing, shape, motion

- Foundation spacing:4/8/12/16/24/32px (or equivalent rem). Use real references for gaps, component padding and rhythm; do not leave an unused token catalogue. Named optical offsets may use2/6px with an explanation.
- Roles: control padding8×12; panel16; dialog24desktop/16mobile; row gap8; section gap16/24. Desktop compact target36px where content permits, touch44px; existing critical40px actions may stay40px. These product targets are not WCAG's minimum-target criterion. At large text, natural content height wins over a fixed panel height.
- Radius: clip/small4; control/media6; panel8; dialog12; flat divider0. This follows the reference lock's .25/.375/.5/.75rem direction without copying branding. Existing5/10/16px exceptions require a reason or consolidation.
- Border:1px passive/control,2px focus/selected marker. Approval is text+symbol. Do not use a bright outline for every passive card.
- Elevation: none for normal panels; modal `0 16px 48px #0006`; transient popover `0 12px 36px #0008`. Do not add decorative glow/gradient.
- Focus:2px dashed semantic ring, preserve the existing safe3px offset unless a measured native layout needs the lock's2px equivalent. Keep focus distinct from selected and approved. The original finalB source-disclosure solid currentColor exception was already normalized to the semantic dashed ring; do not report it as a current defect without reproduction.
- Motion:120ms for color/border, existing easing `cubic-bezier(.2,0,0,1)`. Reduced-motion removes decorative transition/animation and smooth scrolling. No animation substitutes for truthful progress.
- Icons: retain native controls and labelled symbols; unify custom stroke/glyph dimensions only where existing assets allow. Never introduce an unlabelled ambiguous icon action.

## Migration acceptance

Before integration: enumerate active component mappings and intentional exceptions. After the new freeze: compare computed roles at1920 primary/1280 secondary, app scale100/150/200 and error/disabled/focus/selection states. Additional mobile work is deferred; preserve its existing behavior. Record real FG/BG contrast pairs and live unknowns. The existing19 contrast calculations are baseline evidence, not automatic approval of the candidate.

## Current color-method boundary

Keep the current neutral palette while refining semantic roles. New colors require a concrete task/state reason, foreground/background contrast checks and redundant text/icon cues. OKLCH is an optional color-adjustment tool, not WCAG contrast or Material HCT. No thumbnail-driven dynamic theme or fixed60–30–10 color quota. Neutral chrome does not guarantee color-grading accuracy. Forced-colors must preserve focus/selection without relying only on shadows; reduced-motion removes decorative motion while deliberate media playback remains usable. Source/fit/verification distinctions are in the methodology matrix.


## 2026-10-26 최종 독립 검증 상태

고정된1920 shell의 직접 화면 검토와 실제 토큰/geometry 측정을 완료했습니다. [최종 독립 보고서](desktop1920/final-audit/REPORT-ko.md)와 [항목별평가](desktop1920/final-audit/scorecard.json)를 참조하세요. 이 추가 기록은 기존 제안·과거 검증을 소급 변경하지 않습니다. 기본/sequence/정밀/긴패널/출력의1080px 문서와 상세접근을 확인했고, 실제오류·commit·전체keyboard-only·browserzoom·screenreader는 미검증 범위를 유지합니다. 앱코드와 원본07 아키텍처는 변경하지 않았습니다.
