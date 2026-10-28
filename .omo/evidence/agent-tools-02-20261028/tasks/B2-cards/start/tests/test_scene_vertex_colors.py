"""Closed-profile vertex colors: self-authored fixtures and immutable v1 contract."""
from copy import deepcopy
import hashlib
import struct
import unittest

import scene_assets
import scene_spec
from scene_asset_fixtures import glb_parts, pack_glb, textured_glb
from test_scene_contract import sample

COLOR_PROFILE = 'gltf2-static-pbr-color-v2'


def color_glb(component=5121, dimension=4, *, normalized=True, values=None, extras=True):
    document,binary=glb_parts(textured_glb())
    primitive=document['meshes'][0]['primitives'][0]
    count=document['accessors'][primitive['attributes']['POSITION']]['count']
    maximum={5121:255,5123:65535,5126:1}[component]
    if values is None:values=[tuple([maximum,0,maximum//2]+([maximum] if dimension==4 else []))]*count
    color=struct.pack('<'+{5121:'B',5123:'H',5126:'f'}[component]*sum(map(len,values)),*(v for row in values for v in row))
    # RGB integer elements need four-byte strides in vertex buffers.
    element=dimension*{5121:1,5123:2,5126:4}[component];stride=(element+3)//4*4
    color=b''.join(color[i:i+element]+b'\0'*(stride-element) for i in range(0,len(color),element))
    offset=(len(binary)+3)//4*4;binary+=b'\0'*(offset-len(binary))+color
    document['bufferViews'].append(dict(buffer=0,byteOffset=offset,byteLength=len(color),byteStride=stride,target=34962))
    accessor=dict(bufferView=len(document['bufferViews'])-1,componentType=component,type='VEC'+str(dimension),count=count)
    if normalized is not None:accessor['normalized']=normalized
    document['accessors'].append(accessor);primitive['attributes']['COLOR_0']=len(document['accessors'])-1
    document['buffers'][0]['byteLength']=len(binary)
    if extras:document['meshes'][0]['extras']={'processed':True}
    return pack_glb(document,binary)


class VertexColorTest(unittest.TestCase):
    def test_supported_formats_preserve_original_hash(self):
        for component in (5121,5123,5126):
            for dimension in (3,4):
                with self.subTest(component=component,dimension=dimension):
                    raw=color_glb(component,dimension,normalized=None if component==5126 else True)
                    metadata=scene_assets.validate_glb(raw)
                    self.assertEqual(metadata['profile'],COLOR_PROFILE)
                    self.assertEqual(metadata['sha256'],hashlib.sha256(raw).hexdigest())

    def test_invalid_colors_and_metadata_rejected(self):
        raw=color_glb();doc,binary=glb_parts(raw)
        mutations=[lambda d:d['accessors'][-1].update(count=1),lambda d:d['accessors'][-1].update(type='VEC2'),lambda d:d['accessors'][-1].update(normalized=False),lambda d:d['accessors'][-1].update(componentType=5125),lambda d:d['meshes'][0].update(extras={'processed':1}),lambda d:d['meshes'][0].update(extras={'processed':False}),lambda d:d['meshes'][0].update(extras={'processed':True,'script':'run'}),lambda d:d['nodes'][0].update(extras={'processed':True}),lambda d:d.update(extras={'processed':True}),lambda d:d['meshes'][0].update(extensions={}),lambda d:d['accessors'][-1].update(sparse={})]
        for mutate in mutations:
            d=deepcopy(doc);mutate(d)
            with self.subTest(document=d),self.assertRaises(ValueError):scene_assets.validate_glb(pack_glb(d,binary))
        for value in (-.1,1.1,float('nan'),float('inf')):
            with self.subTest(value=value),self.assertRaises(ValueError):
                scene_assets.validate_glb(color_glb(5126,normalized=None,values=[(value,0,0,1)]*24))
        for component,alpha in ((5121,254),(5123,65534),(5126,.99)):
            with self.subTest(alpha=alpha),self.assertRaises(ValueError):
                scene_assets.validate_glb(color_glb(component,normalized=None if component==5126 else True,values=[(0,0,0,alpha)]*24))

    def test_v1_remains_exact_and_disallows_extras(self):
        raw=textured_glb();metadata=scene_assets.validate_glb(raw)
        self.assertEqual(metadata,dict(profile='gltf2-static-pbr-v1',sha256=hashlib.sha256(raw).hexdigest(),byte_length=len(raw),vertex_count=24,triangle_count=12,image_count=1,node_count=1))
        document,binary=glb_parts(raw);document['meshes'][0]['extras']={'processed':True}
        with self.assertRaises(ValueError):scene_assets.validate_glb(pack_glb(document,binary))

    def test_scene_preserves_actual_profile_and_rejects_forgery(self):
        scene=sample();scene['schema_version']=2;obj=scene['objects'][0];obj.pop('color');obj.update(kind='mesh',asset=dict(id='a'*32,sha256='b'*64,profile=COLOR_PROFILE))
        self.assertEqual(scene_spec.validate(scene),scene)
        for profile in ('gltf2-static-pbr-color-v3',{},None):
            obj['asset']['profile']=profile
            with self.assertRaises(ValueError):scene_spec.validate(scene)


class VertexColorHTTPTest(unittest.TestCase):
    # Reuse server lifecycle only; do not duplicate the fixture's inherited tests.
    from test_scene_workflow import SceneWorkflowTest as _Fixture
    setUp=_Fixture.setUp
    close_server=_Fixture.close_server
    state=_Fixture.state
    post=_Fixture.post
    shot_id=_Fixture.shot_id

    def test_mixed_profiles_persist_and_forged_reference_is_rejected(self):
        import base64
        from urllib.error import HTTPError
        assets=[]
        for raw,profile in ((textured_glb(),scene_assets.PROFILE),(color_glb(),COLOR_PROFILE)):
            asset=self.post('scene_asset_import',song='A',filename='color.glb',content=base64.b64encode(raw).decode(),rights='self authored')['scene_asset']
            self.assertEqual(asset['profile'],profile);assets.append(asset)
        self.assertEqual([x['profile'] for x in self.state()['projects']['A']['scene_3d_assets']],[scene_assets.PROFILE,COLOR_PROFILE])
        for asset,wrong in ((assets[0],COLOR_PROFILE),(assets[1],scene_assets.PROFILE)):
            scene=sample();scene['schema_version']=2;obj=scene['objects'][0];obj.pop('color');obj.update(kind='mesh',asset={k:asset[k] for k in ('id','sha256','profile')});obj['asset']['profile']=wrong
            with self.assertRaises(HTTPError) as error:self.post('scene_create',song='A',shot_id=self.shot_id(),scene=scene)
            self.assertEqual(error.exception.code,400);error.exception.close()
