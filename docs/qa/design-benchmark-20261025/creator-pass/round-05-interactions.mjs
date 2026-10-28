import fs from 'node:fs/promises';const D='/Users/leesungmin/Desktop/Loretune/docs/qa/design-benchmark-20261025/creator-pass';const t=await taskSpace(14),p=t.page('p1'),results=[];
await p.cdp('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
// Use the actual candidate controller; replace only its action boundary with a deferred local result.
await p.evaluate(()=>{const w=document.querySelector('iframe').contentWindow;w.__creatorOriginalAct=w.eval('act');w.eval("act=()=>new Promise(resolve=>window.__creatorResolve=resolve);window.__creatorPending=takeReviewController.submit();message('저장 중…')");});
await p.screenshot({path:D+'/candidate-saving-390.png'});
await p.fill('#reviewReason','저장 요청 이후 새로 쓴 문장 — 이 내용은 보존돼야 합니다.');
await p.evaluate(async()=>{const w=document.querySelector('iframe').contentWindow;w.__creatorResolve(true);await w.__creatorPending;w.eval('act=window.__creatorOriginalAct');});
results.push(await p.evaluate(()=>{const w=document.querySelector('iframe').contentWindow;return{name:'Newer text survives actual controller deferred save',pass:w.document.querySelector('#reviewReason').value.includes('이 내용은 보존'),mode:w.document.querySelector('.lt-take-review').dataset.reviewMode}}));
// Scene navigation does not persist selection. Draft remains scoped to scene/Take.
await p.evaluate(()=>{const w=document.querySelector('iframe').contentWindow;w.eval("shotName=Object.keys(project().shots)[2];draw();")});
await p.click('#creatorEditReview');
await p.fill('#reviewReason','장면 3의 별도 미저장 검토 메모');
await p.evaluate(()=>{const w=document.querySelector('iframe').contentWindow;w.eval("shotName=Object.keys(project().shots)[1];draw();")});
results.push(await p.evaluate(()=>{const d=document.querySelector('iframe').contentDocument;return{name:'Scene 2 restores own newer draft',pass:d.querySelector('#reviewReason').value.includes('이 내용은 보존')}}));
await p.click('#discardTakeReviewDraft');
await p.evaluate(()=>document.querySelector('iframe').contentWindow.eval("shotName=Object.keys(project().shots)[2];draw();"));
results.push(await p.evaluate(()=>{const d=document.querySelector('iframe').contentDocument;return{name:'Cancel scene 2 does not clear scene 3',pass:d.querySelector('#reviewReason').value==='장면 3의 별도 미저장 검토 메모'}}));
await p.click('#discardTakeReviewDraft');
await p.focus('#creatorEditReview');await p.keyboard.press('Enter');
results.push(await p.evaluate(()=>{const d=document.querySelector('iframe').contentDocument;return{name:'Keyboard edit opens form and moves focus to reason',pass:d.activeElement.id==='reviewReason'&&!d.querySelector('#creatorReviewEditor').hidden}}));
await p.click('#discardTakeReviewDraft');
results.push(await p.evaluate(()=>{const d=document.querySelector('iframe').contentDocument;return{name:'Cancel returns focus to edit action',pass:d.activeElement.id==='creatorEditReview'&&d.querySelector('#creatorReviewEditor').hidden}}));
await p.cdp('Emulation.setDeviceMetricsOverride',{width:320,height:844,deviceScaleFactor:1,mobile:true});
await p.evaluate(()=>{const w=document.querySelector('iframe').contentWindow;w.scrollTo(0,0);w.eval("message('저장했습니다.')");return new Promise(r=>w.requestAnimationFrame(()=>w.requestAnimationFrame(r)))});
results.push(await p.evaluate(()=>{const w=document.querySelector('iframe').contentWindow,d=w.document;return{name:'320px review has no horizontal document overflow',pass:d.documentElement.scrollWidth===w.innerWidth,width:w.innerWidth,scrollWidth:d.documentElement.scrollWidth}}));
await p.screenshot({path:D+'/candidate-review-320.png'});
// Empty state projection, unchanged upload entry point.
await p.evaluate(()=>{const w=document.querySelector('iframe').contentWindow;w.eval("project().shots[shotName].selected=null;draw();")});
results.push(await p.evaluate(()=>{const d=document.querySelector('iframe').contentDocument;return{name:'No Take exposes existing add route',pass:d.querySelector('#upload').closest('details').open&&d.querySelector('#creatorReviewEditor').hidden}}));
await p.screenshot({path:D+'/candidate-empty-320.png'});
await p.evaluate(()=>{const w=document.querySelector('iframe').contentWindow;w.eval("state.projects[song()]=JSON.parse(window.__creatorFixture);draft=null;shotName=Object.keys(project().shots)[0];draw();message('저장했습니다.');")});
await fs.writeFile(D+'/browser-interaction-results.json',JSON.stringify({results,passed:results.every(r=>r.pass),provenance:'Candidate runtime only, deferred action boundary; no POST. No Take and rejected states projected in browser memory.'},null,2));console.log(results);
