/* Optional local 3D still composition. Server approvals remain authoritative. */
(() => {
 const button=document.createElement('button');button.type='button';button.id='sceneStudioButton';button.textContent='3D 장면 만들기';button.setAttribute('aria-haspopup','dialog');
 const help=document.createElement('p');help.id='sceneStudioButtonHelp';help.className='muted';help.textContent='선택 사항입니다. 사진 없이 도형이나 3D 자산으로 구도를 정합니다.';button.setAttribute('aria-describedby',help.id);
 const motion=document.getElementById('motionButton'),review=document.getElementById('takeReviewStatus');
 if(motion?.after)motion.after(button);else if(review?.after)review.after(button);else (document.getElementById('productionTools')||document.querySelector('.inspector')).append(button);
 button.after(help);
 const dialog=document.createElement('dialog');dialog.id='sceneStudioDialog';dialog.setAttribute('aria-labelledby','sceneStudioTitle');
 dialog.innerHTML=`<div class="row"><h2 id="sceneStudioTitle">3D 장면 만들기</h2><button type="button" id="sceneStudioClose">닫기</button></div>
 <p>도형이나 가져온 3D 자산의 구도·빛을 정해 정지 이미지 후보를 만듭니다.</p><details class="lt-provenance-detail"><summary>지원 범위와 입력 보관</summary><p>사진은 필요하지 않습니다. 실시간 미리보기와 움직임은 아직 지원하지 않습니다. 입력은 이 탭에 보관됩니다.</p></details>
 <p id="sceneStudioContext"></p><p id="sceneStudioCapability" role="status"></p><p id="sceneStudioStorageWarning" role="status" hidden>브라우저 저장소를 확인하지 못했습니다. 입력은 이 페이지에서만 유지되며 새로고침하면 사라질 수 있습니다.</p><p id="sceneStudioStatus" class="dialog-status" role="status" aria-live="polite"></p>
 <div class="toolbar"><button type="button" id="sceneStudioRecover" hidden>기존 요청 확인</button><button type="button" id="sceneStudioRetry" hidden>같은 3D 요청 다시 보내기</button></div>
 <details class="scene-studio-section" id="sceneStudioAssetPanel"><summary>3D 자산 가져오기</summary>
 <p>작은 정지 GLB 파일을 사용할 수 있습니다. 파일은 8MB까지이며 외부 자료를 참조하거나 지원하지 않는 구조가 있으면 가져올 수 없습니다.</p>
 <label>GLB 파일<input type="file" id="sceneStudioAssetFile" accept=".glb,model/gltf-binary" aria-describedby="sceneStudioAssetFileName"></label><p id="sceneStudioAssetFileName"></p>
 <label>이 파일의 사용권 근거<input id="sceneStudioAssetRights" type="text" maxlength="2000" placeholder="직접 제작 또는 사용 허가 근거"></label>
 <button type="button" id="sceneStudioAssetImport">가져와 현재 대상에 사용</button>
 <label>이 대화에서 가져온 자산<select id="sceneStudioAssetSelect"></select></label><button type="button" id="sceneStudioAssetUse">선택한 자산을 현재 대상에 사용</button>
 <p>사용하면 현재 대상의 모양을 교체하는 초안이 됩니다. 위치·회전·크기는 유지됩니다.</p></details>
 <fieldset id="sceneStudioInputs"><legend>구성</legend><div id="sceneStudioFields"></div></fieldset>
 <p class="lt-cost-facts" id="sceneStudioApprovalScope">저장은 변경안이며, 구성 승인과 Take 선택·사용권 검토는 각각 별도입니다.</p>
 <div class="toolbar"><button type="button" id="sceneStudioSave">변경안 저장</button><button type="button" id="sceneStudioDiscard">저장 전 입력 취소</button></div>
 <p id="sceneStudioSummary"></p><div class="toolbar"><button type="button" id="sceneStudioApprove" aria-describedby="sceneStudioApprovalScope">확인한 구성 승인</button><button type="button" id="sceneStudioRender">정지 이미지 후보 만들기</button></div>
 <div class="row" id="sceneStudioRestoreRow" hidden><label>이전 구성<select id="sceneStudioVersions"></select></label><button type="button" id="sceneStudioRestore">새 변경안으로 복원</button></div>
 <div id="sceneStudioJobs" aria-live="polite"></div>`;
 document.body.append(dialog);
 const el=id=>document.getElementById(id),drafts=new Map(),imports=new Map(),MAX_ASSET_BYTES=8*1024*1024,RENDER_REQUESTED='이미지 후보 생성 요청을 확인했습니다. 창을 닫아도 작업은 계속됩니다.';
 const initial=()=>({schema_version:1,width:480,height:270,background:[0.1,0.1,0.1],objects:[{id:'subject',kind:'cube',position:[0,0,0],rotation_degrees:[0,0,0],scale:[1,1,1],color:[0.1,0.3,0.8]}],camera:{position:[5,-7,5],target:[0,0,0],lens_mm:50},lights:[{id:'key',position:[3,-4,6],target:[0,0,0],energy_w:800,size_m:3,color:[1,1,1]}]});
 let scope='',editing=null,baseline=null,source=null,base=0,dirty=false,editVersion=0,inFlight=false,assetReading=false,objectIndex=0,lightIndex=0,renderedFields='',importScope='';
 const scopeKey=()=>JSON.stringify([state?.workspace_id||'',song(),project()?.active_conversation?.id||'',project()?.shots[shotName]?.stable_id||shotName]);
 const storageKey=()=>scope?'loretune-scene-draft:'+scope:'';
 const status=value=>{el('sceneStudioStatus').textContent=value};
 function storageWarning(){el('sceneStudioStorageWarning').hidden=false}
 function persist(){if(!scope||!editing)return;const value={editing,baseline,source,base,dirty,editVersion,objectIndex,lightIndex};drafts.set(scope,structuredClone(value));try{sessionStorage.setItem(storageKey(),JSON.stringify(value))}catch{storageWarning()}}
 function remembered(){if(drafts.has(scope))return structuredClone(drafts.get(scope));try{const raw=sessionStorage.getItem(storageKey());return raw?JSON.parse(raw):null}catch{storageWarning();return null}}
 function record(){const p=project(),s=p?.shots[shotName];return (p?.scenes_3d||[]).find(x=>x.shot===shotName||!!s?.stable_id&&x.shot_id===s.stable_id)}
 function pending(record){return (record?.proposals||[]).filter(x=>['proposed','held'].includes(x.status)&&x.base_revision===record.head).at(-1)||null}
 function replaceable(record){return !record?.head?(record?.proposals||[]).filter(x=>['proposed','held','rejected'].includes(x.status)&&x.base_revision===0).at(-1)||null:pending(record)}
 function savedScene(record){const proposal=replaceable(record);return proposal?{scene:proposal.scene,source:proposal.id,base:proposal.base_revision}:record?.head?{scene:record.versions.find(v=>v.id===record.head)?.scene,source:null,base:record.head}:null}
 function hydrate(record){const saved=savedScene(record);editing=structuredClone(saved?.scene||initial());baseline=structuredClone(saved?.scene||null);source=saved?.source||null;base=saved?.base||0;dirty=!saved;objectIndex=lightIndex=0;editVersion++;renderedFields='';}
 function input(path,label,value,min,max,step='any'){return `<label>${label}<input type="number" data-scene-path="${path}" min="${min}" max="${max}" step="${step}" required value="${esc(value??'')}"></label>`}
 function vector(path,label,values,min,max){return `<fieldset><legend>${label}</legend><div class="scene-studio-grid">${['X','Y','Z'].map((axis,i)=>input(path+'.'+i,axis,values[i],min,max)).join('')}</div></fieldset>`}
 function color(value){return '#'+value.map(n=>Math.round(Math.max(0,Math.min(1,Number(n)))*255).toString(16).padStart(2,'0')).join('')}
 function assets(){return (project()?.scene_3d_assets||[]).filter(x=>typeof x.id==='string'&&/^[a-f0-9]{64}$/.test(x.sha256||'')&&['gltf2-static-pbr-v1','gltf2-static-pbr-color-v2'].includes(x.profile))}
 function assetName(obj){return assets().find(x=>x.id===obj?.asset?.id)?.filename||'가져온 3D 자산'}
 function refreshAssets(){
  if(importScope!==scope){importScope=scope;el('sceneStudioAssetFile').value='';el('sceneStudioAssetRights').value=imports.get(scope)?.rights||'';el('sceneStudioAssetSelect').dataset.rendered=''}
  const selected=el('sceneStudioAssetSelect').value,options=assets().map(x=>`<option value="${esc(x.id)}" ${state?.asset_rights?.[x.sha256]?.blocked?'disabled':''}>${esc(x.filename)}${state?.asset_rights?.[x.sha256]?.blocked?' · 사용 중지':''}</option>`).join('')||'<option value="">가져온 자산 없음</option>';
  if(el('sceneStudioAssetSelect').dataset.rendered!==options){el('sceneStudioAssetSelect').innerHTML=options;el('sceneStudioAssetSelect').dataset.rendered=options;if(assets().some(x=>x.id===selected))el('sceneStudioAssetSelect').value=selected}
  el('sceneStudioAssetFileName').textContent=imports.get(scope)?.file?'선택한 파일: '+imports.get(scope).file.name:'파일을 선택하세요. 선택한 파일은 이 페이지에서만 보관됩니다.';
 }
 function useAsset(asset){
  const obj=editing?.objects?.[objectIndex];if(!obj||!asset||state?.asset_rights?.[asset.sha256]?.blocked)return false;
  editing.objects[objectIndex]={id:obj.id,kind:'mesh',asset:{id:asset.id,sha256:asset.sha256,profile:asset.profile},position:structuredClone(obj.position),rotation_degrees:structuredClone(obj.rotation_degrees),scale:structuredClone(obj.scale)};editing.schema_version=2;dirty=true;editVersion++;persist();fields();controls();status('현재 대상에 자산을 사용하는 초안입니다. 구도·빛을 확인하고 변경안을 저장하세요.');return true;
 }
 function fields(){if(!editing)return;const obj=editing.objects[objectIndex],light=editing.lights[lightIndex],r=record();
  if(!obj||!light){status('현재 구성의 대상을 확인할 수 없습니다. 저장된 구성을 다시 불러오세요.');return}
  const opts=(items,index)=>items.map((x,i)=>`<option value="${i}" ${i===index?'selected':''}>${i+1}</option>`).join('');
  const shapeControl=obj.kind==='mesh'?`<p>현재 자산: ${esc(assetName(obj))}. 파일의 재질을 유지합니다.</p>`:`<label>도형 종류<select data-scene-path="objects.${objectIndex}.kind" ${r?.head?'disabled':''}><option value="cube" ${obj.kind==='cube'?'selected':''}>상자</option><option value="sphere" ${obj.kind==='sphere'?'selected':''}>구</option><option value="plane" ${obj.kind==='plane'?'selected':''}>평면</option></select></label>${r?.head?'<p>저장된 구도의 도형 종류는 현재 변경할 수 없습니다.</p>':''}`;
  el('sceneStudioFields').innerHTML=`<details class="scene-studio-section"><summary>대상</summary><label>편집할 대상<select id="sceneStudioObject">${opts(editing.objects,objectIndex)}</select></label>${shapeControl}${vector('objects.'+objectIndex+'.position','위치',obj.position,-100,100)}${vector('objects.'+objectIndex+'.rotation_degrees','회전 · 도',obj.rotation_degrees,-360,360)}${vector('objects.'+objectIndex+'.scale','크기 배율',obj.scale,.05,10)}${obj.kind==='mesh'?'':`<label>도형 색상<input type="color" data-scene-path="objects.${objectIndex}.color" value="${color(obj.color)}"></label>`}</details>
  <details class="scene-studio-section"><summary>카메라</summary>${vector('camera.position','카메라 위치',editing.camera.position,-100,100)}${vector('camera.target','바라보는 위치',editing.camera.target,-100,100)}${input('camera.lens_mm','렌즈 · mm',editing.camera.lens_mm,18,120)}</details>
  <details class="scene-studio-section"><summary>조명</summary><label>편집할 조명<select id="sceneStudioLight">${opts(editing.lights,lightIndex)}</select></label>${vector('lights.'+lightIndex+'.position','조명 위치',light.position,-100,100)}${vector('lights.'+lightIndex+'.target','비추는 위치',light.target,-100,100)}<div class="scene-studio-grid">${input('lights.'+lightIndex+'.energy_w','밝기 · W',light.energy_w,0,5000)}${input('lights.'+lightIndex+'.size_m','크기 · m',light.size_m,.1,20)}</div><label>조명 색상<input type="color" data-scene-path="lights.${lightIndex}.color" value="${color(light.color)}"></label></details>`;
  el('sceneStudioObject').onchange=e=>{objectIndex=Number(e.target.value);persist();fields();const select=el('sceneStudioObject');select.closest('details').open=true;select.focus()};el('sceneStudioLight').onchange=e=>{lightIndex=Number(e.target.value);persist();fields();const select=el('sceneStudioLight');select.closest('details').open=true;select.focus()};renderedFields=scope+':'+editVersion;
 }
 function stale(r){if(!r)return !!source||base!==0;if(base!==r.head)return true;const current=replaceable(r);if((current?.id||null)!==source)return true;if(source&&!r.proposals.some(x=>x.id===source&&(['proposed','held'].includes(x.status)||!r.head&&x.status==='rejected')&&x.base_revision===r.head))return true;return false}
 function controls(){const r=record(),pendingRequest=typeof pendingId==='function'&&pendingId(),blocked=inFlight||assetReading||busy||!!pendingRequest||(typeof pendingId==='function'&&pendingId.failed),same=scope===scopeKey()&&!!project()?.shots[shotName],p=pending(r),v=r?.versions?.find(x=>x.id===r.head),isStale=stale(r),available=project()?.scene_3d_connection?.available===true,rejected=replaceable(r)?.status==='rejected';
  for(const id of ['sceneStudioAssetFile','sceneStudioAssetRights','sceneStudioAssetSelect'])el(id).disabled=blocked||!same;
  el('sceneStudioAssetImport').disabled=blocked||!same||isStale||!imports.get(scope)?.file||!el('sceneStudioAssetRights').value.trim();
  const selectedAsset=assets().find(x=>x.id===el('sceneStudioAssetSelect').value);el('sceneStudioAssetUse').disabled=blocked||!same||isStale||!selectedAsset||!!state?.asset_rights?.[selectedAsset.sha256]?.blocked;
  el('sceneStudioInputs').disabled=blocked||!same||!editing;el('sceneStudioRecover').hidden=!pendingRequest||(typeof mutationRequestActive==='function'&&mutationRequestActive(pendingRequest)&&!pendingId.failed);el('sceneStudioRecover').disabled=busy||inFlight;
  const retryAvailable=globalThis.LoretuneSceneRecovery?.canRetry?.()===true;el('sceneStudioRetry').hidden=!retryAvailable;el('sceneStudioRetry').disabled=!retryAvailable||inFlight||assetReading||busy;
  el('sceneStudioSave').disabled=blocked||!same||!editing||(!dirty&&!rejected&&!(!r?.head&&p?.requires_review))||isStale;el('sceneStudioDiscard').disabled=blocked||!same||!dirty;
  const unavailableAsset=editing?.objects?.some(obj=>obj.kind==='mesh'&&!assets().some(x=>x.id===obj.asset?.id&&x.sha256===obj.asset?.sha256&&x.profile===obj.asset?.profile&&!state?.asset_rights?.[x.sha256]?.blocked));
  const currentJob=(project()?.scene_3d_jobs||[]).filter(j=>j.scene_id===r?.id).at(-1),shot=project()?.shots[shotName];
  const candidate=!v?.requires_review&&!blocked&&!dirty&&!isStale&&!p&&!unavailableAsset&&r?.head&&currentJob?.scene_revision===r.head&&currentJob.status==='completed'&&(shot?.takes||[]).some(t=>t.id===currentJob.take);
  el('sceneStudioCapability').textContent=v?.requires_review?'실행 기준이 변경됐습니다. 저장된 버전을 새 변경안으로 복원하고 다시 승인하세요.':candidate?(shot.selected===currentJob.take?'현재 구도의 이미지 후보가 준비됐습니다. 편집·출력에서 이어서 작업하세요.':'현재 구도의 이미지 후보가 준비됐습니다. 창을 닫고 Take를 선택해 검토하세요.'):available?'정지 이미지 후보를 만들 수 있습니다.':'구성은 저장할 수 있습니다. 현재 환경에서는 이미지 생성이 준비되지 않았습니다.';
  if(candidate&&el('sceneStudioStatus').textContent===RENDER_REQUESTED)status('');
  el('sceneStudioApprove').disabled=blocked||!same||dirty||isStale||!p||p.requires_review===true||source!==p.id||!!unavailableAsset;
  el('sceneStudioRender').disabled=blocked||!same||dirty||isStale||!!p||!v?.approval?.id||v.requires_review===true||!available||!!unavailableAsset;
  el('sceneStudioRestore').disabled=blocked||!same||dirty||!r?.head;el('sceneStudioVersions').disabled=blocked||!r?.head;
  if(isStale)el('sceneStudioSummary').textContent='저장된 구도나 변경안이 바뀌었습니다. 입력을 보존하고 있습니다. 현재 입력을 취소한 뒤 최신 구도를 확인하세요.';
  else if(unavailableAsset)el('sceneStudioSummary').textContent='현재 구성의 3D 자산을 사용할 수 없습니다. 원본과 사용권 상태를 확인하거나 다른 자산으로 바꾸세요.';
  else if(dirty)el('sceneStudioSummary').textContent='아직 저장하지 않은 구성이 있습니다.';
  else if(p?.requires_review)el('sceneStudioSummary').textContent=r?.head?'실행 기준이 변경된 변경안입니다. 저장된 버전을 복원해 새 변경안으로 다시 검토하세요.':'실행 기준이 변경된 초안입니다. 변경안을 다시 저장한 뒤 승인하세요.';
  else if(v?.requires_review&&!p)el('sceneStudioSummary').textContent='이전 승인과 결과는 보존됩니다. 저장된 버전을 복원해 새 변경안을 승인하세요.';
  else if(p){const kinds={cube:'상자',sphere:'구',plane:'평면'};const shapes=p.scene.objects.map(x=>x.kind==='mesh'?assetName(x):kinds[x.kind]||'도형').join(', ');const o=p.origin,by=o?.actor==='agent'?` 모델 제안 · ${o.model_reason_label||'모델이 제시한 이유(검증 안 됨)'}: ${o.model_reason||''} · 대화 모델 ${o.provenance?.chat_model||'확인 필요'} · 권한 ${agentModeNames[o.provenance?.permission_mode]||'확인 필요'} · 추론 강도 ${agentEffortNames[o.provenance?.effort]||'확인 필요'}.`:'';el('sceneStudioSummary').textContent=`저장된 변경안: ${shapes} · 렌즈 ${p.scene.camera.lens_mm}mm · 조명 ${p.scene.lights.map(x=>x.energy_w+'W').join(', ')}.${by} 각 항목을 펼쳐 확인한 뒤 승인하세요.`}
  else if(rejected)el('sceneStudioSummary').textContent='거절된 구성입니다. 내용을 다시 확인하고 새 변경안으로 저장할 수 있습니다.';
  else if(v)el('sceneStudioSummary').textContent='승인된 구도입니다. 정지 후보 생성과 Take 검토는 별도입니다.';
  else el('sceneStudioSummary').textContent='구성을 입력하고 변경안을 저장하세요.';
 }
 function jobMarkup(job){const previous=record()?.versions?.find(v=>v.id===job.scene_revision)?.requires_review===true;const stateLabel=previous&&job.status==='completed'?'이전 실행 기준의 후보':({queued:'대기',running:'이미지 생성 중',completed:'후보 준비됨',failed:'생성 실패',cancelled:'취소됨',interrupted:'중단됨',outcome_unknown:'확인 필요'})[job.status]||'상태 확인 필요';const detail=previous?'이전 실행 기준의 작업입니다. 결과는 보존되며, 새 후보 생성에는 변경안 복원과 재승인이 필요합니다.':({queued:'창을 닫아도 작업은 계속됩니다.',running:'창을 닫아도 작업은 계속됩니다.',completed:'Take가 추가됐습니다. 기존 Take에서 선택하고 사용권과 내용을 검토하세요.',failed:'후보를 만들지 못했습니다. 작업 상태와 실행 환경을 확인하세요.',cancelled:'작업이 취소됐습니다. 이 작업의 후보는 추가되지 않았습니다.',interrupted:'작업이 중단됐습니다. 작업 상태를 확인하세요.',outcome_unknown:'기존 작업을 확인해야 합니다. 자동으로 다시 실행하지 않습니다.'})[job.status]||'작업 상태를 확인하세요.';const url=typeof job.download==='string'&&/^\/assets\/scene-[a-f0-9]{64}\.png$/.test(job.download)?job.download:'';return `<article class="guided-card"><b>정지 이미지 · ${esc(stateLabel)}</b><p>${esc(detail)}</p>${job.error?`<p class="error">${esc(job.error)}</p>`:''}${url?`<img src="${esc(url)}" alt="생성된 3D 구도 정지 이미지" class="scene-studio-result">`:''}${['queued','running'].includes(job.status)?`<button type="button" data-scene-cancel="${esc(job.id)}">후보 생성 취소</button>`:''}</article>`}
 function refresh(){button.disabled=!project()?.shots[shotName];if(!dialog.open)return;const next=scopeKey();if(scope!==next){persist();scope=next;const old=remembered();if(old?.editing){({editing,baseline,source,base,dirty,editVersion,objectIndex,lightIndex}=old);renderedFields=''}else hydrate(record());status('')}
  const p=project(),r=record(),selected=replaceable(r);if(!dirty&&r&&((selected?.id||null)!==source||r.head!==base)){hydrate(r)}
  el('sceneStudioContext').textContent=shotName?'현재 장면: '+shotName:'장면을 선택하세요.';
  const versions=r?.versions||[];el('sceneStudioRestoreRow').hidden=!versions.length;const versionsHTML=versions.map(v=>`<option value="${esc(v.id)}">구도 ${esc(v.id)}버전</option>`).join('')||'<option value="">저장된 구도 없음</option>';if(el('sceneStudioVersions').dataset.rendered!==versionsHTML){el('sceneStudioVersions').innerHTML=versionsHTML;el('sceneStudioVersions').dataset.rendered=versionsHTML}
  const jobs=(p?.scene_3d_jobs||[]).filter(j=>j.scene_id===r?.id).map(jobMarkup).join('');if(el('sceneStudioJobs').dataset.rendered!==jobs){el('sceneStudioJobs').innerHTML=jobs;el('sceneStudioJobs').dataset.rendered=jobs}
  refreshAssets();if(renderedFields===''&&editing)fields();controls();persist();
 }
 function valid(){
  const invalid=[...el('sceneStudioInputs').querySelectorAll('input,select')].find(x=>x.willValidate&&!x.checkValidity());
  if(invalid){const section=invalid.closest('details');if(section)section.open=true;status('입력 범위를 확인하세요.');invalid.setAttribute?.('aria-invalid','true');invalid.setAttribute?.('aria-describedby','sceneStudioStatus');invalid.focus();invalid.reportValidity();return false}
  const showError=(path,message)=>{const input=el('sceneStudioFields').querySelector(`[data-scene-path="${path}"]`);const section=input?.closest('details');if(section)section.open=true;status(message);input?.setAttribute?.('aria-invalid','true');input?.setAttribute?.('aria-describedby','sceneStudioStatus');input?.focus();return false};
  const number=(n,min,max)=>typeof n==='number'&&Number.isFinite(n)&&n>=min&&n<=max;
  const vectorError=(path,value,min,max)=>{if(!Array.isArray(value)||value.length!==3)return path+'.0';const i=value.findIndex(n=>!number(n,min,max));return i<0?null:path+'.'+i};
  for(let i=0;i<editing.objects.length;i++){
   const obj=editing.objects[i];if(obj.kind==='mesh'&&!assets().some(x=>x.id===obj.asset?.id&&x.sha256===obj.asset?.sha256&&x.profile===obj.asset?.profile&&!state?.asset_rights?.[x.sha256]?.blocked)){status('현재 대화에서 사용할 수 없는 자산입니다. 자산과 사용권 상태를 확인하세요.');el('sceneStudioAssetPanel').open=true;el('sceneStudioAssetSelect').focus();return false}
   for(const [field,min,max] of [['position',-100,100],['rotation_degrees',-360,360],['scale',.05,10],...(obj.kind==='mesh'?[]:[['color',0,1]])]){const path=vectorError('objects.'+i+'.'+field,obj[field],min,max);if(path){if(i!==objectIndex){objectIndex=i;fields()}return showError(field==='color'?'objects.'+i+'.color':path,'대상 입력 범위를 확인하세요.')}}
  }
  for(const field of ['position','target']){const path=vectorError('camera.'+field,editing.camera[field],-100,100);if(path)return showError(path,'카메라 입력 범위를 확인하세요.')}
  if(!number(editing.camera.lens_mm,18,120))return showError('camera.lens_mm','렌즈 입력 범위를 확인하세요.');
  for(let i=0;i<editing.lights.length;i++){
   for(const [field,min,max] of [['position',-100,100],['target',-100,100],['color',0,1]]){const path=vectorError('lights.'+i+'.'+field,editing.lights[i][field],min,max);if(path){if(i!==lightIndex){lightIndex=i;fields()}return showError(field==='color'?'lights.'+i+'.color':path,'조명 입력 범위를 확인하세요.')}}
   for(const [field,min,max] of [['energy_w',0,5000],['size_m',.1,20]])if(!number(editing.lights[i][field],min,max)){if(i!==lightIndex){lightIndex=i;fields()}return showError('lights.'+i+'.'+field,'조명 입력 범위를 확인하세요.')}
  }
  const distance=(a,b)=>a.reduce((n,x,i)=>n+(x-b[i])**2,0);
  if(distance(editing.camera.position,editing.camera.target)<.01)return showError('camera.position.0','카메라 위치와 바라보는 위치를 다르게 입력하세요.');
  for(let i=0;i<editing.lights.length;i++)if(distance(editing.lights[i].position,editing.lights[i].target)<.01){if(i!==lightIndex){lightIndex=i;fields()}return showError('lights.'+i+'.position.0','조명 위치와 비추는 위치를 다르게 입력하세요.')}
  return true;
 }
 function operations(before,after){const changes=[];const add=(target,id,field,a,b)=>{if(JSON.stringify(a)!==JSON.stringify(b))changes.push({target,id,field,value:structuredClone(b)})};for(const field of ['position','target','lens_mm'])add('camera','camera',field,before.camera[field],after.camera[field]);for(const prior of before.objects){const next=after.objects.find(x=>x.id===prior.id);if(!next)throw Error('현재 대상을 다시 확인하세요.');if(next.kind==='mesh')add('object',prior.id,'asset',prior.asset,next.asset);for(const field of ['position','rotation_degrees','scale',...(next.kind==='mesh'?[]:['color'])])add('object',prior.id,field,prior[field],next[field])}for(const prior of before.lights){const next=after.lights.find(x=>x.id===prior.id);if(!next)throw Error('현재 조명을 다시 확인하세요.');for(const field of ['position','target','energy_w','size_m','color'])add('light',prior.id,field,prior[field],next[field])}return changes}
 async function request(action,data,onSuccess){const ctx=scope;let outcome={status:'not_sent'};inFlight=true;controls();try{const ok=await act(action,data,undefined,value=>{outcome=value});if(ok&&scope===ctx)onSuccess?.(outcome.result);if(!ok&&scope===ctx){const messages={rejected:'요청이 거부됐습니다. 입력은 유지됩니다. '+(typeof outcome.reason==='string'?outcome.reason.slice(0,500):'값을 확인해 주세요.'),unknown:'요청 결과가 미확정입니다. 입력을 유지하며 기존 요청을 먼저 확인하세요.',committed_refresh_failed:'저장은 완료됐지만 화면을 갱신하지 못했습니다. 새로고침해 결과를 확인하세요.',not_sent:'요청을 보내지 못했습니다. 진행 중인 작업과 입력을 확인하세요.'};status(messages[outcome.status]||'작업 상태를 확인하지 못했습니다. 입력은 유지됩니다.')}return ok}finally{inFlight=false;controls()}}
 el('sceneStudioAssetFile').onchange=()=>{if(inFlight||assetReading||busy)return;const file=el('sceneStudioAssetFile').files?.[0],old=imports.get(scope)||{};if(file&&(!/\.glb$/i.test(file.name)||file.size<1||file.size>MAX_ASSET_BYTES)){el('sceneStudioAssetFile').value='';imports.set(scope,{...old,file:null});status('8MB 이하의 GLB 파일을 선택하세요.');refreshAssets();controls();return}imports.set(scope,{...old,file:file||null});refreshAssets();controls()};
 el('sceneStudioAssetRights').oninput=()=>{imports.set(scope,{...(imports.get(scope)||{}),rights:el('sceneStudioAssetRights').value});controls()};
 el('sceneStudioAssetSelect').onchange=controls;
 el('sceneStudioAssetUse').onclick=()=>{if(inFlight||assetReading||busy||stale(record())||scope!==scopeKey())return;useAsset(assets().find(x=>x.id===el('sceneStudioAssetSelect').value))};
 el('sceneStudioAssetImport').onclick=async()=>{
  if(inFlight||assetReading||busy||scope!==scopeKey()||stale(record()))return;const ctx=scope,entry=imports.get(scope),file=entry?.file,rights=el('sceneStudioAssetRights').value.trim();if(!file||!rights)return;const selectedId=editing?.objects?.[objectIndex]?.id;assetReading=true;controls();
  try{const content=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>{const result=reader.result;if(typeof result==='string'&&result.includes(','))resolve(result.slice(result.indexOf(',')+1));else reject(Error('invalid file read'))};reader.onerror=()=>reject(Error('file read failed'));reader.readAsDataURL(file)});if(scope!==ctx||scope!==scopeKey())return;let imported=null;
   if(await request('scene_asset_import',{song:song(),filename:file.name,content,rights},result=>{imported=result?.scene_asset})){if(scope!==ctx)return;const asset=assets().find(x=>x.id===imported?.id&&x.sha256===imported?.sha256);if(!asset){status('가져온 자산을 확인하지 못했습니다. 입력을 유지하며 화면을 갱신해 결과를 확인하세요.');return}if(imports.get(ctx)?.file===file){imports.set(ctx,{rights,file:null});el('sceneStudioAssetFile').value=''}refreshAssets();el('sceneStudioAssetSelect').value=asset.id;if(editing?.objects?.[objectIndex]?.id===selectedId)useAsset(asset);else status('자산을 가져왔습니다. 사용할 대상을 확인한 뒤 자산을 선택하세요.')}
  }catch{if(scope===ctx)status('파일 처리를 마치지 못했습니다. 입력은 유지됩니다. 작업 상태와 기존 요청을 확인하세요.')}finally{assetReading=false;controls()}
 };
 button.onclick=()=>{dialog.showModal();refresh()};el('sceneStudioClose').onclick=()=>dialog.close();dialog.addEventListener('close',()=>{persist();button.focus()});
 el('sceneStudioFields').addEventListener('invalid',e=>{const section=e.target.closest('details');if(section)section.open=true;e.target.setAttribute?.('aria-invalid','true');e.target.setAttribute?.('aria-describedby','sceneStudioStatus');status('입력 범위를 확인하세요.')},true);
 el('sceneStudioFields').oninput=e=>{const input=e.target,path=input.dataset.scenePath;if(input.getAttribute?.('aria-invalid')==='true'){input.removeAttribute?.('aria-invalid');input.removeAttribute?.('aria-describedby')}if(!editing||!path||inFlight||busy)return;const keys=path.split('.'),last=keys.pop();let target=editing;for(const key of keys)target=target[key];target[last]=input.type==='number'?(input.value===''?null:Number(input.value)):input.type==='color'?input.value.slice(1).match(/../g).map(x=>parseInt(x,16)/255):input.value;dirty=true;editVersion++;persist();controls();status('수정 내용을 아직 저장하지 않았습니다.')};
 el('sceneStudioDiscard').onclick=()=>{if(inFlight||busy)return;hydrate(record());dirty=false;if(!record()){editing=initial();dirty=true}fields();persist();controls();status('저장된 구도를 다시 불러왔습니다.')};
 el('sceneStudioSave').onclick=async()=>{const r0=record();if(inFlight||busy||!editing||(!dirty&&replaceable(r0)?.status!=='rejected'&&!(!r0?.head&&replaceable(r0)?.requires_review))||scope!==scopeKey()||!valid())return;const ctx=scope,version=editVersion,p=project(),s=p?.shots[shotName],r=record(),scene=structuredClone(editing);if(!s||stale(r))return;let action,data;
  if(!r){action='scene_create';data={song:song(),shot_id:s.stable_id||shotName,scene}}
  else if(!r.head){if(!source)return status('현재 변경안을 다시 확인하세요.');action='scene_replace_draft';data={song:song(),scene_id:r.id,scene_proposal_id:source,base_revision:0,scene}}
  else {const prior=r.versions.find(v=>v.id===r.head)?.scene,ops=prior?operations(prior,scene):[];if(!ops.length)return status('저장할 변경이 없습니다.');action='scene_propose';data={song:song(),scene_id:r.id,base_revision:r.head,operations:ops}}
  if(await request(action,data)){if(scope!==ctx||version!==editVersion)return;const saved=record();if(!saved||!pending(saved)){status('저장은 완료됐지만 변경안을 불러오지 못했습니다. 입력을 유지하고 새로고침해 확인하세요.');return}hydrate(saved);dirty=false;persist();fields();refresh();status('변경안을 저장했습니다. 구성 승인 전입니다.')}
 };
 el('sceneStudioApprove').onclick=async()=>{const r=record(),p=pending(r),ctx=scope;if(inFlight||busy||!p||p.requires_review===true||dirty||stale(r)||p.id!==source)return;if(await request('scene_review',{song:song(),scene_proposal_id:p.id,decision:'approved'})){if(scope!==ctx)return;hydrate(record());dirty=false;fields();refresh();status('구도를 승인했습니다.')}};
 el('sceneStudioRender').onclick=async()=>{const r=record(),v=r?.versions?.find(x=>x.id===r.head),ctx=scope;if(inFlight||busy||!v||v.requires_review===true||dirty||pending(r)||stale(r)||project()?.scene_3d_connection?.available!==true)return;if(await request('scene_render',{song:song(),scene_id:r.id,scene_revision:r.head,grant_id:v.approval.id})){if(ctx!==scope)return;refresh();status(RENDER_REQUESTED)}};
 el('sceneStudioRestore').onclick=async()=>{const r=record(),ctx=scope,revision=editVersion;if(inFlight||busy||!r?.head||dirty)return;const value=Number(el('sceneStudioVersions').value);if(await request('scene_restore',{song:song(),scene_id:r.id,base_revision:r.head,version:value})){if(scope!==ctx||editVersion!==revision)return;hydrate(record());dirty=false;fields();refresh();status('이전 구도를 새 변경안으로 복원했습니다. 다시 검토해 주세요.')}};
 el('sceneStudioJobs').onclick=async e=>{
  const b=e.target.closest('[data-scene-cancel]');
  if(!b||!dialog.open||inFlight||busy||scope!==scopeKey())return;
  const p=project(),r=record(),job=(p?.scene_3d_jobs||[]).find(j=>j.id===b.dataset.sceneCancel&&j.scene_id===r?.id);
  if(!job||!['queued','running'].includes(job.status)){status('현재 장면의 진행 중인 작업을 다시 확인하세요.');return}
  const ctx=scope,name=song();
  if(await request('cancel_job',{song:name,job:job.id})){if(scope!==ctx)return;refresh();status('후보 생성 취소를 요청했습니다. 작업 상태를 확인하세요.')}
 };
 el('sceneStudioRecover').onclick=async()=>{const ctx=scope,version=editVersion,receipt=await reconcilePendingRequest();await refresh();if(scope!==ctx)return;const r=record(),saved=savedScene(r),confirmed=receipt?.result?.scene;
  if(!pendingId()&&dirty&&editVersion===version&&confirmed?.status==='proposed'&&pending(r)?.status==='proposed'&&confirmed.scene_id===r?.id&&confirmed.proposal_id===saved?.source&&JSON.stringify(saved.scene)===JSON.stringify(editing)){hydrate(r);dirty=false;persist();fields();controls();status('기존 변경안 저장을 확인했습니다. 입력은 그대로이며 구성 승인은 별도입니다.');return}
  status(pendingId()?(globalThis.LoretuneSceneRecovery?.canRetry?.()?'원래 3D 요청이 아직 기록되지 않았습니다. 같은 요청을 다시 보내거나 상태를 다시 확인할 수 있습니다.':'요청 결과가 아직 미확정입니다. 새 제출을 차단합니다.'):'기존 요청을 확인했습니다. 입력과 저장된 변경안을 비교하세요.')};
 el('sceneStudioRetry').onclick=async()=>{
  const recovery=globalThis.LoretuneSceneRecovery;if(inFlight||assetReading||busy||scope!==scopeKey()||recovery?.canRetry?.()!==true)return;const ctx=scope,selectedId=editing?.objects?.[objectIndex]?.id;let outcome=null;inFlight=true;controls();
  try{const ok=await recovery.retry(value=>{if(value.status==='committed'||!outcome)outcome=value});if(scope!==ctx)return;refresh();if(ok&&outcome?.status==='committed'){
    if(outcome.request?.action==='scene_asset_import'){const imported=outcome.result?.scene_asset,asset=assets().find(x=>x.id===imported?.id&&x.sha256===imported?.sha256);if(asset&&editing?.objects?.[objectIndex]?.id===selectedId){imports.set(ctx,{rights:imports.get(ctx)?.rights||'',file:null});el('sceneStudioAssetFile').value='';refreshAssets();el('sceneStudioAssetSelect').value=asset.id;useAsset(asset)}else status('기존 자산 요청을 확인했습니다. 사용할 자산과 대상을 확인하세요.')}
    else status('기존 3D 요청을 확인했습니다. 입력과 저장된 구성을 비교하세요.');
   }else status(pendingId()?'요청 결과를 아직 확인하지 못했습니다. 입력을 유지하며 기존 요청을 확인하세요.':'기존 요청의 결과와 입력을 확인하세요.');
  }catch{if(scope===ctx)status('기존 요청 복구를 마치지 못했습니다. 입력을 유지하며 요청 상태를 확인하세요.')}finally{inFlight=false;controls()}
 };
 // S8: chat navigation to a saved proposal. Unsaved 3D input is kept ('kept'), never replaced.
 function reveal(id){const r=record(),item=(r?.proposals||[]).find(x=>x.id===id);if(!dialog.open||!item)return 'missing';
  if(dirty&&source!==id){status('저장하지 않은 3D 입력을 유지했습니다. 대화에서 연 변경안을 보려면 입력을 저장하거나 취소하세요.');return 'kept'}
  status(replaceable(r)?.id===id?'대화에서 연 변경안입니다. 항목을 펼쳐 확인한 뒤 승인하세요.':'대화에서 연 변경안은 현재 검토 대상이 아닙니다(상태: '+({proposed:'검토 전',held:'보류',rejected:'거절',approved:'승인됨',applied:'적용됨'}[item.status]||'확인 필요')+'). 현재 구도를 표시합니다.');return 'opened'}
 window.AethonScene={refresh,reveal};refresh();
})();
