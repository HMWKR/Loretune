// One viewport capture of one UI state at one width (aside repl, deterministic lane).
// Placeholders replaced by capture.sh: "http://127.0.0.1:62828" (JSON string), 1920, 1080, 0.75, "f_dialog_new_project" (JSON string).
// SCALE < 1 is used only when W x H exceeds the Aside tab viewport (1440x900 measured): the iframe keeps a true
// W x H layout viewport (media queries see W) and is CSS-scaled with transform so the clip stays inside the tab.
// Clip beyond the tab viewport was measured to return a tiled fake image (trial 2026-10-28), so it is never used.
// Method = design-toolchain run-qa.sh: same-origin iframe sized W x H + screenshot clip (Aside has no
// setViewportSize/CDP). The host tab loads a static same-origin file (/studio.css) so the app runs only
// inside the iframe. Each state starts from a fresh tab + fresh iframe load (no order dependency).
// UI actions are element.click() on fixed selectors inside the iframe (snapshot refs are not stable
// across runs, so they cannot reproduce the same steps for the "after" capture). No form submission,
// no POST: states are presentation-only (step nav, sidebar open/close, review navigation, showModal).
const ORIGIN = "http://127.0.0.1:62828", W = 1920, H = 1080, SCALE = 0.75, STATE = "f_dialog_new_project";
const KEY = STATE + '_' + W;
let host = null;
const meta = { state: STATE, width: W, height: H, scale: SCALE };
try {
  host = await openTab(ORIGIN + '/studio.css');
  const setup = await host.evaluate(async ([src, w, h, sc]) => {
    try { localStorage.clear(); sessionStorage.clear(); } catch (e) {}
    const outer = { iw: innerWidth, ih: innerHeight, dpr: devicePixelRatio };
    if (innerWidth < Math.ceil(w * sc) || innerHeight < Math.ceil(h * sc)) return { error: 'VIEWPORT_TOO_SMALL', outer };
    document.documentElement.style.cssText = 'margin:0;background:#000;overflow:hidden';
    document.head.innerHTML = ''; document.body.style.cssText = 'margin:0;overflow:hidden'; document.body.innerHTML = '';
    const f = Object.assign(document.createElement('iframe'), { width: w, height: h, id: 'cap' });
    f.style.cssText = 'border:0;display:block' + (sc !== 1 ? ';transform:scale(' + sc + ');transform-origin:0 0' : '');
    const ok = new Promise(r => f.onload = r); f.src = src; document.body.appendChild(f);
    await Promise.race([ok, new Promise(r => setTimeout(r, 15000))]);
    const cw = f.contentWindow, d = f.contentDocument;
    if (!d || !d.body) return { error: 'FRAME_BLOCKED', outer };
    const t0 = Date.now();
    while (Date.now() - t0 < 10000) {   // app ready = state loaded and shot list rendered
      const n = d.querySelector('#notice')?.textContent || '';
      if (d.querySelectorAll('#shotlist [data-shot]').length && !/불러오는 중/.test(n)) break;
      await new Promise(r => setTimeout(r, 100));
    }
    try { await Promise.race([d.fonts.ready, new Promise(r => setTimeout(r, 3000))]); } catch (e) {}
    d.documentElement.style.scrollBehavior = 'auto';
    return { outer, iw: cw.innerWidth, ih: cw.innerHeight, ready_ms: Date.now() - t0 };
  }, [ORIGIN + '/', W, H, SCALE]);
  Object.assign(meta, setup);
  if (setup.error) throw new Error(setup.error);

  // ---- state actions (inside iframe) ----
  const act = async (fn, arg) => host.evaluate(new Function('arg', 'const f=document.getElementById("cap"),d=f.contentDocument,w=f.contentWindow;' + fn), arg);
  const settle = async () => host.evaluate(async () => {
    const d = document.getElementById('cap').contentDocument;
    const end = Date.now() + 2000;
    let run = () => d.getAnimations().filter(a => a.playState === 'running' && Number.isFinite(a.effect?.getComputedTiming().endTime));
    while (run().length && Date.now() < end) await new Promise(r => setTimeout(r, 50));
    await new Promise(r => setTimeout(r, 400));
    return run().length;
  });
  const OPEN_SIDEBAR = 'const s=d.querySelector("#agentSidebar"); if (s.hidden || d.querySelector("#agentToggle").getAttribute("aria-expanded")!=="true") d.querySelector("#agentToggle").click(); const t=d.querySelector("#agentChatTab"); if (t.getAttribute("aria-selected")!=="true") t.click();';
  const steps = [];
  if (STATE === 'a_first_load') {
    // no interaction
  } else if (STATE === 'a2_step1_music') {
    steps.push('click .flow-nav [data-step="1"]');
    await act('d.querySelector(\'.flow-nav [data-step="1"]\').click();');
  } else if (STATE === 'b_ai_panel_open') {
    steps.push('ensure #agentSidebar open via #agentToggle; select #agentChatTab');
    await act(OPEN_SIDEBAR);
  } else if (STATE === 'c_ai_panel_closed') {
    steps.push('ensure open (as b), then click .agent-close');
    await act(OPEN_SIDEBAR); await settle();
    await act('d.querySelector("#agentSidebar .agent-close").click();');
  } else if (STATE === 'd_shotboard_media_card') {
    steps.push('click .flow-nav [data-step="3"]', 'ensure sidebar open + chat tab', 'click #generalChatTurns [data-general-review-action] (app review navigation -> settings tab, shot 1, media action card focused)');
    await act('d.querySelector(\'.flow-nav [data-step="3"]\').click();'); await settle();
    await act(OPEN_SIDEBAR); await settle();
    await act('const b=d.querySelector("#generalChatTurns [data-general-review-action]"); if(!b) throw new Error("NO_REVIEW_BUTTON"); b.click();');
  } else if (STATE === 'e_timeline_edit') {
    steps.push('click .flow-nav [data-step="4"]');
    await act('d.querySelector(\'.flow-nav [data-step="4"]\').click();');
  } else if (STATE === 'e2_timeline_edit_panel_closed') {
    steps.push('click .flow-nav [data-step="4"]', 'ensure sidebar open (as b), then click .agent-close (375: default-open sidebar covers the timeline)');
    await act('d.querySelector(\'.flow-nav [data-step="4"]\').click();'); await settle();
    await act(OPEN_SIDEBAR); await settle();
    await act('d.querySelector("#agentSidebar .agent-close").click();');
  } else if (STATE === 'f_dialog_new_project') {
    steps.push('click #newProject (opens #projectDialog via showModal; not submitted)');
    await act('d.querySelector("#newProject").click();');
  } else throw new Error('UNKNOWN_STATE ' + STATE);
  meta.steps = steps;
  meta.unsettled_animations = await settle();
  Object.assign(meta, await host.evaluate(() => {
    const f = document.getElementById('cap'), d = f.contentDocument, q = s => d.querySelector(s);
    const card = q('[data-action-card]'), r = card?.getBoundingClientRect();
    return {
      app_step: d.body.dataset.step, heading: q('#flowHeading')?.textContent, notice: q('#notice')?.textContent,
      sidebar_open: q('#agentToggle')?.getAttribute('aria-expanded'), sidebar_tab: q('#agentSettingsTab')?.getAttribute('aria-selected') === 'true' ? 'settings' : 'chat',
      open_dialogs: [...d.querySelectorAll('dialog')].filter(x => x.open).map(x => x.id),
      media_card_in_view: !!(r && card.checkVisibility() && r.bottom > 0 && r.top < f.contentWindow.innerHeight),
      shot: (typeof f.contentWindow.shotName === 'string') ? f.contentWindow.shotName : null,
      doc_scroll: [f.contentWindow.scrollX, f.contentWindow.scrollY], url: f.contentWindow.location.href,
      body_bg: getComputedStyle(d.body).backgroundColor, color_scheme: getComputedStyle(d.documentElement).colorScheme,
    };
  }));
  // scrollIntoView inside the iframe can also scroll the host tab (the unscaled 1920 iframe box is larger than
  // the tab); record it and reset so the clip always starts at the iframe's top-left (trial 2026-10-28 finding).
  meta.host_scroll_before_reset = await host.evaluate(() => { const v = [scrollX, scrollY]; scrollTo(0, 0); return v; });
  const png = Buffer.from(await host.screenshot({ type: 'png', clip: { x: 0, y: 0, width: Math.round(W * SCALE), height: Math.round(H * SCALE) } }));
  meta.png_px = [png.readUInt32BE(16), png.readUInt32BE(20)];
  console.log('PNG_' + KEY + '_START'); console.log(png.toString('base64')); console.log('PNG_' + KEY + '_END');
} catch (e) {
  meta.error = String(e && e.message || e).slice(0, 200);
} finally {
  console.log('META ' + JSON.stringify(meta));
  if (host) await closeTab(host);
}
