'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(path.join(__dirname,'snapshot/index.html'),'utf8'),source=html.split('<script id="loretuneDesktopLayout">')[1].split('</script>')[0];
class Node{
 constructor(id){this.id=id;this.childNodes=[];this.listeners={};this.attrs={};this.dataset={};this.hidden=false;this.rect={left:0,right:100};this.clientWidth=500;this.value='';this.visible=true;}
 get children(){return this.childNodes;}
 append(n){if(n.parent)n.parent.childNodes=n.parent.childNodes.filter(x=>x!==n);this.childNodes.push(n);n.parent=this;}
 prepend(n){this.append(n);this.childNodes.pop();this.childNodes.unshift(n);}
 setAttribute(k,v){this.attrs[k]=v;}
 addEventListener(k,f){(this.listeners[k]??=[]).push(f);}
 getBoundingClientRect(){return this.rect;}
 getClientRects(){return this.visible?[this.rect]:[];}
}
const media=new Node('media'),dock=new Node('dock'),preview=new Node('preview'),anchor=new Node('return-anchor'),form=new Node('form'),scale=new Node('scale');scale.value='1';form.value='미저장 검토 초안';preview.currentTime=2.25;for(const n of [anchor,preview,form,dock])media.append(n);
let ruler=new Node('ruler');const mkLabels=bounds=>{ruler.childNodes=bounds.map((b,i)=>Object.assign(new Node('tick'+i),{rect:b}));};mkLabels([{left:0,right:120},{left:90,right:210},{left:180,right:300}]);
const body=new Node('body'),registry={'.lt-media-pane':media,'#ltTimelineDock':dock,'#textScale':scale},mutations=[],resizes=[],globalListeners={},frames=new Map();let next=0,writeCalls=0;
const doc={body,activeElement:form,fonts:{ready:Promise.resolve()},querySelector:s=>s==='#timeRuler'?ruler:registry[s],createElement:()=>new Node('stage')};
const ctx={document:doc,innerWidth:1920,innerHeight:1080,Set,Number,requestAnimationFrame:f=>{frames.set(++next,f);return next;},addEventListener:(k,f)=>(globalListeners[k]??=[]).push(f),ResizeObserver:class{constructor(fn){this.fn=fn;this.observed=[];this.disconnects=0;resizes.push(this)}observe(n){this.observed.push(n)}disconnect(){this.observed=[];this.disconnects++}},MutationObserver:class{constructor(fn){this.fn=fn;mutations.push(this)}observe(n,opt){this.target=n;this.options=opt}},fetch:()=>{writeCalls++;throw Error('network forbidden')},act:()=>{writeCalls++;throw Error('mutation forbidden')},localStorage:new Proxy({},{get(){throw Error('storage access forbidden')}})};
vm.createContext(ctx);vm.runInContext(source,ctx);const results=[];
function test(name,fn){fn();results.push({name,status:'pass'});}
function flush(){const batch=[...frames.values()];frames.clear();for(const f of batch)f();}
const tick=()=>{for(const m of mutations)m.fn();for(const r of resizes)r.fn();for(const f of globalListeners.resize||[])f();for(const f of scale.listeners.change||[])f();};
(async()=>{
await Promise.resolve();flush();
test('actual nodes and return anchor moved once; draft/media position retained',()=>{const stage=media.childNodes[0];assert.equal(stage.attrs.role,'region');assert.equal(stage.tabIndex,0);assert.equal(stage.childNodes[0],anchor);assert.equal(stage.childNodes[1],preview);assert.equal(stage.childNodes[2],form);assert.equal(dock.parent,media);assert.equal(form.value,'미저장 검토 초안');assert.equal(preview.currentTime,2.25);assert.equal(doc.activeElement,form);});
test('overlap hides only intermediate labels and leaves endpoints',()=>{assert.deepEqual(ruler.children.map(n=>n.hidden),[false,true,false]);assert.equal(ruler.dataset.stacked,'false');});
test('labels reappear on wider measured bounds',()=>{ruler.children[1].rect={left:150,right:270};ruler.children[2].rect={left:300,right:420};tick();flush();assert.deepEqual(ruler.children.map(n=>n.hidden),[false,false,false]);});
test('endpoint collision enters stack then unsets when space returns',()=>{ruler.children[2].rect={left:80,right:200};tick();flush();assert.equal(ruler.dataset.stacked,'true');assert.equal(ruler.children[0].hidden,false);assert.equal(ruler.children[2].hidden,false);ruler.children[2].rect={left:300,right:420};tick();flush();assert.equal(ruler.dataset.stacked,'false');});
test('text-scale and small-window transitions preserve draft and pointers',()=>{for(const x of [[1920,1080,'1','bounded'],[1920,1080,'1.5','flow'],[1920,1080,'2','flow'],[1099,1080,'1','flow'],[1920,799,'1','flow'],[1100,800,'1','bounded']]){[ctx.innerWidth,ctx.innerHeight,scale.value]=x;tick();flush();assert.equal(body.dataset.desktopShell,x[3]);assert.equal(form.value,'미저장 검토 초안');assert.equal(preview.currentTime,2.25);assert.equal(doc.activeElement,form);}});
test('500 notifications coalesce with no listener or observer multiplication',()=>{const stage=media.childNodes[0];for(let i=0;i<500;i++)tick();assert.equal(frames.size,1);flush();assert.equal(frames.size,0);assert.equal(globalListeners.resize.length,1);assert.equal(scale.listeners.change.length,1);assert.equal(mutations.length,2);assert.equal(resizes.length,1);assert.equal(media.childNodes[0],stage);assert.deepEqual(Array.from(mutations[1].options.attributeFilter),['data-step','data-guided']);});
test('replaced ruler disconnects old observation; hidden then shown remains operable',()=>{const old=ruler;ruler=new Node('new-ruler');mkLabels([{left:0,right:120},{left:90,right:210},{left:180,right:300}]);ruler.visible=false;tick();flush();assert.equal(resizes[0].observed[0],ruler);assert(!resizes[0].observed.includes(old));ruler.visible=true;tick();flush();assert.deepEqual(ruler.children.map(n=>n.hidden),[false,true,false]);});
test('no network mutation storage focus or media playback side effects',()=>{assert.equal(writeCalls,0);assert.equal(doc.activeElement,form);for(const banned of ['fetch(', 'act(', 'cloneNode', '.focus(', '.play(', 'localStorage', 'replaceChildren'])assert(!source.includes(banned));});
console.log(JSON.stringify({type:'real presentation adapter in controlled DOM geometry; not rendered CSS/browser',results},null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
