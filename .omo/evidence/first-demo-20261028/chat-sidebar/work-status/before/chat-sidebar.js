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
 const sidebar = make('aside', 'agent-sidebar'); sidebar.id = 'agentSidebar'; sidebar.setAttribute('aria-label', 'AI 대화와 작업 설정');
 const handle = make('div', 'agent-resizer'); handle.tabIndex = 0; handle.setAttribute('role', 'separator'); handle.setAttribute('aria-orientation', 'vertical'); handle.setAttribute('aria-label', 'AI 대화와 작업 설정 너비');
 const header = make('div', 'agent-sidebar-header'), tabs = make('div', 'agent-tabs'); tabs.setAttribute('role', 'tablist'); tabs.setAttribute('aria-label', '오른쪽 작업 공간');
 const chatTab = make('button', '', 'AI 대화'), settingsTab = make('button', '', '작업 설정'), close = make('button', 'agent-close', '닫기');
 chatTab.id = 'agentChatTab'; settingsTab.id = 'agentSettingsTab';
 const chat = make('section', 'agent-chat-pane'); chat.id = 'agentChatPane'; chat.setAttribute('role', 'tabpanel'); chat.setAttribute('aria-labelledby', chatTab.id);
 const settings = make('section', 'agent-settings-pane'); settings.id = 'agentSettingsPane'; settings.setAttribute('role', 'tabpanel'); settings.setAttribute('aria-labelledby', settingsTab.id);
 for (const [button, pane] of [[chatTab, chat], [settingsTab, settings]]) { button.type = 'button'; button.setAttribute('role', 'tab'); button.setAttribute('aria-controls', pane.id); tabs.append(button); }
 close.type = 'button'; close.setAttribute('aria-label', '오른쪽 작업 공간 닫기'); header.append(tabs, close); sidebar.append(header, chat, settings); workspace.append(handle, sidebar);
 const toggle = make('button', 'agent-toggle', 'AI 대화'); toggle.id = 'agentToggle'; toggle.type = 'button'; toggle.setAttribute('aria-controls', sidebar.id); q('.lt-studio-shell').append(toggle);
 const context = make('p', 'agent-context'); context.id = 'agentContext'; chat.append(context);
 const savedHint = make('p', 'agent-saved-hint', '서버에 저장된 작품·편집을 기준으로 대화합니다.'); chat.append(savedHint);
 chat.append(q('#conversationControls'));
 const preferences = make('div', 'agent-preferences-slot'); preferences.id = 'agentPreferencesSlot'; chat.append(preferences);
 const preferenceDetails = make('details', 'agent-preferences'), preferenceSummary = make('summary', '', '에이전트 설정');
 const preferenceForm = make('form', 'agent-preferences-form'); preferenceForm.id = 'agentPreferencesForm';
 const modeLabel = make('label', '', '편집 권한'), modeSelect = make('select'); modeSelect.id = 'agentMode'; modeLabel.htmlFor = modeSelect.id;
 const effortLabel = make('label', '', '추론 강도'), effortSelect = make('select'); effortSelect.id = 'agentEffort'; effortLabel.htmlFor = effortSelect.id;
 const preferenceSave = make('button', '', '에이전트 설정 저장 · 호출 없음'); preferenceSave.type = 'submit';
 const preferenceStatus = make('p'); preferenceStatus.id = 'agentSettingsStatus'; preferenceStatus.setAttribute('role', 'status');
 const preferenceRoute = make('p', 'agent-setting-note'), preferenceActive = make('p', 'agent-setting-note');
 const preferencePolicy = make('p', 'agent-setting-note', 'FullAccess는 허용된 비삭제 편집만 새 미승인 버전으로 저장합니다. 컷 제외·겹침 제거는 검토가 필요하며, 최종 출력·비용·전송·사용권 승인은 별도입니다. 계정 삭제는 금지하며 다른 파일 삭제도 대상별 명시 허가가 필요합니다.');
 preferenceForm.append(modeLabel, modeSelect, effortLabel, effortSelect, preferenceSave, preferenceStatus); preferenceDetails.append(preferenceSummary, preferenceForm, preferenceRoute, preferenceActive, preferencePolicy); preferences.append(preferenceDetails); preferences.hidden = true;
 const generalHost = make('div', 'agent-general-host'); chat.append(generalHost);
 const legacy = make('details', 'agent-legacy-chat'); const legacyTitle = make('summary', '', '기존 연결 대화 · 별도 실행 이력'); legacy.append(legacyTitle, q('#modelChatPanel')); chat.append(legacy);
 const proposalTitle = make('h2', '', '편집 변경안'); const proposals = make('section', 'agent-proposals'); proposals.setAttribute('aria-label', '편집 변경안 검토'); proposals.append(proposalTitle, q('#timelineProposals')); chat.append(proposals);
 settings.append(inspector);
 let opened = true, selected = 'chat', activeDialog = null, drag = null, preferredWidth = DEFAULT_WIDTH;
 const dialogHosts = new Map(), dialogStack = [];
 let preferenceScope = '', preferenceChoices = '';
 const modeNames = { read_only: '읽기 전용', review: '검토 후 편집', full_access: 'FullAccess' };
 function renderPreferences(p) {
  const prefs = p?.agent_preferences, current = prefs?.current, cap = prefs?.capabilities?.models?.[current?.selection];
  preferences.hidden = !current?.selection || !cap;
  if (preferences.hidden) return;
  const choices = JSON.stringify([prefs.capabilities.modes, cap.effort_options, cap.unsupported_efforts]);
  if (choices !== preferenceChoices) {
   preferenceChoices = choices; modeSelect.replaceChildren(); effortSelect.replaceChildren();
   for (const mode of prefs.capabilities.modes) { const option = make('option', '', mode.label); option.value = mode.id; modeSelect.append(option); }
   for (const value of cap.effort_options) { const option = make('option', '', value); option.value = value; effortSelect.append(option); }
   for (const item of cap.unsupported_efforts || []) { const option = make('option', '', item.value + ' · 현재 미지원'); option.value = item.value; option.disabled = true; option.title = item.reason; effortSelect.append(option); }
  }
  const scope = conversationDraftKey('agent-settings:' + current.selection) + ':' + current.revision;
  if (preferenceScope !== scope) { preferenceScope = scope; modeSelect.value = current.mode; effortSelect.value = current.effort; preferenceStatus.textContent = ''; }
  preferenceSummary.textContent = '에이전트 설정 · ' + modeNames[current.mode] + ' · ' + current.effort;
  const active = prefs.active_response;
  preferenceActive.textContent = active ? '현재 응답: ' + modeNames[active.effective_mode] + ' · ' + active.effort + (prefs.settings_pending ? ' · 변경한 강도·권한 확장은 다음 새 요청부터 적용됩니다. 권한 축소는 즉시 반영됩니다.' : ' · 이미 승인한 응답의 본문·추론 강도는 유지됩니다.') : '다음 요청: ' + modeNames[current.mode] + ' · ' + current.effort;
  preferenceRoute.textContent = !cap.general_route_supported ? '이 모델은 현재 일반 대화 연결에서 사용할 수 없습니다. 기존 별도 연결의 지원 여부를 확인하세요.' : !cap.general_route_configured ? '이 모델의 일반 대화 연결은 아직 설정되지 않았습니다. 설정 저장은 모델을 호출하지 않습니다.' : '현재 일반 대화 경로에서 지원하는 설정입니다. 계정·사용량·청구 확인은 별도입니다.';
  if (cap.unsupported_efforts?.length) preferenceRoute.textContent += ' xhigh·max는 현재 경로에서 지원하지 않습니다.';
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
  renderPreferences(p);
  legacy.hidden = q('#modelChatPanel').hidden;
  proposals.hidden = !q('#timelineProposals').childElementCount;
 }
 function mobilePreview() { if (narrow.matches && q('[data-panel="review"][aria-selected="true"]')) q('[data-panel="preview"]')?.click(); }
 function apply() {
  document.body.dataset.agentOpen = String(opened && !activeDialog);
  sidebar.hidden = !opened || !!activeDialog; chat.hidden = !activeDialog && selected !== 'chat'; settings.hidden = selected !== 'settings';
  work.hidden = narrow.matches && opened && !activeDialog;
  chatTab.setAttribute('aria-selected', String(selected === 'chat')); settingsTab.setAttribute('aria-selected', String(selected === 'settings'));
  chatTab.tabIndex = selected === 'chat' ? 0 : -1; settingsTab.tabIndex = selected === 'settings' ? 0 : -1;
  toggle.setAttribute('aria-expanded', String(opened)); toggle.textContent = opened ? 'AI 대화 · 열림' : 'AI 대화 열기';
  handle.hidden = narrow.matches || !(activeDialog ? dialogHosts.get(activeDialog)?.open : opened);
  handle.setAttribute('aria-controls', activeDialog ? chat.id : sidebar.id);
  refresh();
 }
 function choose(name, focus = false) {
  selected = name; opened = true;
  if (narrow.matches) { if (name === 'settings') q('[data-panel="review"]')?.click(); else mobilePreview(); }
  apply(); if (focus) (name === 'chat' ? chatTab : settingsTab).focus();
 }
 function closeAgent() {
  if (activeDialog) { const host = dialogHosts.get(activeDialog); host.open = false; host.dock.hidden = true; host.launcher.setAttribute('aria-expanded', 'false'); activeDialog.classList.remove('agent-dialog-open'); handle.hidden = true; host.launcher.focus(); return; }
  opened = false; mobilePreview(); apply(); toggle.focus();
 }
 close.addEventListener('click', closeAgent);
 toggle.addEventListener('click', () => { if (opened && selected === 'chat') closeAgent(); else { choose('chat'); chatTab.focus(); } });
 chatTab.addEventListener('click', () => choose('chat')); settingsTab.addEventListener('click', () => choose('settings'));
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
  const launcher = make('button', 'agent-dialog-launcher', 'AI 대화 열기'); launcher.type = 'button'; launcher.setAttribute('aria-controls', chat.id); launcher.setAttribute('aria-expanded', 'false'); main.prepend(launcher);
  const dock = make('aside', 'agent-dialog-dock'); dock.hidden = true; dock.setAttribute('aria-label', 'AI 대화');
  const heading = make('div', 'agent-dialog-heading'), title = make('h2', '', 'AI 대화'), dismiss = make('button', '', '대화 닫기'); dismiss.type = 'button'; heading.append(title, dismiss); dock.append(heading); dialog.append(main, dock);
  const host = { main, launcher, dock, open: false }; dialogHosts.set(dialog, host); dialog.classList.add('agent-dialog');
  launcher.addEventListener('click', () => { host.open = true; portal(dialog); q('#generalChatPrompt')?.focus(); });
  dismiss.addEventListener('click', closeAgent);
 }
 function portal(dialog) {
  activeDialog = dialog;
  if (dialog) {
   const host = dialogHosts.get(dialog); host.dock.append(chat); host.dock.before(handle); chat.hidden = false; chat.setAttribute('aria-label', 'AI 대화'); chat.removeAttribute('aria-labelledby'); host.dock.hidden = !host.open; dialog.classList.toggle('agent-dialog-open', host.open); host.launcher.setAttribute('aria-expanded', String(host.open));
  } else { sidebar.append(chat); workspace.insertBefore(handle, sidebar); chat.setAttribute('aria-labelledby', chatTab.id); chat.removeAttribute('aria-label'); }
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
 chat.addEventListener('keydown', event => { if (event.key !== 'Escape' || event.defaultPrevented) return; const details = event.target.closest('details'); if (details?.open && chat.contains(details)) { event.preventDefault(); event.stopPropagation(); details.open = false; details.querySelector('summary')?.focus(); } else { event.preventDefault(); event.stopPropagation(); closeAgent(); } });
 // Preserve the existing mobile review/player controller and its original nodes.
 q('[data-panel="review"]')?.addEventListener('click', () => { selected = 'settings'; opened = true; apply(); });
 q('[data-panel="preview"]')?.addEventListener('click', () => { if (narrow.matches && selected === 'settings') { selected = 'chat'; opened = false; apply(); } });
 const stageObserver = new MutationObserver(() => { if (narrow.matches && selected === 'settings') { selected = 'chat'; opened = false; } apply(); });
 stageObserver.observe(document.body, { attributes: true, attributeFilter: ['data-step', 'data-guided'] });
 addEventListener('resize', () => width(preferredWidth)); narrow.addEventListener('change', () => { mobilePreview(); width(preferredWidth); apply(); });
 window.LoretuneAgentSidebar = { refresh, open: () => { if (activeDialog) { dialogHosts.get(activeDialog).open = true; portal(activeDialog); } else choose('chat'); }, close: closeAgent };
 window.LoretuneGeneralChat.mount({ container: generalHost, onClose: closeAgent });
 width(preferredWidth); syncDialogs(); apply();
})();
