# Semantic token consolidation proposal

Status: proposed mapping only, not applied. Baseline final B `a59b8c49…94373c1b`. Exact baseline evidence: `../design-system-audit-20261026/TOKENS.csv`. These are Loretune values, not measured competitor tokens. Reference lock received; decisions are in `REFERENCE-LOCK.md`.

## One source of truth

Use one foundation → semantic role → optional component alias chain. Keep token names under one namespace. The existing `--text-scale` handler remains supported; do not add a second unrelated scale. Do not append a ninth overriding theme layer. Integration must remove superseded declarations with a value-preserving diff and verify all main screens.

| Proposed semantic role | Initial candidate value | Baseline / intention |
|---|---|---|
| canvas | `#101010` | preserve |
| chrome / context | `#141414` / `#151515` | distinguish only where useful |
| surface.panel | `#1B1B1B` | review and grouped working surfaces |
| surface.dialog | `#171717` | existing modal separation |
| surface.timeline | `#191919` | preserve pending visual recheck |
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

Proposed roles at browser default16px and application100%:

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
- Focus:2px dashed semantic ring, preserve the existing safe3px offset unless a measured native layout needs the lock's2px equivalent. Keep focus distinct from selected and approved. Source disclosure currently has a solid currentColor exception; normalize without losing its native keyboard behavior.
- Motion:120ms for color/border, existing easing `cubic-bezier(.2,0,0,1)`. Reduced-motion removes decorative transition/animation and smooth scrolling. No animation substitutes for truthful progress.
- Icons: retain native controls and labelled symbols; unify custom stroke/glyph dimensions only where existing assets allow. Never introduce an unlabelled ambiguous icon action.

## Migration acceptance

Before integration: enumerate active component mappings and intentional exceptions. After integration: compare computed roles at desktop/mobile, app scale100/150/200 and error/disabled/focus/selection states. Record real FG/BG contrast pairs and live unknowns. The existing19 contrast calculations are baseline evidence, not automatic approval of the candidate.
