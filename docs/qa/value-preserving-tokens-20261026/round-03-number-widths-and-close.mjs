const fs=await import('node:fs/promises'),root='/Users/leesungmin/Desktop/Loretune/docs/qa/value-preserving-tokens-20261026';
const task=await taskSpace(39),p=task.page('p1');
await p.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
const widths=await p.evaluate(()=>{
 const samples=['00:00.000','11:11.111','88:88.888','00:00.500 / 00:07.000'],results=[];
 for(const selector of ['#sequenceTime','#compareTime']){
  const c=getComputedStyle(document.querySelector(selector));
  const probe=document.createElement('span');Object.assign(probe.style,{position:'fixed',left:'-10000px',top:'0',whiteSpace:'pre',width:'max-content',fontSize:c.fontSize,fontWeight:c.fontWeight,fontStyle:c.fontStyle,fontVariantNumeric:c.fontVariantNumeric,lineHeight:c.lineHeight});document.body.append(probe);
  const measure=family=>{probe.style.fontFamily=family;return samples.map(text=>{probe.textContent=text;return {text,width:probe.getBoundingClientRect().width}})};
  const token=measure('var(--ui-font-timecode)'),legacy=measure('ui-monospace,monospace');probe.remove();
  results.push({selector,actualFamily:c.fontFamily,size:c.fontSize,weight:c.fontWeight,numericVariant:c.fontVariantNumeric,token,legacy,identical:JSON.stringify(token)===JSON.stringify(legacy)});
 }
 return {time:new Date().toISOString(),viewport:[innerWidth,innerHeight],dpr:devicePixelRatio,method:'Actual DOM span widths with current numeric variant and font size; temporary probes removed. Earlier Canvas c.font shorthand measurements are superseded.',results};
});
if(widths.results.some(x=>!x.identical))throw Error('NUMERAL_WIDTH_CHANGED');
await fs.writeFile(root+'/verified-numeral-widths.json',JSON.stringify(widths,null,2));
const final=await p.evaluate(async()=>{
 const hashes={};for(const path of ['/','/studio.css','/studio-media.js']){const r=await fetch(path);hashes[path]=[...new Uint8Array(await crypto.subtle.digest('SHA-256',await r.arrayBuffer()))].map(b=>b.toString(16).padStart(2,'0')).join('')}
 LoretuneMedia.stop();for(const v of document.querySelectorAll('video,audio'))v.pause();
 return {time:new Date().toISOString(),hashes,projectUnchanged:JSON.stringify(project())===window.__parityOriginalProject,dirty,pending:!!pendingId(),errors:window.__baseline.errors,blocked:window.__baseline.blocked,nonGet:window.__baseline.requests.filter(x=>x.method!=='GET'),externalResources:performance.getEntriesByType('resource').map(x=>x.name).filter(x=>/^https?:/.test(x)&&new URL(x).origin!==location.origin)};
});
await fs.writeFile(root+'/browser-final.json',JSON.stringify(final,null,2));
console.log({numeric:widths.results,final});
await task.finish({keep:[]});
await fs.writeFile(root+'/space-closed.json',JSON.stringify({spaceId:39,closed:true,kept:[],time:new Date().toISOString()},null,2));
console.log({closed:true,spaceId:39});
