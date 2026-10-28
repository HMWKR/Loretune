import fs from 'node:fs/promises';const D='/Users/leesungmin/Desktop/Loretune/docs/qa/design-benchmark-20261025/creator-pass';
const t=await taskSpace(14),p=t.page('p1');
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
