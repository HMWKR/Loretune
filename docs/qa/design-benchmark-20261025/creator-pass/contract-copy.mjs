/* Optional presentation adapter for the staged contract. No requests or mutations.
   Integration owner wires these copy objects to the real proposal/action views. */
export function timelineProposalCopy(receipt={}) {
  return receipt.applied === true
    ? {title:'편집 변경안',status:'새 편집 버전에 적용됨',note:receipt.output_approved===true?'출력 승인됨':'출력하려면 새 편집 버전을 승인하세요.'}
    : {title:'편집 변경안',status:'아직 적용하지 않음',note:'변경할 장면·Take·시작점·길이를 확인하세요. 승인하면 새 편집 버전으로 저장합니다.'};
}
export function memoryProposalCopy(receipt={}) {
  return {title:'캐릭터·장소·스타일 설정 변경 제안',status:receipt.canonical_approved===true?'설정 승인됨':'검토 대기 · 아직 반영하지 않음',note:'이 작품의 설정에 대한 제안입니다. 근거를 확인한 뒤 승인하세요. 다른 작품의 설정은 자동으로 바뀌지 않습니다.'};
}
export function renderReceiptCopy(receipt={}) {
  const states={queued:'출력 대기',running:'출력 중',failed:'출력 실패',cancelled:'출력 취소됨'};
  if(receipt.finished_verified===true)return {title:'영상 출력',status:receipt.output_approved===true?'납품 검토 승인됨':'출력 파일 준비됨 · 납품 검토 전',note:'완료된 파일을 확인하세요.'};
  return {title:'영상 출력',status:states[receipt.state]||'출력 상태 확인 필요',note:receipt.status==='existing'?'이미 접수한 작업입니다. 기존 작업 상태를 확인하세요.':'출력 요청 접수와 파일 완료는 별개입니다.'};
}
