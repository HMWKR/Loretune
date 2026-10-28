"""S7a: typed schema and argument validator for a future 3D change-proposal tool."""
from copy import deepcopy
import json
import os
from pathlib import Path
import unittest

import scene_spec
from test_scene_contract import sample

ASSET=dict(id='a'*32,sha256='b'*64,profile=scene_spec.ASSET_PROFILES[0])


def op(target,identifier,field,value):return dict(target=target,id=identifier,field=field,value=value)


def args(*operations,base=1):return dict(shot_id='shot-stable-id',base_revision=base,operations=list(operations))


def every_field():
    ids={'camera':'camera','object':'subject','light':'key'}
    values={'position':[1,2,3],'target':[0,0,1],'rotation_degrees':[0,90,0],'scale':[1,2,1],'color':[0.5,0.5,0.5],
            'lens_mm':35,'energy_w':400,'size_m':2,'asset':deepcopy(ASSET)}
    return [op(kind,ids[kind],field,deepcopy(values[field])) for kind,fields in scene_spec.CHANGE_FIELDS.items() for field in fields]


class SceneProposalSchemaTest(unittest.TestCase):
    def test_schema_is_closed_typed_and_has_no_add_or_delete(self):
        schema=scene_spec.PROPOSAL_SCHEMA
        self.assertEqual((schema['required'],schema['additionalProperties']),(['shot_id','base_revision','operations'],False))
        self.assertEqual(schema['properties']['base_revision']['minimum'],1)
        self.assertIn('scene-status',schema['properties']['base_revision']['description'])
        ops=schema['properties']['operations'];self.assertEqual((ops['minItems'],ops['maxItems']),(1,16))
        branches=ops['items']['anyOf'];self.assertEqual(len(branches),13)
        pairs=set()
        for branch in branches:
            self.assertEqual((branch['required'],branch['additionalProperties']),(['target','id','field','value'],False))
            kind=branch['properties']['target']['enum'];field=branch['properties']['field']['enum']
            self.assertEqual((len(kind),len(field)),(1,1));pairs.add((kind[0],field[0]))
        self.assertEqual(pairs,{(k,f) for k,fields in scene_spec.CHANGE_FIELDS.items() for f in fields})
        text=json.dumps(schema)
        for word in ('add','delete','remove','kind','objects','lights'):self.assertNotIn('"'+word+'"',text)
        size=len(text.encode());self.assertLess(size,8192)
        folder=os.environ.get('SCENE_STATUS_EVIDENCE')
        if folder:
            Path(folder).mkdir(parents=True,exist_ok=True);(Path(folder)/'proposal-schema-size.json').write_text(json.dumps(dict(bytes=size,branches=len(branches)))+'\n')

    def test_valid_arguments_cover_every_changeable_field_and_are_detached(self):
        value=args(*every_field());result=scene_spec.validate_proposal(value)
        self.assertEqual(result,value);result['operations'][0]['value'][0]=99;self.assertEqual(value['operations'][0]['value'][0],1)
        applied=scene_spec.propose_changes(sample(),value['operations'],base_revision=1,current_revision=1,
            allowed_fields=[(o['target'],o['id'],o['field']) for o in value['operations']])
        self.assertEqual(len(applied['changes']),13)

    def test_bounds_match_scene_validation(self):
        ids={'camera':'camera','object':'subject','light':'key'}
        for kind,fields in scene_spec.CHANGE_FIELDS.items():
            for field in fields:
                if field=='asset':continue
                vector,lower,upper=scene_spec.VALUE_BOUNDS[field]
                for bound,ok in ((lower,True),(upper,True),(lower-1 if field!='scale' else 0.01,False),(upper+1,False)):
                    value=[bound]*3 if vector else bound
                    operation=op(kind,ids[kind],field,value);allowed=[(kind,ids[kind],field)]
                    with self.subTest(kind=kind,field=field,value=value):
                        if ok:
                            scene_spec.validate_proposal(args(operation))
                            scene_spec.propose_changes(sample(),[operation],base_revision=1,current_revision=1,allowed_fields=allowed)
                        else:
                            with self.assertRaises(ValueError):scene_spec.validate_proposal(args(operation))
                            with self.assertRaises(ValueError):scene_spec.propose_changes(sample(),[operation],base_revision=1,current_revision=1,allowed_fields=allowed)

    def test_base_revision_zero_is_explicitly_rejected(self):
        with self.assertRaisesRegex(ValueError,'no approved scene version'):scene_spec.validate_proposal(args(op('camera','camera','lens_mm',35),base=0))
        for bad in (-1,True,1.0,'1',2**31,None):
            with self.subTest(base=bad),self.assertRaisesRegex(ValueError,'invalid scene revision'):
                scene_spec.validate_proposal(args(op('camera','camera','lens_mm',35),base=bad))

    def test_invalid_shapes_are_rejected(self):
        good=op('camera','camera','lens_mm',35)
        cases=[dict(args(good),extra=1),{k:v for k,v in args(good).items() if k!='shot_id'},dict(args(good),shot_id=''),dict(args(good),shot_id='  '),
               dict(args(good),shot_id='x'*201),dict(args(good),shot_id=7),args(),args(*[good]*17),dict(args(good),operations=good),[],
               args(dict(good,extra=1)),args({k:v for k,v in good.items() if k!='value'}),args(op('camera','other','lens_mm',35)),
               args(op('object','1bad','position',[0,0,0])),args(op('object','x'*33,'position',[0,0,0])),args(op('light',7,'position',[0,0,0])),
               args(good,good),args(op('camera','camera','position',[0,0])),args(op('camera','camera','position',[0,0,0,0])),
               args(op('camera','camera','position',[True,0,0])),args(op('camera','camera','lens_mm',float('nan'))),args(op('camera','camera','lens_mm',float('inf'))),
               args(op('camera','camera','lens_mm','35')),args(op('light','key','energy_w',[1,1,1])),args(op('object','subject','asset',dict(ASSET,sha256='z'*64))),
               args(op('object','subject','asset',dict(ASSET,profile='unknown'))),args(op('object','subject','asset',dict(ASSET,path='/tmp/x.glb'))),
               args(op('camera','camera','asset',deepcopy(ASSET))),args(op('light','key','rotation_degrees',[0,0,0]))]
        for index,case in enumerate(cases):
            with self.subTest(index=index),self.assertRaises(ValueError):scene_spec.validate_proposal(case)

    def test_add_and_delete_attempts_are_rejected(self):
        attempts=[args(dict(op='add',target='object',id='new',field='position',value=[0,0,0])),
                  args(op('object','new','add',dict(kind='cube'))),args(op('object','subject','delete',True)),
                  args(op('objects','new','position',[0,0,0])),args(op('object','subject','kind','sphere')),
                  args(op('object','subject','id','renamed')),args(op('scene','scene','objects',[])),args(op('light','key','remove',True))]
        for index,case in enumerate(attempts):
            with self.subTest(index=index),self.assertRaises(ValueError):scene_spec.validate_proposal(case)
        # A well-formed id that names no existing object cannot create one at apply time.
        operation=op('object','new','position',[0,0,0]);scene_spec.validate_proposal(args(operation))
        with self.assertRaisesRegex(ValueError,'scene target not found'):
            scene_spec.propose_changes(sample(),[operation],base_revision=1,current_revision=1,allowed_fields=[('object','new','position')])


if __name__=='__main__':
    unittest.main()
