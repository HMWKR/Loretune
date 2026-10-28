import fs from 'node:fs/promises';const D='/Users/leesungmin/Desktop/Loretune/docs/qa/design-benchmark-20261025/creator-pass';const t=await taskSpace(14),p=t.page('p1');
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
