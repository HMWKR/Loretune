const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),{createRequire}=require('node:module');
(async()=>{
 const root=process.cwd(),audit=path.join(root,'docs/qa/frontend-functional-independent-20261026'),base=process.argv[2]==='before'?path.join(root,'docs/qa/frontend-fq-vq-fixes-20261026/before'):root;
 const name=path.join(audit,'suite.cjs'),native=createRequire(name),results=[];
 let source=fs.readFileSync(name,'utf8').replaceAll('vm.createContext(ctx);',`Object.assign(ctx,{stateReadEpoch:0,pollSequence:0,appliedPollSequence:0,pollReadsInFlight:0,shotName:'A'});vm.createContext(ctx);if(html.includes('function updateRecovery('))vm.runInContext(line('function updateRecovery('),ctx);`);
 source=source.replace('0bfdbbb815c631f23e9188a02a1308aa87430d2db33ab61f4a60f8b7adfdf109',require('node:crypto').createHash('sha256').update(fs.readFileSync(path.join(base,'index.html'))).digest('hex'));
 const wrappedFs={...fs,readFileSync:(p,...args)=>fs.readFileSync(String(p).startsWith(path.join(audit,'snapshot'))?String(p).replace(path.join(audit,'snapshot'),base):p,...args),writeFileSync:(p,b)=>results.push({name:path.basename(p),value:JSON.parse(b)})};
 process.env.LORETUNE_MEDIA_SOURCE=path.join(base,'studio-media.js');
 await vm.runInNewContext(source,{require:n=>n==='node:fs'?wrappedFs:n==='./snapshot/studio-media.js'?require(path.join(base,'studio-media.js')):n==='./snapshot/tests/media_async_harness.cjs'?require(path.join(root,'tests/media_async_harness.cjs')):native(n),__dirname:audit,console:{log(){},error:console.error},process:{version:process.version},queueMicrotask});
 const r=results.find(x=>x.name==='vm-results.json').value;
 console.log(JSON.stringify({source:base,results:r.results,forwarded:results.find(x=>x.name==='request-ledger.json').value.forwarded},null,2));
})().catch(e=>{console.error(e);process.exitCode=2});
