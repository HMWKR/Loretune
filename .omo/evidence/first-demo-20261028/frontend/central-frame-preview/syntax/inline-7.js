
const lateEvidenceContainer=document.createElement('div');
lateEvidenceContainer.hidden=true;
$('#budgetSummary').after(lateEvidenceContainer);
const lateEvidence=LoretuneLateEvidence.mount({container:lateEvidenceContainer,context:()=>({workspace:state.workspace_id,projectId:budgetProject===state.project_ids[song()]?budgetProject:null,token:state.token})});
$('#budgetButton').addEventListener('click',()=>{if($('#budgetDialog').open)lateEvidence.refresh()});
$('#reloadBudget').addEventListener('click',()=>lateEvidence.refresh());
