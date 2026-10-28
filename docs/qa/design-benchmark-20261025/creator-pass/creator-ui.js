/* Presentation helpers: no network calls or authorization changes. */
function creatorError(raw){
 const t=String(raw||'');
 if(/저장은 완료|저장 완료.*갱신/.test(t))return {message:'저장은 완료됐습니다. 화면을 새로고침해 결과를 확인하세요.',detail:t};
 if(/미확정|outcome_unknown|reconciliation|응답.*확인/.test(t))return {message:'처리 결과를 아직 확인하지 못했습니다. 기존 요청 상태를 확인하세요. 새로 실행하지 마세요.',detail:t};
 if(/403|권한|permission|forbidden|접근.*차단/i.test(t))return {message:'결과에 접근할 수 없습니다. 연결 권한을 확인한 뒤 기존 요청을 확인하세요. 새로 생성하지 마세요.',detail:t};
 if(/각 타임라인 take|모든.*take.*승인/i.test(t))return {message:'편집에 사용한 Take를 모두 승인한 뒤 출력 승인을 진행하세요.',detail:t};
 if(/사용권|rights/i.test(t))return {message:'사용권 확인이 필요합니다. 사용권 관리에서 근거와 사용 상태를 확인하세요.',detail:t};
 if(/만료|expired/i.test(t))return {message:'확인 가능한 시간이 지났습니다. 입력과 예상 비용을 다시 확인한 뒤 승인하세요.',detail:t};
 if(/저장되지 않은|먼저.*저장|편집을.*저장/.test(t))return {message:'변경한 편집을 먼저 저장하세요.',detail:t};
 if(/예산|budget|비용.*초과/i.test(t))return {message:'설정한 예산으로 진행할 수 없습니다. 예상 비용과 남은 예산을 확인하세요.',detail:t};
 if(/선택하세요|입력하세요|최대 16MB|작품을 먼저|Take를 먼저|결정을 선택/.test(t))return {message:t,detail:''};
 if(/연결|fetch|network|timeout/i.test(t))return {message:'연결을 확인하지 못했습니다. 저장 상태를 확인한 뒤 다시 진행하세요.',detail:t};
 return {message:'작업을 완료하지 못했습니다. 입력과 작업 상태를 확인하세요. 자세한 원인은 오류 상세에서 볼 수 있습니다.',detail:t};
}
function creatorDiagnostic(label,value){return `<details class="creator-diagnostic"><summary>${esc(label)}</summary><pre>${esc(typeof value==='string'?value:JSON.stringify(value,null,2))}</pre></details>`}
function creatorTestMedia(t){return !!t&&/AI\s*생성\s*아님|로컬\s*합성|테스트 미디어|모의\s*(후보|합성)/i.test(t.reason||'')}
function creatorMediaMarkup(t,{includeMemo=true}={}){
 if(!t)return '';
 const blocked=state?.asset_rights?.[t.sha256],test=creatorTestMedia(t),meta=t.metadata||{};
 const facts=[meta.width&&meta.height?`${meta.width}×${meta.height}`:'',meta.duration>0?`${Number(meta.duration.toFixed(3))}초`:''].filter(Boolean).join(' · ');
 return `${test?'<span class="creator-test-badge">테스트 미디어</span>':''}${facts?`<small class="creator-media-facts">${esc(facts)}</small>`:''}${blocked?.blocked?`<p class="error">사용 중지 · ${esc(blocked.reason)}</p>`:!t.rights?'<p class="error">사용권 근거를 확인하세요.</p>':''}${!test&&includeMemo&&t.reason?`<p>${esc(t.reason)}</p>`:''}<details class="creator-source"><summary>출처·사용권</summary><p>${esc(t.filename||'연결된 파일')}</p><p>${esc(t.rights||'사용권 미확인')}</p>${test?`<p>${esc(t.reason)}</p>`:''}${creatorDiagnostic('파일 식별 정보',t.sha256||'기록 없음')}</details>`;
}
function creatorOutputTest(j){return Object.values(j.snapshot?.shots||{}).some(s=>creatorTestMedia(s.takes?.find(t=>t.id===s.selected)))}
function creatorSceneLabel(name,i){return /^\d{1,2}(?:\s|[.·-]\s)/.test(name)?name:`${String(i+1).padStart(2,'0')} ${name}`}
function creatorSceneFacts(p,name,s){const timeline=draft||(p.timeline_head?p.timeline_versions[p.timeline_head-1]:null),clip=timeline?.clips.find(c=>c.shot===name&&c.take===s.selected);return s.selected?`${clip?Number(clip.duration.toFixed(3))+'초 편집 · ':''}Take ${s.selected}`:'Take를 연결하세요'}
function creatorReviewMode({hasReview,hasDraft,editing,pending}){return pending?'saving':hasDraft?'dirty':!hasReview||editing?'editing':'read'}
const creatorEditing=new Set(),creatorPendingSeen=new Set();
function ensureCreatorReview(){
 const button=$('#reviewTake');if(!button||$('#creatorReviewRecord'))return;
 const section=button.closest('section'),record=document.createElement('div');record.id='creatorReviewRecord';record.innerHTML='<p class="creator-record-label">검토 메모</p><p id="creatorSavedReason"></p><button type="button" id="creatorEditReview" aria-controls="creatorReviewEditor" aria-expanded="false">검토 수정</button>';
 const editor=document.createElement('div');editor.id='creatorReviewEditor';editor.setAttribute('role','group');editor.setAttribute('aria-label','Take 검토 수정');const label=$('#reviewReason').closest('label'),row=$('#takeDecision').parentElement;label.before(record,editor);editor.append(label,row);
 $('#creatorEditReview').onclick=()=>{const c=currentTakeReview();if(!c||busy)return;creatorEditing.add(c.key);renderTakeReview();$('#reviewReason').focus()};
 $('#discardTakeReviewDraft').onclick=()=>{const c=currentTakeReview();if(!c||busy||takeReviewController.pending.has(c.key))return;takeReviewStore.clear(c.key);creatorEditing.delete(c.key);takeReviewScope='';renderTakeReview();(c.review?$('#creatorEditReview'):$('#reviewReason')).focus()};
}
function renderCreatorReview(c,local){
 ensureCreatorReview();if(!$('#creatorReviewRecord'))return;
 const pending=!!c&&takeReviewController.pending.has(c.key);
 if(pending)creatorPendingSeen.add(c.key);
 if(c&&!pending&&creatorPendingSeen.has(c.key)){if(!local)creatorEditing.delete(c.key);creatorPendingSeen.delete(c.key)}
 const mode=creatorReviewMode({hasReview:!!c?.review,hasDraft:!!local,editing:!!c&&creatorEditing.has(c.key),pending});
 const section=$('#reviewTake').closest('section'),s=project()?.shots[shotName],take=s?.takes.find(t=>t.id===c?.take);
 section.dataset.reviewMode=c?mode:'empty';section.querySelector('h2').textContent='장면 검토';
 $('#takeReviewStatus').innerHTML=`<strong class="creator-review-scene">${esc(shotName||'장면을 선택하세요')}</strong>${c?`<b>Take ${c.take}</b>${studioBadge(s,c.take)}<small>${esc(studioUseLabel(project(),c.shot,c.take)||'편집에 미사용')} · 출력 승인과 별도</small>`:'<p>기존 이미지나 영상을 연결해 검토를 시작하세요.</p>'}`;
 const record=$('#creatorReviewRecord'),editor=$('#creatorReviewEditor');record.hidden=!c||mode!=='read';editor.hidden=!c||mode==='read';editor.setAttribute('aria-busy',String(pending));
 $('#creatorSavedReason').textContent=c?.review?.reason||'검토 메모가 없습니다.';
 $('#creatorEditReview').disabled=!!busy;$('#creatorEditReview').setAttribute('aria-expanded',String(mode!=='read'));
 $('#reviewTake').textContent=pending?'저장 중…':c?.review?'검토 변경 저장':'검토 저장';
 $('#discardTakeReviewDraft').textContent='취소';$('#discardTakeReviewDraft').disabled=!!busy||pending;
 $('#takeReviewDraftState').textContent=pending?'검토를 저장하고 있습니다.':takeReviewStore.failed?'이 탭에만 초안을 보존 중입니다. 브라우저 저장소를 확인하세요.':local?'저장하지 않은 검토 변경':c?.review?'결정이나 메모를 수정한 뒤 저장하세요.':'결정과 검토 메모를 입력하세요.';
 $('#reason').innerHTML=creatorMediaMarkup(take,{includeMemo:false});
 let source=$('#creatorReviewSource');if(!source){source=document.createElement('div');source.id='creatorReviewSource';editor.after(source)}source.replaceChildren();const sourceDetail=$('#reason .creator-source');if(sourceDetail)source.append(sourceDetail);
 const uploadDetail=$('#upload').closest('details');if(uploadDetail){if(!c&&!uploadDetail.open){uploadDetail.dataset.creatorAutoOpen='true';uploadDetail.open=true}else if(c&&uploadDetail.dataset.creatorAutoOpen){uploadDetail.open=false;delete uploadDetail.dataset.creatorAutoOpen}}
 const mobile=$('#creatorMobileContext');if(mobile)mobile.innerHTML=`<b>${esc(shotName||'장면 선택')}</b><small>${c?'Take '+c.take+' · '+esc(studioReview(s,c.take).label.replace('Take ','')):'미디어 연결 전'}</small>`;
}
function creatorModelReason(role,model){
 const target=document.getElementById(`model-${role}-reason`);if(!target)return;
 target.textContent=!model?(role==='image'?'이미지 모델을 선택하지 않았습니다. 기존 이미지를 연결할 수 있습니다.':'모델을 선택하세요.'):model.state==='integration_blocked'?'결과 연결이 차단되어 사용할 수 없습니다. 연결 상태를 확인하세요.':'연결 확인이 필요합니다. 선택을 저장해도 바로 실행되지 않습니다.';
 let detail=document.getElementById(`model-${role}-diagnostic`);if(!detail){detail=document.createElement('div');detail.id=`model-${role}-diagnostic`;target.after(detail)}detail.innerHTML=creatorDiagnostic('연결 상세',model?.reason||'선택된 모델 없음');
}
function creatorExecutionVisibility(){const d=$('#executionCards')?.closest('details');if(d&&(project()?.execution_cards||[]).some(c=>!c.result_decision))d.open=true}
function initializeCreatorUI(){
 document.body.classList.add('lt-creator');ensureCreatorReview();
 const shell=$('.lt-studio-shell'),notice=$('.lt-notice-detail'),context=$('.lt-project-context');if(shell&&notice)shell.insertBefore(notice,$('.management'));
 if(context){context.querySelector('summary').textContent='제작 진행·도움말';context.append($('#flowNext'))}
 const heading=$('#flowHeading');heading.classList.add('creator-skip-target');$('.lt-stage-bar').append(heading);$('.lt-status-line')?.remove();
 const mobile=document.createElement('div');mobile.id='creatorMobileContext';$('.lt-panel-nav').before(mobile);
 const description=$('#description'),detail=document.createElement('details');detail.className='creator-scene-description';detail.innerHTML='<summary>장면 설명</summary>';description.before(detail);detail.append(description);
 const labels={ontologyButton:'캐릭터·장소·스타일',settings:'세계관 설정',budgetButton:'제작 예산',operationsButton:'진단·작업 기록',manifest:'제작 기록 내보내기',sync:'선택한 Take로 편집 구성',review:'출력 버전 승인',render:'영상 출력',prepareSelectedAction:'테스트 미디어 만들기',prepareGeneration:'영상 입력·예상 비용 확인',modelChatRefresh:'대화·작업 상태 새로고침',saveTimeline:'편집 저장',restore:'이 버전으로 복원'};
 for(const [id,text]of Object.entries(labels))if($('#'+id))$('#'+id).textContent=text;
 const exec=$('#executionCards').closest('details');if(exec){exec.querySelector('summary').textContent='테스트 미디어';exec.open=!!project()?.execution_cards?.some(c=>!c.result_decision)}
 for(const [id,text]of [['imageConnection','이미지 모델·기존 결과'],['generationGateText','영상 생성'],['referenceVersions','참고 이미지']]){const d=$('#'+id)?.closest('.lt-inspector-detail');if(d)d.querySelector('summary').textContent=text}
 const planIntro=$('#chatPanel>p');if(planIntro)planIntro.textContent='영상의 목표와 장면을 정리하세요. 계획을 검토한 뒤 제작을 진행합니다.';
 const capIntro=$('#modelChatPanel>p.muted');if(capIntro)capIntro.textContent='답변과 장면 계획을 확인하세요. 계획 검토와 미디어 실행 승인은 별개입니다.';
 $('#modelChatPrompt').placeholder='허용된 테스트 입력으로 영상 계획을 상담하세요.';
 const uploadLabel=$('#upload [name=asset]').closest('label');uploadLabel.firstChild.textContent='기존 이미지·영상 ';$('#upload button').textContent='새 Take 연결';$('.shot-board h2')?.firstChild && ($('.shot-board h2').firstChild.textContent='장면 ');
 const modelIntro=$('#modelSettingsPanel>p:not(.dialog-status)');if(modelIntro)modelIntro.textContent='대화·이미지·영상에 사용할 모델을 고르세요. 실행할 때 입력과 예상 비용을 다시 확인합니다.';
 $('#modelSettingsForm button').textContent='모델 선택 저장';
 const ontologyIntro=$('#ontologyDialog>p:not(.dialog-status)');if(ontologyIntro)ontologyIntro.textContent='여러 장면에서 일관되게 사용할 캐릭터·장소·스타일을 저장하세요. 검토 후 원하는 장면에 연결할 수 있습니다.';
 $('#ontologyDialog h2').textContent='캐릭터·장소·스타일';$('#ontologyNew').textContent='새 설정 작성';$('#ontologyEditStatus').textContent='새 설정';
 const lineage=$('#lineageContent').closest('details');lineage.querySelector('summary').textContent='설정·제작 연결 기록';
 const budget=$('#budgetLedger'),ledger=document.createElement('details');ledger.className='creator-diagnostic';ledger.innerHTML='<summary>비용 상세 기록</summary>';budget.previousElementSibling?.remove();budget.before(ledger);ledger.append(budget);
 const budgetIntro=$('#budgetDialog>p:not(.dialog-status)');if(budgetIntro)budgetIntro.textContent='모델 작업에 사용할 예산입니다. 예산 저장은 유료 실행 승인이 아닙니다.';$('#budgetTitle').textContent='제작 예산';$('#budgetForm button').textContent='예산 저장';
 const projectForm=$('#project'),story=document.createElement('details');story.className='creator-context-detail';story.innerHTML='<summary>세계관·이야기 설정</summary>';const ip=projectForm.querySelector('[name=ip]').closest('label');ip.before(story);for(const name of ['ip','era','story'])story.append(projectForm.querySelector(`[name="${name}"]`).closest('label'));
 const d=$('#renderConfirm>p:not(.dialog-status)');if(d)d.textContent='외부 모델 비용 $0 · 로컬 처리 비용은 별도입니다. 확인한 편집과 자막으로 출력합니다.';
 if(state)renderTakeReview();
}
