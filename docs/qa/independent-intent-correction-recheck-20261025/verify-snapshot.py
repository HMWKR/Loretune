from pathlib import Path
import json,hashlib,datetime,ast,re
r=Path('/Users/leesungmin/Desktop/Loretune');o=r/'docs/qa/independent-intent-correction-recheck-20261025';o.mkdir(parents=True,exist_ok=True);s=o/'snapshot'
rel=Path('docs/qa/benchmark-provider-correction-20261025');release=json.loads((r/rel/'integrated/fixed-release.json').read_text())
paths=list(release['source_sha256'])+['fal_provider.py','live_launcher.py','chat_runtime.py','ledger.py','media_bridge.py','Master_Specification.md','docs/originals/Master_Specification.md','07_Chat_Directed_Multimodel_Production_Spec.md',str(rel/'REPORT-ko.md'),str(rel/'integrated/fixed-release.json'),str(rel/'historical-inactive/README.md')]
kits=['docs/knowledge/project_kit','docs/specification/IP_Music_Video_Platform/project_kit']
for kit in kits:
 paths.append(kit+'/registry/knowledge.json')
 paths += [str(p.relative_to(r)) for p in (r/kit/'docs/modules/spec-ms-001/20261025').iterdir() if p.is_file()]
manifest=[]
for n in sorted(set(paths)):
 p=r/n;b=p.read_bytes();q=s/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b);manifest.append(dict(path=n,bytes=len(b),mtime_ns=p.stat().st_mtime_ns,sha256=hashlib.sha256(b).hexdigest()))
(o/'snapshot-manifest.json').write_text(json.dumps(dict(captured_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=manifest),ensure_ascii=False,indent=2)+'\n')
hashmap={x['path']:x['sha256'] for x in manifest};e={'release_source_mismatches':[n for n,h in release['source_sha256'].items() if hashmap[n]!=h],'registries':[]}
for i,kit in enumerate(kits):
 d=json.loads((s/kit/'registry/knowledge.json').read_text());old=json.loads((r/'docs/qa/independent-intent-alignment-audit-20261025/snapshot'/kit/'registry/knowledge.json').read_text());objs={x['id']:x for x in d['objects']};oldobjs={x['id']:x for x in old['objects']}
 head=lambda k:objs[d['heads'][k]]
 fr=[head('Requirement:MS-FR-%02d'%n) for n in range(1,29)];ats=[head('Test:MS-AT%02d'%n) for n in range(1,39)];doc=head('Document:SPEC-MS-001')
 cat=json.loads((s/kit/'docs/modules/spec-ms-001/20261025/catalog.json').read_text());cov=json.loads((s/kit/'docs/modules/spec-ms-001/20261025/coverage.json').read_text());lines=(s/'07_Chat_Directed_Multimodel_Production_Spec.md').read_text().splitlines()
 source_errors=[x['id'] for x in cat['requirements'] if x['id'] not in lines[x['line']-1] or x['title'] not in lines[x['line']-1]]
 source_errors += [x['id'] for x in cat['tests'] if x['trigger'] not in lines[x['line']-1] or x['expected'] not in lines[x['line']-1]]
 file_errors=[]
 for x in d['objects']:
  if x.get('namespace')=='MS20261025' and x.get('file') and x.get('sha256'):
   p=r/kit/x['file'];actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
   if actual!=x['sha256']:file_errors.append(x['id'])
 row=dict(path=kit,hash_matches_release=hashmap[kit+'/registry/knowledge.json']==release['registry'][i]['sha256'],revision=d['registry_revision'],objects=len(objs),heads=len(d['heads']),old_object_changes=[k for k,v in oldobjs.items() if objs.get(k)!=v],old_head_changes=[k for k,v in old['heads'].items() if d['heads'].get(k)!=v],requirements=len(fr),tests=len(ats),bad_test_status=[x['id'] for x in ats if x.get('execution_status')!='not_run' or x.get('acceptance_status')!='not_fully_verified' or x.get('verification_level')!='unverified'],bad_coverage_status=[x['id'] for x in cov if x.get('execution_status')!='not_run' or x.get('acceptance_status')!='not_fully_verified'],editorial_only=all(x['approval']['scope']=='editorial_baseline' for x in [doc]+fr+ats),unimplemented={x['canonical_key']:x.get('implementation_status') for x in fr if x['canonical_key'] in ['Requirement:MS-FR-22','Requirement:MS-FR-28']},source_line_errors=source_errors,module_document_hash_errors=file_errors,original_spec_preserved=hashlib.sha256((s/kit/doc['file']).read_bytes()).hexdigest()==release['original_spec_sha256'],decision_ids=[x['id'] for x in d['objects'] if x.get('kind')=='Decision' and 'RUNWAY' in x['id']])
 e['registries'].append(row)
e['trial_files_unchanged_from_previous_audit']={n:hashmap[n]==hashlib.sha256((r/'docs/qa/independent-intent-alignment-audit-20261025/snapshot'/n).read_bytes()).hexdigest() for n in ['fal_provider.py','live_launcher.py','chat_runtime.py','ledger.py']}
e['master_preserved']=hashmap['Master_Specification.md']==hashmap['docs/originals/Master_Specification.md']==hashlib.sha256((r/'docs/qa/independent-intent-alignment-audit-20261025/snapshot/Master_Specification.md').read_bytes()).hexdigest()
(o/'verification.json').write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n');print(json.dumps(e,ensure_ascii=False,indent=2))
