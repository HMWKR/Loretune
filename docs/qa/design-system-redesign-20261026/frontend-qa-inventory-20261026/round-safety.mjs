// QA-only: no application source changes. Reinstall each Ego invocation.
export async function protect(p) {
  return p.evaluate(() => {
    if (window.__visualGuard) return window.__visualGuard;
    const guard = window.__visualGuard = {blocked: [], requests: []};
    const allowed = (url, method) => {
      const u = new URL(url, location.href);
      return u.origin === location.origin && ['GET','HEAD'].includes(method.toUpperCase());
    };
    const originalFetch = window.fetch.bind(window);
    window.fetch = (input, options={}) => {
      const url = typeof input === 'string' ? input : input.url;
      const method = options.method || input.method || 'GET';
      const entry = {url,method};
      if (!allowed(url,method)) {guard.blocked.push(entry); return Promise.reject(new Error('Read-only QA request blocked'));}
      guard.requests.push(entry); return originalFetch(input,options);
    };
    const open = XMLHttpRequest.prototype.open, send = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function(method,url,...rest) {this.__qaRequest={method,url}; return open.call(this,method,url,...rest);};
    XMLHttpRequest.prototype.send = function(...args) {
      const r=this.__qaRequest;
      if (!r || !allowed(r.url,r.method)) {guard.blocked.push(r||{type:'xhr'}); throw new Error('Read-only QA request blocked');}
      guard.requests.push(r); return send.apply(this,args);
    };
    navigator.sendBeacon=()=>false;
    document.addEventListener('submit',event=>{event.preventDefault();event.stopImmediatePropagation();guard.blocked.push({type:'form-submit'});},true);
    const meta=document.createElement('meta');meta.httpEquiv='Content-Security-Policy';
    meta.content="connect-src 'self'; img-src 'self' data: blob:; media-src 'self' data: blob:; form-action 'none'; frame-src 'none'";
    document.head.append(meta);
    return {installed:true,fetchWrapper:!String(window.fetch).includes('[native code]')};
  });
}
export async function activeBounds(p) {
  return p.evaluate(() => {
    const e=document.activeElement,r=e.getBoundingClientRect(),s=getComputedStyle(e);
    let clip={left:0,top:0,right:innerWidth,bottom:innerHeight};
    for(let n=e.parentElement;n;n=n.parentElement){const c=getComputedStyle(n),b=n.getBoundingClientRect();if(/auto|scroll|hidden|clip/.test(c.overflowX)){clip.left=Math.max(clip.left,b.left);clip.right=Math.min(clip.right,b.right);}if(/auto|scroll|hidden|clip/.test(c.overflowY)){clip.top=Math.max(clip.top,b.top);clip.bottom=Math.min(clip.bottom,b.bottom);}}
    const visibleWidth=Math.max(0,Math.min(r.right,clip.right)-Math.max(r.left,clip.left)),visibleHeight=Math.max(0,Math.min(r.bottom,clip.bottom)-Math.max(r.top,clip.top));
    const hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);
    return {tag:e.tagName,id:e.id,text:(e.getAttribute('aria-label')||e.textContent||'').trim().slice(0,90),rect:r.toJSON(),clip,partlyVisible:visibleWidth>0&&visibleHeight>0,fullyVisible:visibleWidth>=r.width-1&&visibleHeight>=r.height-1,centerHit:hit===e||e.contains(hit),outline:s.outline,offset:s.outlineOffset,disabled:e.disabled??null};
  });
}
