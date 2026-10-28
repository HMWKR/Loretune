# 순수 시각 관찰표 — 실행 전 추가 고정

2026-10-26. 숫자 합계/새 점수 없음.1920×1080 주,1280×900 보조,모바일 보류.
각 관찰은 `confirmed contract/standard violation` / `visual-task hypothesis` / `missing evidence` / `checked pass`로 분류한다.
작은미디어면적비율·150%소수점px·3:1미만장식선·nativecontrol혼용을자동실패로판정하지않는다.사용자과업영향과증거가필요하다.

1. 레이아웃 geometry·확대
2. 과업별 공간 배분·밀도
3. 그룹·간격·정렬
4. 타입·실제글꼴·CJK·잘림
5. semantic색상·상태대비
6. focus·선택·playhead 동시인지
7. 아이콘 광학정렬·control형태
8. 미디어·timeline aspect/crop/contain
9. surface·overlay·z-index·overflow·CSS일관성
10. 시각회귀 증거 신뢰성

## 추가 자료와 적용 경계

- [Spectrum component spacing](https://spectrum.adobe.com/foundations/layout-and-structure/spacing/component-spacing), [spacing overview](https://spectrum.adobe.com/foundations/layout-and-structure/spacing/spacing-overview): 관계·그룹·정렬 참고. 특정px를표준정답으로강제하지않음.
- [Spectrum typography](https://spectrum.adobe.com/foundations/typography/typography-system), [using icons](https://spectrum.adobe.com/foundations/icons-and-illustrations/using-icons): 역할·광학크기·CJK참고. 실제fontfallback과nativeglyph차이분리.
- [W3C text spacing](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html): 사용자변경시정보/기능보존.기본lineheight강제기준아님.
- [W3C focus not obscured](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html):AA는전체가려지지않음.완전가시는제품기준.
- [W3C focus appearance](https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html):AAA이며AA실패로혼동하지않음.
- [Playwright snapshots](https://playwright.dev/docs/test-snapshots):동일환경·고정콘텐츠·원본보존.변화는미감점수아님.

fixture:기존empty/3scene대표작품;DOM만긴내용;16:9/9:16/1:1은기존Take비교로가능한범위;투명이미지는승인된기존자료없으면NOT RUN.queued/running/partial/failed는functional담당의안전한기존또는격리표본만검사,계정/DB/실행활성화로만들지않음.사용가능한공개browserAPI확인후만조작하며막힌route를숨은API로우회하지않음.
