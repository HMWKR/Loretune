const fs=await import('node:fs/promises');
const root='/Users/leesungmin/Desktop/Loretune/docs/qa/proposal-draft-fix-20261026/served-baseline';
const spec=JSON.parse(await fs.readFile(root+'/server-start.json','utf8'));
const task=await taskSpace('Loretune served baseline and proposal guards 20261026-0615');
await fs.writeFile(root+'/space.json',JSON.stringify({spaceId:task.spaceId,page:'p1'}));
console.log({spaceId:task.spaceId,url:spec.url});
const p=task.page('p1');
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
await p.cdp('Page.addScriptToEvaluateOnNewDocument',{source:`
window.__baseline={errors:[],requests:[],blocked:[]};
window.addEventListener('error',e=>window.__baseline.errors.push(e.message));
window.addEventListener('unhandledrejection',e=>window.__baseline.errors.push(String(e.reason?.message||e.reason)));
const baselineFetch=window.fetch.bind(window);
window.fetch=(url,options={})=>{const target=new URL(url,location.href),method=options.method||'GET';
window.__baseline.requests.push({path:target.pathname,method});
if(target.origin!==location.origin||method!=='GET'){window.__baseline.blocked.push({path:target.pathname,method});return Promise.reject(Error('QA_NETWORK_BLOCKED'))}
return baselineFetch(url,options)};
navigator.sendBeacon=()=>false;
`});
await p.goto(spec.url);
await p.waitForFunction(()=>document.querySelectorAll('.lt-scene-copy>b').length>0,undefined,{timeout:10000});
const verified=await p.evaluate(async()=>{
 const hashes={};for(const name of ['index.html','studio.css','studio-media.js']){const data=await(await fetch(name==='index.html'?'/':'/'+name)).arrayBuffer();hashes[name]=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',data)),x=>x.toString(16).padStart(2,'0')).join('')}
 return{time:new Date().toISOString(),url:location.href,ua:navigator.userAgent,viewport:[innerWidth,innerHeight],dpr:devicePixelRatio,hashes,errors:window.__baseline.errors,projectCount:document.querySelector('#songs').options.length,scenes:document.querySelectorAll('.lt-scene-copy>b').length};
});
for(const[name,hash]of Object.entries(verified.hashes))if(hash!==spec.source_hashes[name])throw Error('SERVED_SOURCE_HASH_MISMATCH '+name);
await fs.writeFile(root+'/served-source.json',JSON.stringify(verified,null,2));
console.log(verified);
console.log(await p.snapshot());
