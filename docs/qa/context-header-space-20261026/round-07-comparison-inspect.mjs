const task=await taskSpace(40),p=task.page('p1');
console.log(await p.evaluate(()=>({viewport:[innerWidth,innerHeight],dialog:document.querySelector('#compareDialog').open,left:document.querySelector('#compareLeft').value,right:document.querySelector('#compareRight').value,videos:[...document.querySelectorAll('#compareDialog video')].map(v=>({readyState:v.readyState,error:v.error?.code,currentTime:v.currentTime,paused:v.paused})),images:[...document.querySelectorAll('#compareDialog img')].length,dirty,pending:!!pendingRequest})));
console.log(await p.snapshot());
