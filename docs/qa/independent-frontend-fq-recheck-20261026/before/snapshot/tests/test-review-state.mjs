import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const path=new URL('./review-state.js',import.meta.url);
const core=fs.readFileSync(path,'utf8').split('// DOM glue.')[0];
const ctx={};vm.createContext(ctx);vm.runInContext(core,ctx);
const results=[];const test=async(name,fn)=>{await fn();results.push({name,passed:true})};
function memory(){const m=new Map();return{getItem:k=>m.get(k)||null,setItem:(k,v)=>m.set(k,v),removeItem:k=>m.delete(k)}}
function fixture(){const storage=memory(),store=ctx.createTakeReviewStore(storage);let current={key:'A',song:'qa',shot:'one',take:1},value={decision:'approved',reason:'A reason'},resolve,calls=[];const controller=ctx.createTakeReviewController({store,context:()=>current,inputs:()=>({...value}),save:(action,payload)=>{calls.push({action,payload});return new Promise(r=>resolve=r)},render:()=>{},notify:()=>false});return{storage,store,controller,calls,setContext:c=>current=c,setValue:v=>value=v,resolve:ok=>resolve(ok)}}
await test('keys include workspace/project/scene/Take without delimiter collisions',()=>{assert.notEqual(ctx.takeReviewKey('w','a:b','c',1),ctx.takeReviewKey('w','a','b:c',1));assert.notEqual(ctx.takeReviewKey('w','a','b',1),ctx.takeReviewKey('w','a','b',2))});
await test('draft survives store recreation and remains isolated',()=>{const f=fixture();f.controller.capture();const restored=ctx.createTakeReviewStore(f.storage);assert.equal(restored.get('A').reason,'A reason');assert.equal(restored.get('B'),null)});
await test('failed save retains submitted draft',async()=>{const f=fixture();const p=f.controller.submit();f.resolve(false);assert.equal(await p,false);assert.equal(f.store.get('A').reason,'A reason')});
await test('successful save clears unchanged submitted draft only',async()=>{const f=fixture();const p=f.controller.submit();f.resolve(true);await p;assert.equal(f.store.get('A'),null)});
await test('typing during save preserves newer input even if value later repeats',async()=>{const f=fixture();const p=f.controller.submit();f.setValue({decision:'rejected',reason:'new'});f.controller.capture();f.setValue({decision:'approved',reason:'A reason'});f.controller.capture();f.resolve(true);await p;assert.ok(f.store.get('A'));assert.equal(f.store.get('A').reason,'A reason')});
await test('context switch during save does not clear destination draft',async()=>{const f=fixture();const p=f.controller.submit();f.setContext({key:'B',song:'other',shot:'two',take:2});f.setValue({decision:'rejected',reason:'B reason'});f.controller.capture();f.resolve(true);await p;assert.equal(f.store.get('B').reason,'B reason');assert.equal(f.calls[0].payload.shot,'one');assert.equal(f.calls[0].payload.take,1)});
await test('repeat click while pending sends one request',async()=>{const f=fixture();const p=f.controller.submit();assert.equal(await f.controller.submit(),false);assert.equal(f.calls.length,1);f.resolve(true);await p});
await test('unchanged saved review and missing decision do not submit',async()=>{const f=fixture();f.setContext({key:'A',song:'qa',shot:'one',take:1,review:{decision:'approved',reason:'A reason'}});await f.controller.submit();assert.equal(f.calls.length,0);f.setContext({key:'A',song:'qa',shot:'one',take:1});f.setValue({decision:'',reason:'text'});await f.controller.submit();assert.equal(f.calls.length,0)});
await test('storage failure keeps draft in memory and exposes failure',()=>{const storage={getItem(){throw Error()},setItem(){throw Error()},removeItem(){throw Error()}};const store=ctx.createTakeReviewStore(storage);store.set('A',{decision:'approved',reason:'text'});assert.equal(store.get('A').reason,'text');assert.equal(store.failed,true)});
console.log(`${results.length} focused draft tests passed`);
