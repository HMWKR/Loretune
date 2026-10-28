/* A single conversation surface follows the workspace and native modal host.
   This module changes presentation only; request journals and consent stay in
   the existing chat and application controllers. */
(() => {
 'use strict';
 if (window.LoretuneAgentSidebar) return;
 const q = selector => document.querySelector(selector);
 const make = (tag, className, text) => { const node = document.createElement(tag); if (className) node.className = className; if (text) node.textContent = text; return node; };
 const MIN_WIDTH = 288, MAX_WIDTH = 600, DEFAULT_WIDTH = 360, MIN_WORK_WIDTH = 580, HANDLE_WIDTH = 12;
 const WIDTH_KEY = 'loretune-agent-sidebar-width-v1';
 const narrow = matchMedia('(max-width: 900px)');
 const workspace = make('div', 'agent-workspace'); workspace.id = 'agentWorkspace';
 const work = make('div', 'agent-work');
 const main = q('main'), planning = q('#chatPanel'), inspector = q('.inspector'), panelNav = q('.lt-panel-nav');
 planning.before(workspace); workspace.append(work); work.append(planning, panelNav, main);
 const sidebar = make('aside', 'agent-sidebar'); sidebar.id = 'agentSidebar'; sidebar.setAttribute('aria-label', 'AI 대화와 검토');
 const handle = make('div', 'agent-resizer'); handle.tabIndex = 0; handle.setAttribute('role', 'separator'); handle.setAttribute('aria-orientation', 'vertical'); handle.setAttribute('aria-label', 'AI 대화와 검토 패널 너비');
 const header = make('div', 'agent-sidebar-header'), tabs = make('div', 'agent-tabs'); tabs.setAttribute('role', 'tablist'); tabs.setAttribute('aria-label', '오른쪽 작업 공간');
 const chatTab = make('button', '', 'AI 대화'), settingsTab = make('button', '', '검토'), close = make('button', 'agent-close', '닫기');
 chatTab.id = 'agentChatTab'; settingsTab.id = 'agentSettingsTab';
 const chat = make('section', 'agent-chat-pane'); chat.id = 'agentChatPane'; chat.setAttribute('role', 'tabpanel'); chat.setAttribute('aria-labelledby', chatTab.id);
 const settings = make('section', 'agent-settings-pane'); settings.id = 'agentSettingsPane'; settings.setAttribute('role', 'tabpanel'); settings.setAttribute('aria-labelledby', settingsTab.id);
 for (const [button, pane] of [[chatTab, chat], [settingsTab, settings]]) { button.type = 'button'; button.setAttribute('role', 'tab'); button.setAttribute('aria-controls', pane.id); tabs.append(button); }
 close.type = 'button'; close.setAttribute('aria-label', '오른쪽 작업 공간 닫기');
 const sizes = make('div', 'agent-width-controls'), narrower = make('button', '', '좁게'), wider = make('button', '', '넓게'); sizes.setAttribute('role', 'group'); sizes.setAttribute('aria-label', 'AI 패널 너비'); narrower.type = wider.type = 'button'; sizes.append(narrower, wider);
 header.append(tabs, sizes, close); sidebar.append(header, chat, settings); workspace.append(handle, sidebar);
 const toggle = make('button', 'agent-toggle', 'AI 대화'); toggle.id = 'agentToggle'; toggle.type = 'button'; toggle.setAttribute('aria-controls', sidebar.id); q('.lt-studio-shell').append(toggle);
 const context = make('p', 'agent-context'); context.id = 'agentContext'; chat.append(context);
 const savedHint = make('p', 'agent-saved-hint', '서버에 저장된 작품·편집을 기준으로 대화합니다.'); chat.append(savedHint);
 const workStatus = make('section', 'agent-work-status'); workStatus.id = 'agentWorkStatus'; workStatus.setAttribute('aria-label', '현재 대화의 제작 작업');
 const workEmpty = make('p', 'agent-setting-note', '저장된 제작 작업 없음'), workDetails = make('details'), workSummary = make('summary'), workSummaryText = make('span'), workRows = make('div');
 workSummaryText.setAttribute('role', 'status'); workSummaryText.setAttribute('aria-live', 'polite'); workSummary.append(workSummaryText); workDetails.append(workSummary, workRows); workStatus.append(workEmpty, workDetails); chat.append(workStatus);
 chat.append(q('#conversationControls'));
 const preferences = make('div', 'agent-preferences-slot'); preferences.id = 'agentPreferencesSlot'; chat.append(preferences);
 const preferenceDetails = make('details', 'agent-preferences'), preferenceSummary = make('summary', '', '에이전트 설정');
 const preferenceForm = make('form', 'agent-preferences-form'); preferenceForm.id = 'agentPreferencesForm';
 const modeLabel = make('label', '', '편집 권한'), modeSelect = make('select'); modeSelect.id = 'agentMode'; modeLabel.htmlFor = modeSelect.id;
 const effortLabel = make('label', '', '추론 강도'), effortSelect = make('select'); effortSelect.id = 'agentEffort'; effortLabel.htmlFor = effortSelect.id;
 const preferenceSave = make('button', '', '에이전트 설정 저장'); preferenceSave.type = 'submit';
 const preferenceHelp = make('p', 'agent-setting-note', '저장해도 모델을 호출하지 않습니다.'); preferenceHelp.id = 'agentPreferencesHelp'; preferenceSave.setAttribute('aria-describedby', preferenceHelp.id);
 const preferenceStatus = make('p'); preferenceStatus.id = 'agentSettingsStatus'; preferenceStatus.setAttribute('role', 'status');
 const preferenceRoute = make('p', 'agent-setting-note'), preferenceActive = make('p', 'agent-setting-note');
 const preferenceScopeNote = make('p', 'agent-setting-note', '편집 권한과 관계없이 최종 출력·비용·전송·사용권 승인은 별도입니다. 계정 삭제는 금지합니다.'); preferenceScopeNote.id = 'agentPreferencesScope'; modeSelect.setAttribute('aria-describedby', preferenceScopeNote.id);
 const preferencePolicy = make('p', 'agent-setting-note', '전체 편집은 허용된 비삭제 편집만 새 미승인 버전으로 저장합니다. 컷 제외·겹침 제거는 검토가 필요하며, 다른 파일 삭제도 대상별 명시 허가가 필요합니다.');
 // D21: chat model token rates, reservation and source at the decision point; secondary detail and the policy note (#46) in one disclosure.
 const preferenceCost = make('p', 'lt-cost-facts'); preferenceCost.id = 'agentSettingsCost';
 const preferenceDetail = make('details', 'lt-provenance-detail'), preferencePrice = make('p', 'agent-setting-note'), preferenceSource = make('a'); preferenceSource.target = '_blank'; preferenceSource.rel = 'noopener noreferrer';
 preferenceDetail.append(make('summary', '', '대화 모델 가격 출처·권한 범위'), preferencePrice, preferenceSource, preferencePolicy);
 preferenceForm.append(modeLabel, modeSelect, preferenceScopeNote, effortLabel, effortSelect, preferenceSave, preferenceHelp, preferenceStatus); preferenceDetails.append(preferenceSummary, preferenceCost, preferenceForm, preferenceRoute, preferenceActive, preferenceDetail); preferences.append(preferenceDetails); preferences.hidden = true;
 const generalHost = make('div', 'agent-general-host'); chat.append(generalHost);
 const legacy = make('details', 'agent-legacy-chat'); const legacyTitle = make('summary', '', '기존 연결 대화 · 별도 실행 이력'); legacy.append(legacyTitle, q('#modelChatPanel')); chat.append(legacy);
 const proposalTitle = make('h2', '', '편집 변경안'); const proposals = make('section', 'agent-proposals'); proposals.setAttribute('aria-label', '편집 변경안 검토'); proposals.append(proposalTitle, q('#timelineProposals')); chat.append(proposals);
 const backToChat = make('button', 'agent-back-to-chat', '대화로 돌아가기'); backToChat.type = 'button'; backToChat.hidden = true; settings.append(backToChat, inspector);
 let opened = !narrow.matches, selected = 'chat', activeDialog = null, drag = null, preferredWidth = DEFAULT_WIDTH;
 const dialogHosts = new Map(), dialogStack = [];
 let preferenceScope = '', preferenceChoices = '';
 let workStatusSignature = '';
 let navigationSequence = 0;
 function workGroups(snapshot, p, name, shot) {
  if (!p) return [];
  const cid = p.active_conversation?.id;
  const visible = j => !!j && (!j.conversation_id || j.conversation_id === cid) && (!j.context?.conversation_id || j.context.conversation_id === cid);
  const local = (snapshot?.jobs || []).filter(j => visible(j) && j.song === name);
  const records = [];
  const localNames = { queued: '대기', running: '진행', completed: '결과 준비', failed: '실패', cancelled: '취소', interrupted: '중단', outcome_unknown: '상태 확인 필요' };
  const providerNames = { prepared: '대기', submitting: '접수 확인 중', accepted: '접수됨', running: '생성 중', result_ready: '결과 수신 대기', downloading: '결과 연결 중', imported: 'Take 연결됨', failed: '실패', submission_blocked: '전송 전 차단', expired: '견적 만료 · 전송 안 됨', reconciliation_required: '접수 확인 필요', import_blocked: '결과 연결 실패', cancel_pending: '취소 전송 대기', cancel_sent: '취소 요청 중', cancelled: '전송 전 취소', cancelled_result: '취소 후 결과 · 검토 필요' };
  function add(key, label, jobs, field, names) {
   if (!jobs.length) return;
   const counts = new Map(), buckets = { active: 0, attention: 0, result: 0, stopped: 0 };
   for (const j of jobs) {
    const value = j[field], text = names[value] || '상태 확인 필요'; counts.set(text, (counts.get(text) || 0) + 1);
    if (['completed', 'imported'].includes(value)) buckets.result++;
    else if (['cancelled', 'interrupted', 'expired'].includes(value)) buckets.stopped++;
    else if (['queued', 'running', 'prepared', 'submitting', 'accepted', 'result_ready', 'downloading', 'cancel_pending', 'cancel_sent'].includes(value)) buckets.active++;
    else buckets.attention++;
   }
   records.push({ key, label, count: jobs.length, summary: [...counts].map(([text, count]) => text + ' ' + count + '건').join(' · '), buckets });
  }
  add('output', '출력', local.filter(j => !j.kind && j.snapshot?.timeline), 'status', localNames);
  add('motion', '선택 장면 모션', local.filter(j => shot && j.kind === 'local-motion' && j.shot === shot), 'status', localNames);
  const scene = (p.scenes_3d || []).find(s => shot && (s.shot === shot || p.shots?.[shot]?.stable_id && s.shot_id === p.shots[shot].stable_id));
  add('scene', '선택 장면 3D', (p.scene_3d_jobs || []).filter(j => visible(j) && scene && j.scene_id === scene.id), 'status', localNames);
  const provider = new Map();
  for (const j of snapshot?.generation_jobs || []) if (visible(j) && j.context?.song === name && shot && j.context.shot === shot && typeof j.id === 'string') provider.set(j.id, j);
  for (const action of p.media_actions || []) if (action.shot === shot && visible(action) && visible(action.job) && typeof action.job?.id === 'string' && !provider.has(action.job.id)) provider.set(action.job.id, action.job);
  add('provider', '선택 장면 AI 미디어', [...provider.values()], 'state', providerNames);
  if (records.at(-1)?.key === 'provider') records.at(-1).jobIds = [...provider.keys()];
  return records;
 }
 function renderWorkStatus() {
  const p = project(), groups = workGroups(state, p, song(), shotName), scope = conversationDraftKey('agent-work-status');
  // D15: provider work rows carry the same model/quote/reason facts as the card for this scene's actions.
  // S16: unit price, kind, sources, revision, expiry and provenance go into one disclosure per row.
  const jobIds = new Set(groups.find(group => group.key === 'provider')?.jobIds || []), priced = (p?.media_actions || []).filter(action => action.shot === shotName && jobIds.has(action.job?.id));
  const facts = priced.map(action => action.shot + ' ' + (action.role === 'video' ? '영상' : '이미지') + ' · ' + mediaFactsLine(action));
  const factDetail = priced.map(action => '<p>' + esc(action.shot + ' ' + (action.role === 'video' ? '영상' : '이미지')) + '</p>' + mediaFactsDetail(mediaFacts(action), true)).join(''), unpriced = jobIds.size - new Set(priced.map(action => action.job.id)).size;
  const signature = JSON.stringify([scope, groups, facts, factDetail]); if (signature === workStatusSignature) return;
  workStatusSignature = signature; workStatus.hidden = !p; workEmpty.hidden = groups.length > 0; workDetails.hidden = !groups.length;
  const counts = groups.reduce((all, group) => { for (const key in all) all[key] += group.buckets[key]; return all; }, { active: 0, attention: 0, result: 0, stopped: 0 });
  const parts = [[counts.active, '진행'], [counts.attention, '확인 필요'], [counts.result, '결과 준비'], [counts.stopped, '취소·중단·만료']].filter(([count]) => count).map(([count, label]) => label + ' ' + count + '건');
  workSummaryText.textContent = '제작 작업 · ' + parts.join(' · ');
  const focusedKey = workRows.contains(document.activeElement) ? document.activeElement.dataset.agentWork : null;
  workRows.replaceChildren();
  for (const group of groups) { const row = make('div', 'agent-work-row'), text = make('p', '', group.label + ' · ' + group.summary), button = make('button', '', '작업 보기'); button.type = 'button'; button.dataset.agentWork = group.key; button.setAttribute('aria-label', group.label + ' 작업 보기'); button.title = '입력은 보존하고 기존 제작 작업 화면에서 확인합니다.'; row.append(text, button); if (group.key === 'provider') { for (const line of facts) row.append(make('p', 'lt-cost-facts', line)); if (unpriced > 0) row.append(make('p', 'agent-work-note', '준비 기록이 없는 작업 ' + unpriced + '건은 가격 정보를 표시하지 않습니다.')); if (factDetail) { const detail = make('details', 'lt-provenance-detail'); detail.innerHTML = '<summary>가격·출처 상세</summary>' + factDetail; row.append(detail); } } workRows.append(row); }
  if (focusedKey) workRows.querySelector('[data-agent-work="' + focusedKey + '"]')?.focus({ preventScroll: true });
 }
 function focusWorkTarget(target) {
  if (!target) return;
  for (let parent = target.parentElement; parent; parent = parent.parentElement) if (parent.tagName === 'DETAILS') parent.open = true;
  if (!target.getClientRects().length) return;
  target.tabIndex = -1; target.focus({ preventScroll: true }); target.scrollIntoView({ block: 'center' });
 }
 function viewWork(key) {
  if (!workGroups(state, project(), song(), shotName).some(group => group.key === key)) return;
  const sequence = ++navigationSequence;
  const desiredDialog = key === 'motion' ? q('#motionDialog') : key === 'scene' ? q('#sceneStudioDialog') : null;
  const target = () => {
   if (key === 'output') return q('#jobs');
   if (key === 'motion') return q('#motionJobs');
   if (key === 'scene') return q('#sceneStudioJobs');
   if ((project()?.media_actions || []).some(action => action.shot === shotName && action.job)) return q('#mediaActionCards');
   const video = (state?.generation_jobs || []).some(job => job.context?.song === song() && job.context.shot === shotName && job.context.output_kind !== 'image' && job.context.dispatch !== 'fal-model-queue-v1');
   return q(video ? '#generationPreparations' : '#imageRecoveryJobs');
  };
  if (activeDialog && activeDialog === desiredDialog) { focusWorkTarget(target()); return; }
  const scope = conversationDraftKey('agent-work-status');
  const closing = [...dialogStack].reverse().filter(dialog => dialog.open);
  const closed = closing.map(dialog => new Promise(resolve => dialog.addEventListener('close', resolve, { once: true })));
  for (const dialog of closing) dialog.close();
  // Existing modal close handlers persist drafts and return focus to launchers.
  // Complete that lifecycle before giving the requested work card focus.
  Promise.all(closed).then(() => {
   syncDialogs(); if (sequence !== navigationSequence || scope !== conversationDraftKey('agent-work-status')) return;
   setStep(key === 'output' ? 4 : 3);
   // Let the original stage/mobile controllers settle before selecting review.
   queueMicrotask(() => {
    if (sequence !== navigationSequence || scope !== conversationDraftKey('agent-work-status')) return;
    choose('settings');
    if (desiredDialog) { const launcher = key === 'motion' ? q('#motionButton') : q('#sceneStudioButton'); if (!launcher || launcher.disabled) return; launcher.click(); syncDialogs(); }
    focusWorkTarget(target());
   });
  });
 }
 // Returns 'opened' or a reason: superseded (newer navigation/conversation, stay silent),
 // missing (target gone), dirty (unsaved edit on another scene), blocked (screen did not reach the card).
 async function reviewMediaAction(id, scope, stillCurrent) {
  const sequence = ++navigationSequence;
  const check = () => {
   if (sequence !== navigationSequence || scope !== conversationDraftKey('general-chat')) return 'superseded';
   const p = project(), actions = (p?.media_actions || []).filter(action => action.id === id);
   if (typeof stillCurrent !== 'function' || !stillCurrent() || actions.length !== 1 || !['image', 'video'].includes(actions[0].role) || !p.shots?.[actions[0].shot]) return 'missing';
   return dirty && actions[0].shot !== shotName ? 'dirty' : actions[0];
  };
  const shotButton = shot => { const buttons = [...document.querySelectorAll('#shotlist [data-shot]')].filter(button => button.dataset.shot === shot); return buttons.length === 1 && !buttons[0].disabled ? buttons[0] : null; };
  // Verify the scene control before closing dialogs or changing the step so a failure leaves the screen as it was.
  let action = check(); if (typeof action === 'string') return action;
  if (action.shot !== shotName && !shotButton(action.shot)) return 'blocked';
  const closing = [...dialogStack].reverse().filter(dialog => dialog.open);
  const closed = closing.map(dialog => new Promise(resolve => dialog.addEventListener('close', resolve, { once: true })));
  for (const dialog of closing) dialog.close();
  await Promise.all(closed); syncDialogs();
  action = check(); if (typeof action === 'string') return action; if (activeDialog) return 'blocked';
  setStep(3, { focus: false }); await Promise.resolve();
  action = check(); if (typeof action === 'string') return action; if (activeDialog) return 'blocked';
  // The flag tells the mobile shot listener to switch panels without taking focus; only the card is focused.
  if (action.shot !== shotName) { const button = shotButton(action.shot); if (!button) return 'blocked'; button.dataset.reviewNavigation = ''; try { button.click(); } finally { delete button.dataset.reviewNavigation; } }
  await Promise.resolve();
  action = check(); if (typeof action === 'string') return action; if (action.shot !== shotName || activeDialog) return 'blocked';
  const cards = [...document.querySelectorAll('[data-action-card]')].filter(card => card.dataset.actionCard === id);
  if (cards.length !== 1) return 'blocked';
  choose('settings'); focusWorkTarget(cards[0]);
  // The chat pane is hidden now; return to it so the failure text and button focus are reachable.
  if (!cards[0].getClientRects().length || document.activeElement !== cards[0]) { choose('chat'); return 'blocked'; }
  cards[0].dataset.reviewArrival = ''; cards[0].addEventListener('blur', () => { delete cards[0].dataset.reviewArrival; }, { once: true });
  return 'opened';
 }
 // S8: open a saved 3D (Scene Studio) or motion proposal from chat. Same scoping, dirty protection and
 // sequencing as reviewMediaAction; the studio keeps unsaved dialog input ('kept') instead of replacing it.
 async function reviewStudioProposal(kind, id, scope, stillCurrent) {
  const sequence = ++navigationSequence;
  const launcher = () => q(kind === 'scene' ? '#sceneStudioButton' : '#motionButton');
  const studio = () => kind === 'scene' ? window.AethonScene : window.AethonMotion;
  const check = () => {
   if (sequence !== navigationSequence || scope !== conversationDraftKey('general-chat')) return 'superseded';
   const p = project();
   const shots = kind === 'scene' ? (p?.scenes_3d || []).filter(record => (record.proposals || []).some(item => item.id === id)).map(record => record.shot) : (p?.motion_proposals || []).filter(item => item.id === id).map(item => item.shot);
   if (typeof stillCurrent !== 'function' || !stillCurrent() || shots.length !== 1 || typeof shots[0] !== 'string' || !p.shots?.[shots[0]]) return 'missing';
   return dirty && shots[0] !== shotName ? 'dirty' : shots[0];
  };
  const shotButton = shot => { const buttons = [...document.querySelectorAll('#shotlist [data-shot]')].filter(button => button.dataset.shot === shot); return buttons.length === 1 && !buttons[0].disabled ? buttons[0] : null; };
  let shot = check(); if (shot === 'superseded' || shot === 'missing' || shot === 'dirty') return shot;
  if (shot !== shotName && !shotButton(shot)) return 'blocked';
  const closing = [...dialogStack].reverse().filter(dialog => dialog.open);
  const closed = closing.map(dialog => new Promise(resolve => dialog.addEventListener('close', resolve, { once: true })));
  for (const dialog of closing) dialog.close();
  await Promise.all(closed); syncDialogs();
  const again = () => { const value = check(); return ['superseded', 'missing', 'dirty'].includes(value) ? value : activeDialog ? 'blocked' : null; };
  let stop = again(); if (stop) return stop;
  setStep(3, { focus: false }); await Promise.resolve();
  stop = again(); if (stop) return stop;
  if (shot !== shotName) { const button = shotButton(shot); if (!button) return 'blocked'; button.dataset.reviewNavigation = ''; try { button.click(); } finally { delete button.dataset.reviewNavigation; } }
  await Promise.resolve();
  stop = again(); if (stop) return stop; if (check() !== shotName) return 'blocked';
  const open = launcher(); if (!open || open.disabled || typeof studio()?.reveal !== 'function') return 'blocked';
  // From here to reveal() nothing awaits, so no newer navigation can interleave.
  choose('settings'); open.click(); syncDialogs();
  const shown = studio().reveal(id);
  if (shown !== 'opened' && shown !== 'kept') return shown === 'missing' ? 'missing' : 'blocked';
  const target = q(shown === 'kept' ? (kind === 'scene' ? '#sceneStudioStatus' : '#motionStatus') : (kind === 'scene' ? '#sceneStudioSummary' : '#motionProposal'));
  if (!target) return 'blocked';
  focusWorkTarget(target);
  if (document.activeElement !== target) return 'blocked';
  target.dataset.reviewArrival = ''; target.addEventListener('blur', () => { delete target.dataset.reviewArrival; }, { once: true });
  return shown;
 }
 workRows.addEventListener('click', event => { const button = event.target.closest('[data-agent-work]'); if (button) viewWork(button.dataset.agentWork); });
 const modeNames = { read_only: '읽기 전용', review: '검토 후 편집', full_access: '전체 편집' };
 const effortNames = { none: '없음', minimal: '최소', low: '낮음', medium: '보통', high: '높음', xhigh: '매우 높음', max: '최대' }, effortName = value => effortNames[value] || value;
 function renderPreferences(p) {
  const prefs = p?.agent_preferences, current = prefs?.current, cap = prefs?.capabilities?.models?.[current?.selection];
  preferences.hidden = !current?.selection || !cap;
  if (preferences.hidden) return;
  const choices = JSON.stringify([prefs.capabilities.modes, cap.effort_options, cap.unsupported_efforts]);
  if (choices !== preferenceChoices) {
   preferenceChoices = choices; modeSelect.replaceChildren(); effortSelect.replaceChildren();
   for (const mode of prefs.capabilities.modes) { const option = make('option', '', modeNames[mode.id] || mode.label); option.value = mode.id; modeSelect.append(option); }
   for (const value of cap.effort_options) { const option = make('option', '', effortName(value)); option.value = value; effortSelect.append(option); }
   for (const item of cap.unsupported_efforts || []) { const option = make('option', '', effortName(item.value) + ' (현재 미지원)'); option.value = item.value; option.disabled = true; option.title = item.reason; effortSelect.append(option); }
  }
  const scope = conversationDraftKey('agent-settings:' + current.selection) + ':' + current.revision;
  if (preferenceScope !== scope) { preferenceScope = scope; modeSelect.value = current.mode; effortSelect.value = current.effort; preferenceStatus.textContent = ''; }
  preferenceSummary.textContent = '에이전트 설정 · ' + modeNames[current.mode] + ' · ' + effortName(current.effort);
  const rate = cap.token_price, hold = cap.reservation;
  preferenceCost.textContent = '대화 모델 ' + cap.model + ' · 사용자가 선택한 모델 · ' + (rate ? '입력 ' + usd(rate.input_rate) + ' / 출력 ' + usd(rate.output_rate) + ' (100만 토큰당 · 문서 기준 · 청구 아님)' : '단가 기록 없음') + (hold ? ' · 회차당 최대 예약 ' + usd(hold.worst_per_round_micro / 1000000) + ' · 대화 상한 ' + usd(hold.conversation_cap_micro / 1000000) + ' 안 최대 ' + hold.worst_case_rounds_within_cap + '회차' : ' · 예약 기준 기록 없음');
  preferencePrice.textContent = (rate ? '단가 개정 ' + rate.revision + (rate.long_context ? ' · 입력 ' + rate.long_context.threshold_input_tokens + '토큰 초과 시 입력 ' + usd(rate.long_context.input_rate) + ' / 출력 ' + usd(rate.long_context.output_rate) : '') : '단가 기록 없음') + (hold ? ' · 회차 상한 입력 ' + hold.max_input_tokens + ' / 출력 ' + hold.max_output_tokens + '토큰' : '') + ' · 권한 ' + modeNames[current.mode] + ' · 추론 강도 ' + effortName(current.effort) + ' · 에이전트는 모델·권한·추론 강도를 바꿀 수 없습니다.';
  const source = typeof rate?.source === 'string' && /^https:\/\//.test(rate.source) ? rate.source : '';
  preferenceSource.hidden = !source; if (source) { preferenceSource.href = source; preferenceSource.textContent = '단가 출처 ' + source; }
  const active = prefs.active_response;
  preferenceActive.textContent = active ? '현재 응답: ' + modeNames[active.effective_mode] + ' · ' + effortName(active.effort) + (prefs.settings_pending ? ' · 변경한 강도·권한 확장은 다음 새 요청부터 적용됩니다. 권한 축소는 즉시 반영됩니다.' : ' · 이미 승인한 응답의 본문·추론 강도는 유지됩니다.') : '다음 요청: ' + modeNames[current.mode] + ' · ' + effortName(current.effort);
  preferenceRoute.textContent = !cap.general_route_supported ? '이 모델은 현재 일반 대화 연결에서 사용할 수 없습니다. 기존 별도 연결의 지원 여부를 확인하세요.' : !cap.general_route_configured ? '이 모델의 일반 대화 연결은 아직 설정되지 않았습니다. 설정 저장은 모델을 호출하지 않습니다.' : '현재 일반 대화 경로에서 지원하는 설정입니다. 계정·사용량·청구 확인은 별도입니다.';
  if (cap.unsupported_efforts?.length) preferenceRoute.textContent += ' 추론 강도 ' + cap.unsupported_efforts.map(item => effortName(item.value)).join(', ') + '는 현재 경로에서 지원하지 않습니다.';
  preferenceSave.disabled = !!busy || !!pendingId() || !!pendingId.failed || !!dirty || current.mode === modeSelect.value && current.effort === effortSelect.value;
 }
 modeSelect.addEventListener('change', () => renderPreferences(project())); effortSelect.addEventListener('change', () => renderPreferences(project()));
 preferenceForm.addEventListener('submit', async event => {
  event.preventDefault(); const p = project(), current = p?.agent_preferences?.current;
  if (!current || preferenceSave.disabled) return;
  const key = conversationDraftKey('agent-settings:' + current.selection);
  const data = { song: song(), selection: current.selection, settings_revision: current.revision, mode: modeSelect.value, effort: effortSelect.value };
  preferenceStatus.textContent = '설정 저장 중…';
  const saved = await act('conversation_agent_settings', data);
  renderPreferences(project());
  if (key === conversationDraftKey('agent-settings:' + project()?.agent_preferences?.current?.selection)) preferenceStatus.textContent = saved ? '에이전트 설정을 저장했습니다. 모델 호출은 없습니다.' : '설정을 저장하지 못했습니다. 현재 상태를 확인한 뒤 다시 저장하세요.';
 });
 try { const saved = Number(localStorage.getItem(WIDTH_KEY)); if (Number.isFinite(saved) && saved >= MIN_WIDTH && saved <= MAX_WIDTH) preferredWidth = saved; } catch (_) { /* Width preference does not affect request recovery. */ }
 function maximumWidth() { return Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, innerWidth - MIN_WORK_WIDTH - HANDLE_WIDTH)); }
 function width(value, persist = false) {
  const max = maximumWidth(), next = Math.round(Math.max(MIN_WIDTH, Math.min(max, value)));
  document.documentElement.style.setProperty('--agent-width', next + 'px');
  handle.setAttribute('aria-valuemin', String(MIN_WIDTH)); handle.setAttribute('aria-valuemax', String(max)); handle.setAttribute('aria-valuenow', String(next)); handle.setAttribute('aria-valuetext', next + '픽셀');
  narrower.disabled = next <= MIN_WIDTH; wider.disabled = next >= max;
  if (persist) { preferredWidth = next; try { localStorage.setItem(WIDTH_KEY, String(next)); } catch (_) {} }
  return next;
 }
 function refresh() {
  const p = project();
  const active = [...(p?.general_chat_turns || []), ...(p?.chat_turns || [])].some(t => ['queued', 'running', 'cancel_requested'].includes(t.status));
  const text = p ? `${song()} · ${shotName || '장면 미선택'} · ${p.timeline_head ? '저장 편집 v' + p.timeline_head : '편집 저장 전'}${active ? ' · 대화 작업 진행 중' : ''}` : '작품을 선택하면 음악·장면·편집을 함께 확인합니다.';
  if (context.textContent !== text) context.textContent = text;
  const hint = activeDialog ? '이 작업 창의 미저장 입력은 아직 AI에 반영되지 않습니다. 저장된 작품·편집을 기준으로 대화합니다.' : dirty ? '현재 편집에 미저장 변경이 있습니다. 저장 후 대화에 반영됩니다.' : '서버에 저장된 작품·편집을 기준으로 대화합니다.';
  if (savedHint.textContent !== hint) savedHint.textContent = hint;
  renderWorkStatus();
  renderPreferences(p);
  legacy.hidden = q('#modelChatPanel').hidden;
  proposals.hidden = !q('#timelineProposals').childElementCount;
 }
 function mobilePreview() { if (narrow.matches && q('[data-panel="review"][aria-selected="true"]')) q('[data-panel="preview"]')?.click(); }
 // Open on the chat tab the toggle collapses the panel; open on settings it only switches tabs, so it is not a disclosure there.
 function toggleState(isOpen, tab) { return isOpen && tab === 'chat' ? { expanded: 'true', label: 'AI 대화 닫기' } : isOpen ? { expanded: null, label: 'AI 대화 보기' } : { expanded: 'false', label: 'AI 대화 열기' }; }
 function apply() {
  document.body.dataset.agentOpen = String(opened && !activeDialog);
  sidebar.hidden = !opened || !!activeDialog; chat.hidden = !activeDialog && selected !== 'chat'; settings.hidden = selected !== 'settings';
  work.hidden = narrow.matches && opened && !activeDialog;
  chatTab.setAttribute('aria-selected', String(selected === 'chat')); settingsTab.setAttribute('aria-selected', String(selected === 'settings'));
  chatTab.tabIndex = selected === 'chat' ? 0 : -1; settingsTab.tabIndex = selected === 'settings' ? 0 : -1;
  const toggleView = toggleState(opened, selected); if (toggleView.expanded === null) toggle.removeAttribute('aria-expanded'); else toggle.setAttribute('aria-expanded', toggleView.expanded); toggle.textContent = toggleView.label;
  handle.hidden = narrow.matches || !(activeDialog ? dialogHosts.get(activeDialog)?.open : opened);
  handle.setAttribute('aria-controls', activeDialog ? chat.id : sidebar.id); sizes.hidden = handle.hidden;
  refresh();
 }
 function choose(name, focus = false) {
  navigationSequence++;
  selected = name; opened = true; if (name === 'chat') backToChat.hidden = true;
  if (narrow.matches) { if (name === 'settings') q('[data-panel="review"]')?.click(); else mobilePreview(); }
  apply(); if (focus) (name === 'chat' ? chatTab : settingsTab).focus();
 }
 function closeAgent() {
  navigationSequence++;
  if (activeDialog) { const host = dialogHosts.get(activeDialog); host.open = false; host.dock.hidden = true; host.launcher.setAttribute('aria-expanded', 'false'); activeDialog.classList.remove('agent-dialog-open'); handle.hidden = true; host.launcher.focus(); return; }
  opened = false; mobilePreview(); apply(); toggle.focus();
 }
 close.addEventListener('click', closeAgent);
 toggle.addEventListener('click', () => { if (opened && selected === 'chat') closeAgent(); else { choose('chat'); chatTab.focus(); } });
 chatTab.addEventListener('click', () => choose('chat')); settingsTab.addEventListener('click', () => choose('settings'));
 backToChat.addEventListener('click', () => choose('chat', true));
 for (const [button, step, other] of [[narrower, -48, wider], [wider, 48, narrower]]) button.addEventListener('click', () => { width(Number(handle.getAttribute('aria-valuenow')) + step, true); if (button.disabled) other.focus(); });
 tabs.addEventListener('keydown', event => {
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
  event.preventDefault(); choose(event.key === 'Home' ? 'chat' : event.key === 'End' ? 'settings' : selected === 'chat' ? 'settings' : 'chat', true);
 });
 handle.addEventListener('keydown', event => {
  const current = Number(handle.getAttribute('aria-valuenow')), step = event.shiftKey ? 48 : 16;
  const values = { ArrowLeft: current + step, ArrowRight: current - step, Home: MIN_WIDTH, End: maximumWidth() };
  if (event.key === 'Enter') { event.preventDefault(); closeAgent(); return; }
  if (!(event.key in values)) return;
  event.preventDefault(); width(values[event.key], true);
 });
 handle.addEventListener('pointerdown', event => {
  if (event.button !== 0 || narrow.matches) return;
  event.preventDefault(); handle.focus(); drag = { id: event.pointerId, x: event.clientX, width: Number(handle.getAttribute('aria-valuenow')) }; handle.setPointerCapture(event.pointerId); document.body.classList.add('agent-resizing');
 });
 handle.addEventListener('pointermove', event => { if (drag?.id === event.pointerId) width(drag.width + drag.x - event.clientX); });
 function stopDrag(event) { if (drag?.id !== event.pointerId) return; width(Number(handle.getAttribute('aria-valuenow')), true); drag = null; document.body.classList.remove('agent-resizing'); }
 handle.addEventListener('pointerup', stopDrag); handle.addEventListener('pointercancel', stopDrag); handle.addEventListener('lostpointercapture', stopDrag);
 function prepareDialog(dialog) {
  if (dialogHosts.has(dialog)) return;
  const main = make('div', 'agent-dialog-main'); while (dialog.firstChild) main.append(dialog.firstChild);
  const launcher = make('button', 'agent-dialog-launcher', 'AI 대화 열기'); launcher.type = 'button'; launcher.setAttribute('aria-controls', chat.id); launcher.setAttribute('aria-expanded', 'false');
  const titleRow = main.firstElementChild?.matches('.row') && main.firstElementChild.querySelector(':scope > h2') ? main.firstElementChild : null, dismissButton = titleRow?.querySelector(':scope > button:last-of-type');
  if (dismissButton) dismissButton.before(launcher); else { const firstHeading = main.querySelector(':scope > h2'); if (firstHeading) firstHeading.after(launcher); else main.prepend(launcher); }
  if (!main.querySelector('[autofocus]')) { const initial = dismissButton || main.querySelector('#dismissRender'); if (initial) initial.autofocus = true; }
  const dock = make('aside', 'agent-dialog-dock'); dock.hidden = true; dock.setAttribute('aria-label', 'AI 대화');
  const heading = make('div', 'agent-dialog-heading'), title = make('h2', '', 'AI 대화'), dismiss = make('button', 'agent-dialog-dismiss', '대화 닫기'); dismiss.type = 'button'; heading.append(title, dismiss); dock.append(heading); dialog.append(main, dock);
  const host = { main, launcher, dock, open: false }; dialogHosts.set(dialog, host); dialog.classList.add('agent-dialog');
  launcher.addEventListener('click', () => { host.open = true; portal(dialog); q('#generalChatPrompt')?.focus(); });
  dismiss.addEventListener('click', closeAgent);
 }
 function portal(dialog) {
  activeDialog = dialog;
  if (dialog) {
   const host = dialogHosts.get(dialog); host.dock.append(chat); host.dock.before(handle); host.dock.querySelector('.agent-dialog-dismiss').before(sizes); chat.hidden = false; chat.setAttribute('aria-label', 'AI 대화'); chat.removeAttribute('aria-labelledby'); host.dock.hidden = !host.open; dialog.classList.toggle('agent-dialog-open', host.open); host.launcher.setAttribute('aria-expanded', String(host.open));
  } else { sidebar.append(chat); workspace.insertBefore(handle, sidebar); header.insertBefore(sizes, close); chat.setAttribute('aria-labelledby', chatTab.id); chat.removeAttribute('aria-label'); }
  apply();
 }
 function syncDialogs() {
  document.querySelectorAll('dialog').forEach(dialog => {
   prepareDialog(dialog);
   const i = dialogStack.indexOf(dialog);
   if (dialog.open && i === -1) { dialogStack.push(dialog); const host = dialogHosts.get(dialog); host.open = opened && selected === 'chat'; }
   else if (!dialog.open) { if (i !== -1) dialogStack.splice(i, 1); dialog.classList.remove('agent-dialog-open'); dialogHosts.get(dialog).dock.hidden = true; }
  });
  const next = dialogStack.at(-1) || null;
  if (next !== activeDialog) { const focused = document.activeElement, retain = chat.contains(focused); portal(next); if (retain && focused?.isConnected) { if (next && !dialogHosts.get(next).open) dialogHosts.get(next).launcher.focus(); else if (!next && !opened) toggle.focus(); else focused.focus({ preventScroll: true }); } }
 }
 // Observe dialog lifecycle only; never infer application state from rendered text.
 const lifecycle = new MutationObserver(records => { if (records.some(r => r.type === 'childList' && [...r.addedNodes].some(n => n.nodeType === 1 && (n.matches?.('dialog') || n.querySelector?.('dialog'))) || r.type === 'attributes' && r.target.tagName === 'DIALOG')) syncDialogs(); });
 lifecycle.observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ['open'] });
 sidebar.addEventListener('keydown', event => { if (event.key === 'Escape' && !event.defaultPrevented) { event.preventDefault(); closeAgent(); } });
 settings.addEventListener('keydown', event => { if (event.key !== 'Escape' || event.defaultPrevented) return; const details = event.target.closest('details'); if (details?.open && settings.contains(details)) { event.preventDefault(); event.stopPropagation(); details.open = false; details.querySelector('summary')?.focus(); } else if (event.target.matches('input, textarea, select')) event.stopPropagation(); });
 chat.addEventListener('keydown', event => { if (event.key !== 'Escape' || event.defaultPrevented) return; const details = event.target.closest('details'); if (details?.open && chat.contains(details)) { event.preventDefault(); event.stopPropagation(); details.open = false; details.querySelector('summary')?.focus(); } else { event.preventDefault(); event.stopPropagation(); closeAgent(); } });
 // Preserve the existing mobile review/player controller and its original nodes.
 q('[data-panel="review"]')?.addEventListener('click', () => { selected = 'settings'; opened = true; apply(); });
 q('[data-panel="preview"]')?.addEventListener('click', () => { if (narrow.matches && selected === 'settings') { selected = 'chat'; opened = false; apply(); } });
 const stageObserver = new MutationObserver(() => { if (narrow.matches && selected === 'settings') { selected = 'chat'; opened = false; } apply(); });
 stageObserver.observe(document.body, { attributes: true, attributeFilter: ['data-step', 'data-guided'] });
 addEventListener('resize', () => width(preferredWidth)); narrow.addEventListener('change', () => { mobilePreview(); width(preferredWidth); apply(); });
 window.LoretuneAgentSidebar = { refresh, open: () => { if (activeDialog) { dialogHosts.get(activeDialog).open = true; portal(activeDialog); } else choose('chat'); }, close: closeAgent, reviewMediaAction: async (...args) => { const result = await reviewMediaAction(...args); if (result === 'opened') backToChat.hidden = false; return result; }, reviewStudioProposal };
 window.LoretuneGeneralChat.mount({ container: generalHost, onClose: closeAgent });
 width(preferredWidth); syncDialogs(); apply();
 // Reuse the application's scoped public-state polling. This is presentation
 // only: no new requests, providers, job creation, or execution-state writes.
 setInterval(() => { if (!document.hidden) renderWorkStatus(); }, 1500);
})();
