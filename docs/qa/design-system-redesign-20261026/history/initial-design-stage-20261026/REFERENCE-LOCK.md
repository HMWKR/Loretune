# Accepted reference lock and design decisions

Received from the parent research handoff on2026-10-26. This task did not newly open competitor accounts or measure their internal CSS. References below are **research-session supplied captures / official documents**, not a claim of fresh direct editor access.

| Reference | Adopted role | Explicit exclusions |
|---|---|---|
| [Refero Descript captured editor](https://refero.design/pages/7aaa7dcf-f7e2-4a12-aedf-10ce0576ba87) | common timeline, measured waveform and layer-time alignment | no copied brand colors, no fake beat markers |
| [Refero Frame.io captured editor](https://refero.design/pages/afd4cddd-a493-47c7-9f65-da6b74819871) | real asset/version thumbnail and adjacent player/review | no inference that Loretune already has their collaboration features |
| [Refero Runway captured home](https://refero.design/pages/bc5ff496-55ad-4478-a968-62f7e641b9db) | quiet prompt shell and subordinate metadata | home is not timeline evidence; Runway remains benchmark-only, not API provider |
| Krea/Warp/Runway style references supplied by research | restrained tonal surfaces where compatible | marketing hero, gradients, purple/pink branding and exact internal token claims |
| Existing Loretune final B | neutral media canvas, clear approval separation, native controls | no reset of fixed save/error/disclosure behavior |

## Methodology grounded in evidence

- **Component/state decomposition:** review the same selected object across rail, preview, Take, inspector, Storyboard/timeline and output, rather than rating isolated empty cards.
- **Semantic roles before color choice:** separate content, actions, selection, focus, review outcome and provenance; use actual state text as well as symbols. No color-only approval.
- **Time-domain correctness:** compare clip geometry with edited seconds and real playback, source trim and waveform data. Card size or progress animation is not evidence of timing.
- **Same-task comparison:** identical fixture, media versions, viewport and state before/after; label candidate vs integrated hash.
- **Accessibility as tests, not appearance:** text resizing, focus, keyboard and dragging alternatives are separate checks. Contrast calculations only cover actual paired colors.

Research-supplied official sources:

- [Descript timeline overview](https://help.descript.com/timeline/timeline-overview)
- [Neural Frames editor features](https://help.neuralframes.com/en/articles/8715740-what-do-all-the-features-on-the-video-editor-mean)
- [Runway trimming and assembling clips](https://help.runwayml.com/hc/en-us/articles/52685547867667-Trimming-and-Assembling-Clips-in-Studio)
- [Frame.io iOS player and commenting](https://help.frame.io/en/articles/9105536-commenting-and-the-player-page-on-the-ios-app)
- [W3C resize text](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html)
- [W3C dragging movements](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html)
- [W3C contrast minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)

The prior token audit directly checked W3C contrast guidance. Other documents in this handoff are source references supplied by research; this task does not claim a second independent content or runtime verification.

## Choices for the next candidate

1. Keep canvas#101010, panel#1B1B1B, text#F4F4F2/body#DEDEDB/muted#BDBDBB. Adopt raised#242424 and hover#303030; selected retains its distinct marker.
2. Use proposed#858585 only where a control boundary is required; passive divider#383838 stays quiet. Existing state.error#FFB49D remains. Success/info candidate colors are not introduced without a clear state need; approved remains calm.
3. Consolidate type to12/14/16/18/24 at100%, all scale-aware. Use400/500/600. Preserve a more generous Korean memo line-height1.6–1.7 where the lock's general1.45 would compress review text; no external font dependency.
4. Use real4/8/12/16/24/32 spacing references. Shape direction4clip/6control/8panel/12dialog. Keep enough control height for wrapped Korean; desktop36/touch44 are targets, not fixed clipping boxes.
5. Retain safe focus2px+3px offset unless measurement justifies2px offset. Normalize the disclosure exception without losing Enter/Space/native details behavior. Motion120ms remains within the research120–160 range; reduced-motion removes it.
6. True timeline/real waveform/playhead, separate audition, actual posters and mobile preview+review require explicit functional binding. No visual substitute may imply they are implemented.

Organization target: tokens → base → layout → components → states → responsive. This is a single consolidation pass, not another chain of overriding theme patches. Final pixel quality and functional regression determine acceptance; no numerical score is promised.
