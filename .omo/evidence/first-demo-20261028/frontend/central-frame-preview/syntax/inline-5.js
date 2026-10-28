
// Presentation only: no media clock, project mutation, approval or storage calls.
function desktopShellMode(width,height,scale){return width>=1100&&height>=800&&Number(scale)<=1.25?'bounded':'flow'}
function visibleTimelineLabels(bounds,gap=12){
 if(bounds.length<2)return bounds.map((_,i)=>i);
 const keep=[0],end=bounds.length-1;let right=bounds[0].right;
 for(let i=1;i<end;i++)if(bounds[i].left>=right+gap&&bounds[i].right<=bounds[end].left-gap){keep.push(i);right=bounds[i].right}
 keep.push(end);return keep;
}
(() => {
 const q=s=>document.querySelector(s),media=q('.lt-media-pane'),dock=q('#ltTimelineDock');if(!media||!dock)return;
 const stage=document.createElement('div');stage.className='lt-preview-stage';stage.setAttribute('role','region');stage.setAttribute('aria-label','현재 장면 미리보기와 Take');stage.tabIndex=0;
 // Move the actual player, its return anchor and forms; never clone or reset them.
 for(const node of [...media.childNodes])if(node!==dock)stage.append(node);
 media.prepend(stage);
 let pending=0,observed=null;const resize=new ResizeObserver(schedule);
 function fit(){
  pending=0;document.body.dataset.desktopShell=desktopShellMode(innerWidth,innerHeight,q('#textScale').value);
  const ruler=q('#timeRuler');if(!ruler)return;
  if(observed!==ruler){resize.disconnect();resize.observe(ruler);observed=ruler}
  const labels=[...ruler.children];labels.forEach(e=>e.hidden=false);
  if(!ruler.getClientRects().length||!ruler.clientWidth)return;
  const bounds=labels.map(e=>e.getBoundingClientRect()),keep=new Set(visibleTimelineLabels(bounds));
  ruler.dataset.stacked=String(bounds.length>1&&bounds.at(-1).left<bounds[0].right+12);
  labels.forEach((e,i)=>e.hidden=!keep.has(i));
 }
 function schedule(){if(!pending)pending=requestAnimationFrame(fit)}
 new MutationObserver(schedule).observe(dock,{childList:true,subtree:true});
 new MutationObserver(schedule).observe(document.body,{attributes:true,attributeFilter:['data-step','data-guided']});
 addEventListener('resize',schedule);q('#textScale').addEventListener('change',schedule);
 document.fonts?.ready.then(schedule);schedule();
})();
