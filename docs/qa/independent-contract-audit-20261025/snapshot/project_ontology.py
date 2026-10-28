"""Local Studio identity/provenance projection and reviewed semantic annotations.
Runtime projection is read-only: a model cannot rewrite takes or approvals.
"""
import hashlib, json, uuid
import ontology
from pathlib import Path


def scope(workspace, project_id):return workspace+':project:'+project_id


def projection(workspace, project_id, project):
    namespace=scope(workspace,project_id);nodes=[];edges=[]
    def node(kind,key,label,source,version=None):
        identifier=ontology.stable_id(namespace,kind,str(key))
        nodes.append(dict(id=identifier,type=kind,label=label,source=source,version=version))
        return identifier
    def edge(a,b,role):edges.append(dict(source=a,target=b,role=role))
    root=node('project',project_id,project['name'],'local-project')
    for a in project.get('audio_versions',[]):
        asset=node('asset','audio:'+str(a['id']),a['filename'],'imported',a['id']);edge(root,asset,'audio_version')
    for name,shot in project['shots'].items():
        sid=node('shot',shot.get('stable_id','legacy:'+name),name,'authored',shot['revision']);edge(root,sid,'contains')
        for take in shot['takes']:
            tid=node('take',sid+':'+str(take['id']),'T'+str(take['id']),'generated' if take.get('generation_job') else 'imported',take['id'])
            aid=ontology.stable_id(namespace,'asset',take['sha256'])
            if not any(n['id']==aid for n in nodes):nodes.append(dict(id=aid,type='asset',label=take.get('filename') or Path(take.get('asset','')).name or '기존 자산',source='sha256:'+take['sha256'],version=None))
            edge(sid,tid,'has_take');edge(tid,aid,'uses_asset')
            if shot['selected']==take['id']:edge(sid,tid,'selected')
        for ref in shot.get('reference_versions',[]):
            for role,origin in ref['roles'].items():
                source_key=json.dumps([origin['song'],origin['shot'],origin['take'],origin['sha256']])
                proxy=ontology.stable_id(namespace,'asset','reference:'+source_key)
                if not any(n['id']==proxy for n in nodes):nodes.append(dict(id=proxy,type='asset',label='참고 원본 · '+origin['song'],source='reference-proxy',version=ref['id'],origin=dict(song=origin['song'],shot=origin['shot'],take=origin['take'],sha256=origin['sha256'])))
                edges.append(dict(source=sid,target=proxy,role=role,reference_version=ref['id']))
    return dict(nodes=nodes,edges=edges,note='실제 저장 객체의 읽기 전용 계보. 외부 작품 참고는 출처 좌표로 표시하며 현재 작품 개체로 자동 병합하지 않습니다.')


def manual_proposal(conn, namespace, data):
    current=ontology.snapshot(conn,namespace);graph=current['graph']
    kind=data['kind']
    if kind not in {'character','place','style'}:raise ValueError('인물·장소·스타일 중 선택하세요.')
    label=data['label'];description=data['description'];evidence=data['evidence']
    if any(not isinstance(v,str) or not v.strip() or len(v)>2000 for v in (label,description,evidence)):raise ValueError('이름·설명·출처를 입력하세요.')
    identifier=data.get('entity')
    existing=next((e for e in graph['entities'] if e['id']==identifier),None) if identifier else None
    if identifier and not existing:raise ValueError('현재 작품의 개체가 아닙니다.')
    if existing and existing['type']!=kind:raise ValueError('기존 개체의 역할은 변경할 수 없습니다.')
    identifier=identifier or str(uuid.uuid4())
    entity=dict(id=identifier,type=kind,label=label,description=description,provenance=[dict(source_id='manual:'+hashlib.sha256(evidence.encode()).hexdigest(),excerpt=evidence)],uncertainty=dict(status='asserted',reason='로컬 사용자가 직접 작성한 진술; 외부 사실 검증 아님'))
    graph['entities']=[e for e in graph['entities'] if e['id']!=identifier]+[entity]
    return ontology.propose(conn,namespace,graph,data['ontology_revision'],'local-owner')


def bind(shot, snapshot, entity_ids):
    if not isinstance(entity_ids,list) or not entity_ids or len(entity_ids)!=len(set(entity_ids)):raise ValueError('연결할 승인 개체를 선택하세요.')
    entities={e['id']:e for e in snapshot['graph']['entities']}
    if any(i not in entities for i in entity_ids):raise ValueError('현재 승인 버전의 개체가 아닙니다.')
    from copy import deepcopy
    shot['semantic_context']=dict(revision=snapshot['revision'],entities=[deepcopy(entities[i]) for i in entity_ids])
    shot['revision']+=1


def impact(shot, snapshot):
    latest={e['id']:e for e in snapshot['graph']['entities']}
    return [dict(id=e['id'],label=e['label'],reason='승인 설정에서 제외됨' if e['id'] not in latest else '연결 후 승인 설정이 변경됨') for e in shot.get('semantic_context',{}).get('entities',[]) if e!=latest.get(e['id'])]
