
/* DOM-only integration candidate. Preserve original nodes, IDs, handlers and data. */
(() => {
  if (document.body.classList.contains('lt-workspace-v3')) return;
  const q = s => document.querySelector(s);
  const make = (tag, cls, text) => { const el = document.createElement(tag); if (cls) el.className = cls; if (text) el.textContent = text; return el; };
  const disclosure = (label, cls) => { const d = make('details', cls); d.append(make('summary', '', label)); return d; };
  const main = q('main'), media = q('main>article'), rail = q('main>aside:not(.inspector)'), inspector = q('main>.inspector');
  if (!main || !media || !rail || !inspector) return;
  document.body.classList.add('lt-workspace-v3');

  // A compact shell. Nodes move without changing their save/action semantics.
  const oldHeader = q('body>header'), projectBar = q('.lt-project-bar');
  const shell = make('header', 'lt-studio-shell');
  oldHeader.before(shell);
  const brand = oldHeader.querySelector('b'); shell.append(brand, q('#songs'));
  const management = q('.management');
  management.querySelector('summary').textContent = '작품·설정';
  const modeBar = q('#chatMode').parentElement;
  modeBar.classList.add('lt-mode-switch');
  management.append(modeBar, q('#newProject'));
  const modelButton = q('#editModelSettings');
  const context = disclosure('프로젝트 상태', 'lt-project-context');
  const modelBar = q('#modelDefaultsBar'); modelBar.className = 'lt-model-context';
  context.append(q('#providerBadge'), q('#flowSummary'), modelBar);
  shell.append(management, context, modelButton);
  modelButton.textContent = '모델 설정';
  const stage = make('div', 'lt-stage-bar');
  shell.after(stage);
  stage.append(q('.flow-nav'), q('#flowNext'));
  const heading = q('#flowHeading'); heading.classList.add('lt-stage-heading');
  const status = make('div', 'lt-status-line'); stage.after(status);
  status.append(heading, q('#notice'));
  // Move the existing output actions next to timeline save/version controls.
  const outputActions = make('div', 'lt-output-actions');
  outputActions.append(q('#review'), q('#render'));
  oldHeader.remove(); projectBar.remove(); q('.flow-summary').remove();

  main.classList.add('lt-edit-workspace');
  rail.classList.add('lt-scene-rail'); rail.id = 'ltScenePanel';
  media.classList.add('lt-media-pane'); media.id = 'ltPreviewPanel';
  inspector.id = 'ltReviewPanel';
  const shotHeader = q('#shotTitle').parentElement; shotHeader.classList.add('lt-shot-header');
  const takeRow = make('div', 'lt-take-row');
  q('#preview').after(takeRow); takeRow.append(q('#takes'), q('#compareButton'));
  const download = q('#downloadPreview'); q('#preview').before(download);
  const outputLabel = make('p', 'lt-output-label', '렌더 결과 · 선택 Take와 별도 출력 버전'); download.before(outputLabel);

  // Keep actual timeline data visible; secondary numeric controls are disclosed.
  const timeline = q('.timeline');
  timeline.id = 'ltTimelineDock';
  const timelineHeader = timeline.querySelector('.row'); timelineHeader.classList.add('lt-timeline-header');
  timelineHeader.querySelector('h2').textContent = '타임라인';
  const track = q('#track'), timelineStatus = q('#timelineStatus');
  const controls = disclosure('정밀 편집 · 음원·자막·버전', 'lt-timeline-controls');
  [...timeline.children].filter(n => n !== timelineHeader && n !== track && n !== timelineStatus).forEach(n => controls.append(n));
  timeline.append(timelineHeader, timelineStatus, track, controls);
  timelineHeader.append(outputActions);

  // Inspection starts with the selected Take. Production controls remain separate.
  const reviewSection = q('#takeDecision').closest('section');
  reviewSection.classList.add('lt-take-review');
  reviewSection.querySelector('h2').textContent = '선택 Take 검토';
  inspector.prepend(reviewSection);
  const upload = q('#upload');
  const uploadDetails = disclosure('새 Take 연결', 'lt-inspector-detail');
  upload.before(uploadDetails); uploadDetails.append(upload);
  const reviewRow = q('#takeDecision').parentElement;
  reviewRow.before(q('#reviewReason').closest('label'));
  const reason = q('#reason'); reviewSection.querySelector('h2').after(q('#takeReviewStatus'),reason);
  [...inspector.children].filter(n => n.tagName === 'SECTION' && n !== reviewSection && !n.classList.contains('render-section')).forEach(section => {
    const title = section.querySelector('h2');
    const d = disclosure(title?.textContent || '상세', 'lt-inspector-detail');
    section.before(d); if (title) title.remove(); d.append(section);
    if (section.contains(q('#executionCards'))) { d.classList.add('lt-execution-detail'); d.open = true; }
  });

  // Mobile focuses one working panel, while desktop retains all three columns.
  const panelNav = make('div', 'lt-panel-nav'); panelNav.setAttribute('role', 'tablist'); panelNav.setAttribute('aria-label', '작업 영역');
  main.before(panelNav);
  const panels = [['scenes', '장면', rail], ['preview', '미리보기', media], ['review', '검토', inspector]];
  const mobile = matchMedia('(max-width: 900px)');
  let selected = 'preview';
  function applyPanels() {
    // On small screens keep one shell row; model/state controls stay in the
    // clearly named project disclosure rather than forming more chrome rows.
    if (mobile.matches && context.parentElement === shell) management.append(context, modelButton);
    if (!mobile.matches && context.parentElement === management) shell.append(context, modelButton);
    const focused = !document.body.matches('[data-guided="true"][data-step="1"],[data-guided="true"][data-step="2"]');
    panelNav.hidden = !mobile.matches || !focused;
    panels.forEach(([name, , panel]) => {
      const button = panelNav.querySelector('[data-panel="' + name + '"]');
      const active = name === selected;
      button.setAttribute('aria-selected', String(active)); button.tabIndex = active ? 0 : -1;
      panel.classList.toggle('lt-panel-inactive', mobile.matches && focused && !active);
      if (mobile.matches && focused) { panel.setAttribute('role', 'tabpanel'); panel.setAttribute('aria-labelledby', button.id); panel.tabIndex = 0; }
      else { panel.removeAttribute('role'); panel.removeAttribute('aria-labelledby'); panel.removeAttribute('tabindex'); }
    });
  }
  function choose(name, focusButton = false) {
    selected = name; applyPanels();
    if (focusButton) panelNav.querySelector('[data-panel="' + name + '"]').focus();
  }
  panels.forEach(([name, label, panel], i) => {
    const button = make('button', '', label); button.type = 'button'; button.id = 'ltPanelTab-' + name;
    button.dataset.panel = name; button.setAttribute('role', 'tab'); button.setAttribute('aria-controls', panel.id);
    button.addEventListener('click', () => choose(name));
    button.addEventListener('keydown', event => {
      const keys = { ArrowRight: (i + 1) % 3, ArrowLeft: (i + 2) % 3, Home: 0, End: 2 };
      if (event.key in keys) { event.preventDefault(); choose(panels[keys[event.key]][0], true); }
    });
    panelNav.append(button);
  });
  q('#shotlist').addEventListener('click', event => { if (mobile.matches && event.target.closest('[data-shot]')) choose('preview', true); });
  q('#jobs').addEventListener('click', event => { if (mobile.matches && event.target.closest('[data-play]')) choose('preview', true); });
  // Only mode/stage UI changes are observed. No provider or application-state writes.
  let previousStage = '';
  function stageChanged() {
    const stageKey = document.body.dataset.guided + ':' + document.body.dataset.step;
    if (stageKey !== previousStage) {
      previousStage = stageKey; selected = 'preview';
      management.open = false; context.open = false;
      controls.open = document.body.dataset.step === '4';
      // Only change focus visibility; keep app's original stage handling intact.
      applyPanels();
    }
  }
  new MutationObserver(stageChanged).observe(document.body, { attributes: true, attributeFilter: ['data-guided', 'data-step'] });
  mobile.addEventListener('change', applyPanels); stageChanged();
  // Disclosure dismissal never submits a form or changes project data.
  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape' || q('dialog[open]')) return;
    const opened = [management, context].find(d => d.open && d.contains(document.activeElement));
    if (opened) { opened.open = false; opened.querySelector('summary').focus(); }
  });
})();

