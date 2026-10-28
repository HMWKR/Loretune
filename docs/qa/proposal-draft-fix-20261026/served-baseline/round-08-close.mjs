const fs=await import('node:fs/promises'),root='/Users/leesungmin/Desktop/Loretune/docs/qa/proposal-draft-fix-20261026/served-baseline';
const task=await taskSpace(37),p=task.page('p1');
const declarations=await p.evaluate(()=>{
 const probes={'#sequenceTime':['font-family','font-size','font-weight'],'#compareTime':['font-family'],'.skip-link':['color','background-color','background','padding'],'.lt-timeline-controls>summary':['padding','font-size'],'.clip-row input':['padding','font-size'],'#compareButton':['padding','min-height','font-weight'],'#audioInfo svg':['background-color'],'#audioInfo polyline':['stroke'],'#preferenceForm input[name=value]':['color','padding'],'#preferencesDialog':['color']};
 return Object.entries(probes).map(([selector,props])=>{const el=document.querySelector(selector),computed=getComputedStyle(el),matches=[];
  function walk(rules,source){for(const rule of rules){if(rule instanceof CSSMediaRule&&!matchMedia(rule.conditionText).matches)continue;
   if(rule.selectorText){let match=false;try{match=el.matches(rule.selectorText)}catch{}if(match){const declarations=Object.fromEntries(props.map(prop=>[prop,rule.style.getPropertyValue(prop)]).filter(x=>x[1]));if(Object.keys(declarations).length)matches.push({source,selector:rule.selectorText,declarations})}}
   if(rule.cssRules?.length)walk(rule.cssRules,source);
  }}
  for(const sheet of document.styleSheets)walk(sheet.cssRules,sheet.href?new URL(sheet.href).pathname:'inline');
  return {selector,computed:Object.fromEntries(props.map(prop=>[prop,computed.getPropertyValue(prop)])),inline:el.getAttribute('style'),attributes:{stroke:el.getAttribute('stroke')},matchingRulesInSourceOrder:matches};
 });
});
await fs.writeFile(root+'/active-declarations-verified.json',JSON.stringify(declarations,null,2));
const final=await p.evaluate(async()=>{
 const sourceHashes={};for(const path of ['/','/studio.css','/studio-media.js']){const r=await fetch(path);sourceHashes[path]=[...new Uint8Array(await crypto.subtle.digest('SHA-256',await r.arrayBuffer()))].map(b=>b.toString(16).padStart(2,'0')).join('')}
 LoretuneMedia.stop();for(const v of document.querySelectorAll('video,audio'))v.pause();
 return {time:new Date().toISOString(),userAgent:navigator.userAgent,sourceHashes,projectUnchanged:JSON.stringify(project())===window.__baselineSaved.project,revision:state.revision,dirty,pending:!!pendingId(),unhandledErrors:window.__baseline.errors,guardCases:window.__guardQA.results.length,guardPassed:window.__guardQA.results.filter(x=>x.pass).length,mockedPosts:window.__guardQA.calls.length,mockedExistingRequestLookups:window.__guardQA.lookups,blockedTransportAttempts:window.__baseline.blocked,unexpectedExternalResources:performance.getEntriesByType('resource').map(x=>x.name).filter(x=>/^https?:/.test(x)&&new URL(x).origin!==location.origin),requestSummary:window.__baseline.requests.reduce((m,x)=>(m[x.method+' '+x.path]=(m[x.method+' '+x.path]||0)+1,m),{})};
});
await fs.writeFile(root+'/browser-final.json',JSON.stringify(final,null,2));
console.log(final);
await task.finish({keep:[]});
await fs.writeFile(root+'/space-closed.json',JSON.stringify({spaceId:37,closed:true,time:new Date().toISOString(),kept:[]},null,2));
console.log({spaceId:37,closed:true});
