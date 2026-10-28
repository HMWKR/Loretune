import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const source=fs.readFileSync(new URL('./review-state.js',import.meta.url),'utf8');
const functionSource=source.slice(source.indexOf('function openStudioComparison(){'),source.indexOf('function installStudioNotice('));
const results=[];
for(const {name,ids,selected,expected} of [
 {name:'zero Takes: explain without opening',ids:[],selected:null,expected:null},
 {name:'single Take: explain without duplicate comparison',ids:[1],selected:1,expected:null},
 {name:'selected last Take: choose distinct earlier Take',ids:[1,2],selected:2,expected:['2','1']},
 {name:'selected first Take: compare with latest alternative',ids:[1,2,3],selected:1,expected:['1','3']},
 {name:'no selection: first and last distinct',ids:[1,2,3],selected:null,expected:['1','3']}
]){
 let shown=0,drawn=0;const messages=[];
 const select=()=>({innerHTML:'',get value(){return this._value||''},set value(x){this._value=String(x)}});
 const elements={'#compareLeft':select(),'#compareRight':select(),'#compareDialog':{showModal(){shown++}}};
 const shot={takes:ids.map(id=>({id})),selected};const before=JSON.stringify(shot);
 const ctx={project:()=>({shots:{qa:shot}}),shotName:'qa',message:(...args)=>messages.push(args),$:id=>elements[id],studioReview:()=>({label:'Take 검토 대기'}),esc:String,drawComparison:()=>drawn++};
 vm.createContext(ctx);vm.runInContext(functionSource,ctx);ctx.openStudioComparison();
 if(expected){assert.deepEqual([elements['#compareLeft'].value,elements['#compareRight'].value],expected);assert.equal(shown,1);assert.equal(drawn,1)}else{assert.equal(shown,0);assert.equal(drawn,0);assert.equal(messages.length,1)}
 assert.equal(JSON.stringify(shot),before,'opening comparison must not change selection/reviews');
 results.push({name,passed:true});
}
console.log(`${results.length} comparison behavior tests passed`);
