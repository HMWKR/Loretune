"""Canonical local asset authorization at action claim; no model authority flags."""
import hashlib,stat,os
from pathlib import Path

def validate(c,store,project,job):
    inputs=job['action']['inputs']
    if set(inputs)-{'prompt','asset_refs'}:raise ValueError('unsupported action input')
    refs=inputs.get('asset_refs',[])
    if not isinstance(refs,list) or len(refs)>16:raise ValueError('asset reference limit')
    takes=[(name,t) for name,sh in project.get('shots',{}).items() for t in sh.get('takes',[])]
    selected=[]
    for ref in refs:
        if not isinstance(ref,dict) or set(ref)!={'shot','take','sha256','role'}:raise ValueError('server asset reference required')
        if ref['role'] not in {'character','style','start_frame','end_frame'} or type(ref['take']) is not int:raise ValueError('asset role/type')
        found=next((t for n,t in takes if n==ref['shot'] and t['id']==ref['take'] and t['sha256']==ref['sha256']),None)
        if found is None:raise ValueError('asset does not belong to this project')
        selected.append(found)
    # A collected dependency is not sufficient: its file must still be registered,
    # owned in this project and currently permitted at the claim boundary.
    for dep in job.get('dependencies',[]):
        matches=[t for _,t in takes if t['sha256']==dep['result']['sha256']]
        if not matches:raise ValueError('dependency asset is not registered in this project')
        selected.extend(matches)
    for take in selected:
        if not isinstance(take.get('rights'),str) or not take['rights'].strip() or take['rights']=='사용권 미확인':raise ValueError('asset rights evidence missing')
        store.check_rights(c,[take['sha256']])
        path=Path(take['asset']);base=(store.root/'assets').resolve()
        if path.is_symlink() or path.resolve().parent!=base or path.stem!=take['sha256']:raise ValueError('asset location invalid')
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
        with os.fdopen(fd,'rb') as f:
            info=os.fstat(f.fileno())
            if not stat.S_ISREG(info.st_mode) or not 0<info.st_size<=16*1024*1024:raise ValueError('asset file invalid')
            raw=f.read(16*1024*1024+1)
            if len(raw)!=info.st_size or hashlib.sha256(raw).hexdigest()!=take['sha256']:raise ValueError('asset content changed')
    return True
