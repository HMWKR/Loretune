'use strict';
// Diagnostic only: current source handlers and request controller, in-memory doubles.
// No browser, HTTP, provider, database, application-source or user-data writes.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const html = fs.readFileSync('index.html', 'utf8');
const harnessPath = 'tests/frontend_async_regressions.cjs';
const prefix = fs.readFileSync(harnessPath, 'utf8')
  .split('\n(async()=>{')[0]
  .replace("const {fixture}=require('./media_async_harness.cjs');", '');
const root = {require, console};
vm.createContext(root);
vm.runInContext(prefix + '\nglobalThis.makeRequestFixture=requestFixture;', root);
const rows = [];

(async () => {
  for (const formId of ['preferenceForm', 'chatForm']) {
    for (const mode of ['edit', 'switch', 'reject']) {
      const f = root.makeRequestFixture();
      let currentProject = 'A', releaseResponse;
      f.c.song = () => currentProject;
      f.c.project = () => ({ip: 'synthetic-ip'});
      f.c.state.capabilities = {chat_plan: true};
      f.c.FormData = class {
        constructor(form) { this.snapshot = {...form.data}; }
        get(key) { return this.snapshot[key] ?? null; }
      };
      const form = f.$('#' + formId);
      form.data = {scope: 'song', category: 'color', value: 'first', evidence: 'synthetic', reason: 'fixture', prompt: 'first'};
      form.reset = () => { form.data = {}; };
      f.c.fetch = async (url, options) => {
        f.calls.push([url, options]);
        return new Promise(resolve => { releaseResponse = resolve; });
      };
      const handler = html.split('\n').find(line => line.startsWith("$('#" + formId + "').onsubmit="));
      assert.ok(handler, 'current source handler found');
      vm.runInContext(handler, f.c);
      const submitted = form.onsubmit({target: form, preventDefault() {}});
      for (let turn = 0; !releaseResponse && turn < 10; turn++) await Promise.resolve();
      assert.equal(typeof releaseResponse, 'function', 'request reached controlled response');
      if (mode === 'switch') currentProject = 'B';
      form.data.value = form.data.prompt = '대기 중 새 초안';
      releaseResponse({ok: mode !== 'reject', status: mode === 'reject' ? 400 : 200,
        json: async () => mode === 'reject' ? {error: 'synthetic rejection'} : {}});
      await submitted;
      const row = {form: formId, mode, submittedProject: 'A', currentProject,
        newDraftLost: form.data.prompt !== '대기 중 새 초안',
        requestCount: f.calls.filter(call => call[0] === '/api/action').length};
      assert.equal(row.requestCount, 1);
      assert.equal(row.newDraftLost, mode !== 'reject', 'baseline counterexample/control result');
      rows.push(row);
    }
  }
  console.log(JSON.stringify({observedAtUtc: new Date().toISOString(), evidence: 'current-source Node VM; not browser',
    sourceSha256: crypto.createHash('sha256').update(html).digest('hex'),
    expectations: 'baseline defect reproduced, not product acceptance', rows}, null, 2));
})().catch(error => { console.error(error); process.exitCode = 1; });
