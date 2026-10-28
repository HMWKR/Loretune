import fs from 'node:fs/promises';
const D='/Users/leesungmin/Desktop/Loretune/docs/qa/design-benchmark-20261025/creator-pass';
const t=await taskSpace(14),p=t.page('p1');
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});
await p.evaluate(html=>{document.querySelector('iframe').srcdoc=html},await fs.readFile(D+'/candidate-index.html','utf8'));
await p.waitForFunction(()=>[...document.querySelector('iframe').contentDocument.querySelectorAll('#songs option')].some(o=>o.value==='디자인 다중장면 QA 20261025 1330'),undefined,{timeout:10000});
await p.selectOption('#songs',{label:'디자인 다중장면 QA 20261025 1330'});
await p.click('button[data-step="3"]');
await p.evaluate(()=>{const w=document.querySelector('iframe').contentWindow;w.__creatorErrors=[];w.addEventListener('error',e=>w.__creatorErrors.push(e.message));const original=w.fetch;w.__creatorMutations=[];w.fetch=(u,o={})=>{if(o.method&&o.method.toUpperCase()!=='GET'){w.__creatorMutations.push(String(u));return Promise.reject(new Error('Candidate preview is read-only'))}return original(u,o)};w.__creatorFixture=w.eval('JSON.stringify(project())');const v=w.document.querySelector('#preview video');if(v){v.muted=true;return v.play().catch(()=>{})}});
await p.waitForFunction(()=>{const v=document.querySelector('iframe').contentDocument.querySelector('#preview video');return !v||v.currentTime>.12},undefined,{timeout:5000});
await p.evaluate(()=>document.querySelector('iframe').contentDocument.querySelector('#preview video')?.pause());
await p.screenshot({path:D+'/candidate-approved-1280.png'});
const geo=await p.evaluate(()=>{const w=document.querySelector('iframe').contentWindow,d=w.document;const box=s=>{const r=d.querySelector(s).getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height,bottom:r.bottom}};return{width:w.innerWidth,shell:box('.lt-studio-shell'),stage:box('.lt-stage-bar'),preview:box('#preview'),timeline:box('#ltTimelineDock'),review:box('.lt-take-review'),mode:d.querySelector('.lt-take-review').dataset.reviewMode,saveHidden:d.querySelector('#creatorReviewEditor').hidden,scrollWidth:d.documentElement.scrollWidth,errors:w.__creatorErrors}});
await fs.writeFile(D+'/candidate-geometry-desktop.json',JSON.stringify(geo,null,2));console.log(geo);
await p.cdp('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
await p.click('loc=role:tab[name="검토"]');
await p.evaluate(()=>{const w=document.querySelector('iframe').contentWindow;w.scrollTo(0,0);return new Promise(r=>w.requestAnimationFrame(()=>w.requestAnimationFrame(r)))});
await p.screenshot({path:D+'/candidate-approved-390.png'});
console.log(await p.snapshot());

{
await p.cdp('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
const results=[];
async function record(name){const v=await p.evaluate(()=>{const w=document.querySelector('iframe').contentWindow,d=w.document;w.scrollTo(0,0);d.querySelector('.inspector').scrollTop=0;const mode=d.querySelector('.lt-take-review').dataset.reviewMode;const b=d.querySelector(mode==='read'?'#creatorEditReview':'#reviewTake');const r=b.getBoundingClientRect();return{mode,identity:d.querySelector('#creatorMobileContext').innerText,action:b.textContent,actionBottom:r.bottom,actionHeight:r.height,width:w.innerWidth,scrollWidth:d.documentElement.scrollWidth,draft:d.querySelector('#reviewReason').value,decision:d.querySelector('#takeDecision').value}});results.push({name,...v});await p.screenshot({path:D+'/candidate-'+name+'-390.png'});}
await record('approved');
await p.evaluate(()=>{const w=document.querySelector('iframe').contentWindow;w.eval("shotName=Object.keys(project().shots)[2];project().shots[shotName].reviews.push({take:1,decision:'rejected',reason:'후보 투영: 마지막 장면의 색감이 맞지 않아 다시 검토합니다.'});draw();");});
await record('rejected');
await p.evaluate(()=>{const w=document.querySelector('iframe').contentWindow;w.eval("shotName=Object.keys(project().shots)[1];project().shots[shotName].selected=1;takeReviewStore.clear(currentTakeReview().key);draw();");});
await record('unreviewed');
await p.selectOption('#takeDecision','changes_requested');await p.fill('#reviewReason','후보 QA 초안 · 장면 2의 대비와 연결을 다시 검토합니다.');
await record('dirty');
await p.evaluate(()=>document.querySelector('iframe').contentWindow.eval("message('네트워크 연결 timeout · candidate-only injected error',true)"));
await record('error');
const e=await p.evaluate(()=>{const w=document.querySelector('iframe').contentWindow,d=w.document;return{notice:d.querySelector('#notice').innerText,detail:d.querySelector('[data-creator-error]')?.textContent,formValue:d.querySelector('#reviewReason').value,errors:w.__creatorErrors,requestsBlocked:w.__creatorMutations}});
await fs.writeFile(D+'/candidate-mobile-states.json',JSON.stringify({provenance:'Browser-only projections from existing local synthetic fixture; no API writes. Rejected review is injected, unreviewed Take already existed, selection changed in browser memory only.',results,error:e},null,2));console.log({results,error:e});

}
await p.evaluate(()=>{const w=document.querySelector('iframe').contentWindow;w.eval("takeReviewStore.clear(currentTakeReview().key);state.projects[song()]=JSON.parse(window.__creatorFixture);draft=null;shotName=Object.keys(project().shots)[0];draw();message('저장했습니다.');")});

{
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false});
async function capture(name){await p.evaluate(()=>{const w=document.querySelector('iframe').contentWindow;w.scrollTo(0,0);return new Promise(r=>w.requestAnimationFrame(()=>w.requestAnimationFrame(r)))});await p.screenshot({path:D+'/candidate-'+name+'-1280.png'});await fs.writeFile(D+'/candidate-'+name+'-text.txt',await p.evaluate(()=>document.querySelector('iframe').contentDocument.body.innerText));}
await p.click('#compareButton');await capture('comparison');await p.keyboard.press('Escape');
await p.click('button[data-step="1"]');await capture('music');
await p.click('button[data-step="2"]');await capture('plan');
await p.click('#editModelSettings');await capture('models');await p.keyboard.press('Escape');
await p.click('.management>summary');await p.click('#newProject');await capture('project');await p.keyboard.press('Escape');
await p.evaluate(()=>document.querySelector('iframe').contentDocument.querySelector('.management').open=false);
await p.click('button[data-step="4"]');
console.log(await p.evaluate(()=>{const d=document.querySelector('iframe').contentDocument;return{jobs:d.querySelector('#jobs').innerText,playCount:d.querySelectorAll('[data-play]').length}}));
await p.click('[data-play]');await capture('output');
const final=await p.evaluate(()=>{const w=document.querySelector('iframe').contentWindow,d=w.document;return{errors:w.__creatorErrors,mutations:w.__creatorMutations,projectUnchanged:w.eval('JSON.stringify(project())')===w.__creatorFixture,duplicateIds:[...d.querySelectorAll('[id]')].map(x=>x.id).filter((id,i,a)=>a.indexOf(id)!==i),identity:d.querySelector('#creatorMobileContext').innerText}});
await fs.writeFile(D+'/candidate-primary-results.json',JSON.stringify(final,null,2));console.log(final);

}
