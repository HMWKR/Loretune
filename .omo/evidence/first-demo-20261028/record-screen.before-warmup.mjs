// Capture the actual task-owned browser viewport, preserving elapsed time.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';

// Short observations leave the page command channel free for screencast ACKs.
// A long waitForFunction occupies that channel and makes the capture drop frames.
export async function observeUntil(page, predicate, argument, timeout = 15000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (await (argument === undefined ? page.evaluate(predicate) : page.evaluate(predicate, argument))) return;
    await new Promise(resolve => setTimeout(resolve, 90));
  }
  throw new Error('Recorded UI observation timed out; inspect actual state before replay.');
}

export async function recordScreen(page, folder, actions) {
  await fs.mkdir(folder); // Refuse to overwrite an earlier take.
  await page.cdp('Page.enable');
  await page.cdp('Network.enable');
  await page.cdp('Runtime.enable');
  await page.events();
  const startedAt = Date.now();
  const frames = [], requests = [], responses = [], markers = [], runtimeErrors = [], requestFailures = [];
  let active = true, actionError = null, captureError = null;
  const mark = async (name, detail = {}) => {
    markers.push({ name, elapsedSeconds: (Date.now() - startedAt) / 1000, ...detail });
    await fs.writeFile(path.join(folder, 'markers.json'), JSON.stringify(markers, null, 2));
  };
  await page.cdp('Page.startScreencast', { format: 'jpeg', quality: 85, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 });
  async function drain() {
    for (const event of await page.events()) {
      if (event.method === 'Page.screencastFrame') {
        const p = event.params;
        const filename = `frame-${String(frames.length).padStart(6, '0')}.jpg`;
        const bytes = Buffer.from(p.data, 'base64');
        await fs.writeFile(path.join(folder, filename), bytes);
        frames.push({ filename, capturedTimestamp: p.metadata.timestamp, receivedAt: Date.now(), bytes: bytes.length, sha256: crypto.createHash('sha256').update(bytes).digest('hex') });
        await page.cdp('Page.screencastFrameAck', { sessionId: p.sessionId });
      } else if (event.method === 'Network.requestWillBeSent' && event.params.request.url.includes('/api/')) {
        const { requestId, request, timestamp } = event.params;
        let action = null;
        try {
          const v = JSON.parse(request.postData || '{}');
          action = { action: v.action, request_id: v.request_id, revision: v.revision, conversation_id: v.conversation_id, data_fields: Object.keys(v.data || {}) };
        } catch { /* Binary upload details are deliberately omitted. */ }
        requests.push({ requestId, url: request.url, method: request.method, timestamp, action });
      } else if (event.method === 'Network.responseReceived' && event.params.response.url.includes('/api/')) {
        const { requestId, response, timestamp } = event.params;
        responses.push({ requestId, url: response.url, status: response.status, timestamp });
      } else if (event.method === 'Runtime.exceptionThrown') {
        const d = event.params.exceptionDetails;
        runtimeErrors.push({ timestamp: event.params.timestamp, text: d.text, description: String(d.exception?.description || '').slice(0, 600), url: d.url, lineNumber: d.lineNumber });
      } else if (event.method === 'Network.loadingFailed') {
        requestFailures.push({ requestId: event.params.requestId, timestamp: event.params.timestamp, type: event.params.type, errorText: event.params.errorText, cancelled: event.params.canceled === true });
      }
    }
  }
  const capture = (async () => {
    try {
      while (active) { await drain(); await new Promise(resolve => setTimeout(resolve, 35)); }
      await drain();
    } catch (error) { captureError = { name: error.name, message: error.message }; active = false; }
  })();
  try { await mark('recording-start'); await actions(mark); await mark('actions-complete'); }
  catch (error) { actionError = { name: error.name, message: error.message }; await mark('action-failed', actionError); }
  finally {
    active = false;
    await capture;
    await page.cdp('Page.stopScreencast');
    const finishedAt = Date.now();
    const record = { capture: 'Actual Chromium Page.startScreencast viewport frames', startedAt, finishedAt, elapsedSeconds: (finishedAt - startedAt) / 1000, frames, markers, requests, responses, runtimeErrors, requestFailures, actionError, captureError, edited: false, spedUp: false, omittedIntervals: [], audio: 'Browser pixel capture only; output media audio is delivered separately.', otherTabsOrDesktopCaptured: false };
    await fs.writeFile(path.join(folder, 'recording.json'), JSON.stringify(record, null, 2));
    if (!frames.length || captureError) throw new Error('Browser recording failed; retained diagnostic record.');
  }
  if (actionError) throw new Error('Demo actions failed; recording is retained with failure marker.');
  return { folder, frames: frames.length, elapsedSeconds: (Date.now() - startedAt) / 1000 };
}
