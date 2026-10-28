import copy
import hashlib
import json
import random
import struct
import unittest
import zlib
from unittest.mock import patch

import scene_assets as assets
from tests.scene_asset_fixtures import glb_parts,jpeg,pack_glb,png,textured_glb


def altered(change):
    document,binary=glb_parts(textured_glb())
    binary=bytearray(binary);change(document,binary)
    return pack_glb(document,binary)


def texture(image,mime='image/png'):
    document,binary=glb_parts(textured_glb())
    view=document['bufferViews'][document['images'][0]['bufferView']]
    binary=binary[:view['byteOffset']]+image
    view['byteLength']=len(image);document['buffers'][0]['byteLength']=len(binary)
    document['images'][0]['mimeType']=mime
    return pack_glb(document,binary)


def geometry(vertex_count=3,triangle_count=1):
    points=[(-1.0,-1.0,0.0),(1.0,-1.0,0.0),(0.0,1.0,0.0)]
    positions=b''.join(struct.pack('<fff',*points[i%3]) for i in range(vertex_count))
    indices=bytes((0,1,2))*triangle_count
    document={'asset':{'version':'2.0'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0}],
              'meshes':[{'primitives':[{'attributes':{'POSITION':0},'indices':1}]}],
              'accessors':[{'bufferView':0,'componentType':5126,'count':vertex_count,'type':'VEC3','min':[-1,-1,0],'max':[1,1,0]},
                           {'bufferView':1,'componentType':5121,'count':triangle_count*3,'type':'SCALAR'}],
              'bufferViews':[{'buffer':0,'byteLength':len(positions),'target':34962},
                             {'buffer':0,'byteOffset':len(positions),'byteLength':len(indices),'target':34963}],
              'buffers':[{'byteLength':len(positions)+len(indices)}]}
    return pack_glb(document,positions+indices)


class SceneAssetsTest(unittest.TestCase):
    def test_self_authored_texture_cube_returns_exact_metadata_without_rewriting_bytes(self):
        raw=textured_glb();saved=raw[:]
        self.assertEqual(assets.validate_glb(raw),dict(profile=assets.PROFILE,sha256=hashlib.sha256(raw).hexdigest(),
            byte_length=len(raw),vertex_count=24,triangle_count=12,image_count=1,node_count=1))
        self.assertEqual(raw,saved)
        self.assertEqual(assets.PROFILE,'gltf2-static-pbr-v1')

    def test_valid_jpeg_texture_and_core_pbr_slots(self):
        raw=texture(jpeg(),'image/jpeg')
        self.assertEqual(assets.validate_glb(raw)['image_count'],1)
        def change(document,_):
            document['samplers']=[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':33071}]
            document['textures'][0]['sampler']=0
            material=document['materials'][0]
            material.update(normalTexture={'index':0,'scale':0.5},occlusionTexture={'index':0,'strength':0.8},
                            emissiveTexture={'index':0},emissiveFactor=[0.1,0.2,0.3],alphaMode='BLEND',doubleSided=True)
            material['pbrMetallicRoughness'].update(metallicRoughnessTexture={'index':0},baseColorFactor=[1,0.5,0.4,0.8])
        self.assertEqual(assets.validate_glb(altered(change))['triangle_count'],12)

    def test_embedded_images_return_original_slices_only_after_full_admission(self):
        self.assertEqual(assets.embedded_images(textured_glb()),[{'mime_type':'image/png','data':png()}])
        self.assertEqual(assets.embedded_images(texture(jpeg(),'image/jpeg')),[{'mime_type':'image/jpeg','data':jpeg()}])
        self.assertEqual(assets.embedded_images(geometry()),[])
        with self.assertRaises(ValueError):assets.embedded_images(altered(lambda d,_:d['images'][0].update(uri='file:///private')))

    def test_glb_header_lengths_chunks_padding_and_input_types(self):
        raw=textured_glb()
        variants=[b'',bytearray(raw),memoryview(raw),b'glTF'+raw[4:8],raw+b'junk',raw[:-1]]
        for offset,value in ((0,b'bad!'),(4,struct.pack('<I',1)),(8,struct.pack('<I',len(raw)+4)),(16,struct.pack('<I',0x004e4942))):
            modified=bytearray(raw);modified[offset:offset+4]=value;variants.append(bytes(modified))
        modified=bytearray(raw);struct.pack_into('<I',modified,12,struct.unpack_from('<I',raw,12)[0]-1);variants.append(bytes(modified))
        for variant in variants:
            with self.subTest(kind=type(variant).__name__,size=len(variant)),self.assertRaises(ValueError):assets.validate_glb(variant)
        with self.assertRaises(ValueError):assets.validate_glb(b'x'*(assets.MAX_BYTES+1))

    def test_external_and_data_uris_are_rejected_without_returning_the_input(self):
        for location in ('buffers','images'):
            for uri in ('https://secret.invalid/private','file:///etc/passwd','../../outside','data:application/octet-stream;base64,AAAA'):
                raw=altered(lambda document,_:document[location][0].update(uri=uri))
                with self.subTest(location=location,uri=uri),self.assertRaises(ValueError) as failure:assets.validate_glb(raw)
                self.assertNotIn(uri,str(failure.exception))

    def test_animation_skin_morph_camera_extensions_and_custom_metadata_are_not_silently_ignored(self):
        changes=[lambda d,_:d.update(animations=[]),lambda d,_:d.update(skins=[]),lambda d,_:d.update(cameras=[]),
                 lambda d,_:d.update(extensionsUsed=['EXT_meshopt_compression']),
                 lambda d,_:d['nodes'][0].update(camera=0),lambda d,_:d['nodes'][0].update(skin=0),
                 lambda d,_:d['nodes'][0].update(extras={'script':'not executed'}),
                 lambda d,_:d['materials'][0].update(extensions={'KHR_materials_unlit':{}}),
                 lambda d,_:d['meshes'][0]['primitives'][0].update(targets=[])]
        for index,change in enumerate(changes):
            with self.subTest(index=index),self.assertRaises(ValueError):assets.validate_glb(altered(change))
        self.assertEqual(assets.validate_glb(altered(lambda d,_:d.update(extensionsUsed=[],extensionsRequired=[])))['vertex_count'],24)

    def test_json_duplicates_nonfinite_numbers_depth_and_unknown_keys(self):
        document,binary=glb_parts(textured_glb())
        for encoded in (b'{"asset":{},"asset":{}}',b'{"asset":NaN}',b'{"asset":Infinity}',b'['*25+b'0'+b']'*25):
            encoded+=b' '*((-len(encoded))%4);body=binary+b'\0'*((-len(binary))%4)
            raw=struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(body))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(body),0x004e4942)+body
            with self.subTest(encoded=encoded[:20]),self.assertRaises(ValueError):assets.validate_glb(raw)
        for change in (lambda d,_:d['nodes'][0].update(translation=[float('inf'),0,0]),
                       lambda d,_:d.update(unrecognized={'anything':True}),lambda d,_:d['asset'].update(version='2.1'),
                       lambda d,_:d['accessors'][0].update(count=True)):
            with self.assertRaises(ValueError):assets.validate_glb(altered(change))

    def test_buffer_view_accessor_bounds_alignment_stride_sparse_and_types(self):
        changes=[lambda d,_:d['bufferViews'][0].update(byteOffset=8*1024*1024),
                 lambda d,_:d['bufferViews'][0].update(byteLength=-1),lambda d,_:d['bufferViews'][0].update(buffer=1),
                 lambda d,_:d['bufferViews'][0].update(byteStride=10),lambda d,_:d['bufferViews'][0].update(byteStride=4),
                 lambda d,_:d['accessors'][0].update(byteOffset=2),lambda d,_:d['accessors'][0].update(count=500001),
                 lambda d,_:d['accessors'][0].update(sparse={'count':1}),lambda d,_:d['accessors'][0].update(type='MAT4'),
                 lambda d,_:d['accessors'][0].update(componentType=5123),lambda d,_:d['accessors'][3].update(normalized=True),
                 lambda d,_:d['bufferViews'][3].update(byteStride=4),lambda d,_:d['buffers'][0].update(byteLength=1)]
        for index,change in enumerate(changes):
            with self.subTest(index=index),self.assertRaises(ValueError):assets.validate_glb(altered(change))

    def test_one_buffer_view_cannot_mix_attributes_and_indices_without_target_hint(self):
        document,binary=glb_parts(geometry())
        index_offset=document['bufferViews'][1]['byteOffset']
        document['bufferViews']=[{'buffer':0,'byteLength':len(binary)}]
        document['accessors'][1].update(bufferView=0,byteOffset=index_offset)
        with self.assertRaises(ValueError):assets.validate_glb(pack_glb(document,binary))

    def test_nonfinite_binary_vertices_invalid_indices_and_false_bounds(self):
        document,binary=glb_parts(textured_glb())
        for value in (float('nan'),float('inf'),float('-inf'),assets.MAX_COORDINATE*2):
            changed=bytearray(binary);struct.pack_into('<f',changed,0,value)
            with self.subTest(value=value),self.assertRaises(ValueError):assets.validate_glb(pack_glb(document,changed))
        changed=bytearray(binary);offset=document['bufferViews'][3]['byteOffset'];struct.pack_into('<H',changed,offset,24)
        with self.assertRaises(ValueError):assets.validate_glb(pack_glb(document,changed))
        with self.assertRaises(ValueError):assets.validate_glb(altered(lambda d,_:d['accessors'][0].update(max=[0,0,0])))

    def test_attribute_counts_uv_and_triangle_mode(self):
        changes=[lambda d,_:d['accessors'][1].update(count=23),
                 lambda d,_:d['meshes'][0]['primitives'][0]['attributes'].pop('TEXCOORD_0'),
                 lambda d,_:d['meshes'][0]['primitives'][0].update(mode=5),
                 lambda d,_:d['accessors'][3].update(count=35),
                 lambda d,_:d['materials'][0]['pbrMetallicRoughness']['baseColorTexture'].update(texCoord=1)]
        for index,change in enumerate(changes):
            with self.subTest(index=index),self.assertRaises(ValueError):assets.validate_glb(altered(change))

    def test_node_tree_cycles_duplicates_shared_children_and_disconnected_nodes(self):
        changes=[lambda d,_:d['nodes'][0].update(children=[0]),
                 lambda d,_:d['scenes'][0].update(nodes=[0,0]),
                 lambda d,_:d['nodes'].append({'mesh':0}),
                 lambda d,_:(d.update(nodes=[{'children':[1,2]},{'mesh':0,'children':[2]},{'mesh':0}]),d['scenes'][0].update(nodes=[0])),
                 lambda d,_:d['nodes'][0].update(children=[0,0]),lambda d,_:d['nodes'][0].update(children=[True])]
        for index,change in enumerate(changes):
            with self.subTest(index=index),self.assertRaises(ValueError):assets.validate_glb(altered(change))

    def test_node_transform_validity_composed_world_bounds_and_instancing(self):
        def valid(document,_):
            document['nodes']=[{'translation':[1,0,0],'children':[1]}, {'mesh':0,'scale':[0.5,0.5,0.5]}]
        self.assertEqual(assets.validate_glb(altered(valid))['node_count'],2)
        matrix=[1,0,0,0,0,1,0,0,0,0,1,0,1,2,3,1]
        self.assertEqual(assets.validate_glb(altered(lambda d,_:d['nodes'][0].update(matrix=matrix)))['triangle_count'],12)
        changes=[lambda d,_:d['nodes'][0].update(rotation=[0,0,0,0]),lambda d,_:d['nodes'][0].update(scale=[1,0,1]),
                 lambda d,_:d['nodes'][0].update(matrix=matrix,translation=[0,0,0]),
                 lambda d,_:d['nodes'][0].update(matrix=matrix[:-1]+[2]),
                 lambda d,_:(d.update(nodes=[{'children':[1],'scale':[10000]*3},{'mesh':0,'scale':[10000]*3}]),d['scenes'][0].update(nodes=[0]))]
        for index,change in enumerate(changes):
            with self.subTest(index=index),self.assertRaises(ValueError):assets.validate_glb(altered(change))
        def instances(document,_):
            document['nodes']=[{'mesh':0},{'mesh':0,'translation':[3,0,0]}];document['scenes'][0]['nodes']=[0,1]
        self.assertEqual(assets.validate_glb(altered(instances))['triangle_count'],24)
        with patch.object(assets,'MAX_VERTICES',24),self.assertRaises(ValueError):assets.validate_glb(altered(instances))

    def test_world_bounds_use_decoded_vertices_instead_of_rounded_declared_extrema(self):
        document,binary=glb_parts(geometry());binary=bytearray(binary)
        struct.pack_into('<f',binary,12,1.000005)
        document['nodes'][0]['matrix']=[1000000,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
        with self.assertRaises(ValueError):assets.validate_glb(pack_glb(document,binary))

    def test_geometry_admission_limits_include_boundary_and_rendered_instances(self):
        self.assertEqual(assets.validate_glb(geometry(assets.MAX_VERTICES))['vertex_count'],assets.MAX_VERTICES)
        with self.assertRaises(ValueError):assets.validate_glb(geometry(assets.MAX_VERTICES+1))
        self.assertEqual(assets.validate_glb(geometry(triangle_count=assets.MAX_TRIANGLES))['triangle_count'],assets.MAX_TRIANGLES)
        with self.assertRaises(ValueError):assets.validate_glb(geometry(triangle_count=assets.MAX_TRIANGLES+1))

    def test_png_crc_compressed_size_filters_and_dimensions(self):
        good=png();bad=bytearray(good);bad[-5]^=1
        variants=[bytes(bad),good[:-2],good+b'junk']
        def chunk(kind,content):return struct.pack('>I',len(content))+kind+content+struct.pack('>I',zlib.crc32(kind+content)&0xffffffff)
        header=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',2,2,8,6,0,0,0))
        variants.extend([header+chunk(b'IDAT',zlib.compress(b'\0'*10000))+chunk(b'IEND',b''),
                         header+chunk(b'IDAT',zlib.compress(bytes([5])+b'\0'*17))+chunk(b'IEND',b''),
                         header+chunk(b'IDAT',b'broken')+chunk(b'IEND',b'')])
        for variant in variants:
            with self.assertRaises(ValueError):assets.validate_glb(texture(variant))
        oversized=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',2049,1,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0'))+chunk(b'IEND',b'')
        with self.assertRaises(ValueError):assets.validate_glb(texture(oversized))
        with self.assertRaises(ValueError):assets.validate_glb(texture(header+chunk(b'acTL',struct.pack('>II',2,0))+chunk(b'IDAT',zlib.compress(b'\0'*18))+chunk(b'IEND',b'')))

    def test_png_ancillary_chunks_respect_color_length_singleton_and_order(self):
        def chunk(kind,content):return struct.pack('>I',len(content))+kind+content+struct.pack('>I',zlib.crc32(kind+content)&0xffffffff)
        source=png()
        invalid=[chunk(b'tRNS',b'\0'),chunk(b'sRGB',b'\x04'),chunk(b'gAMA',b'\0'),
                 chunk(b'pHYs',b'\0'*8+b'\x02'),chunk(b'bKGD',b'\0'),chunk(b'sBIT',b'\x09'*4),
                 chunk(b'sRGB',b'\0')*2]
        for metadata in invalid:
            with self.subTest(metadata=metadata[:12]),self.assertRaises(ValueError):assets.validate_glb(texture(source[:33]+metadata+source[33:]))
        # Metadata after the compressed image stream is outside this profile.
        with self.assertRaises(ValueError):assets.validate_glb(texture(source[:-12]+chunk(b'sRGB',b'\0')+source[-12:]))
        grayscale=(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,0,0,0,0))+
                   chunk(b'tRNS',b'\0\x22')+chunk(b'IDAT',zlib.compress(b'\0\x22'))+chunk(b'IEND',b''))
        self.assertEqual(assets.validate_glb(texture(grayscale))['image_count'],1)
        indexed=(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,3,0,0,0))+
                 chunk(b'PLTE',b'\x20\x20\x20')+chunk(b'IDAT',zlib.compress(b'\0\xff'))+chunk(b'IEND',b''))
        with self.assertRaises(ValueError):assets.validate_glb(texture(indexed))

    def test_jpeg_dimensions_truncation_and_conflicting_frame_headers(self):
        good=jpeg();position=good.index(b'\xff\xc0');changed=bytearray(good)
        struct.pack_into('>H',changed,position+7,4096)
        for variant in (good[:-1],good+b'junk',bytes(changed),b'not a JPEG'):
            with self.assertRaises(ValueError):assets.validate_glb(texture(variant,'image/jpeg'))
        length=struct.unpack_from('>H',good,position+2)[0]
        duplicate=good[:position]+good[position:position+2+length]+good[position:]
        with self.assertRaises(ValueError):assets.validate_glb(texture(duplicate,'image/jpeg'))

    def test_image_count_aggregate_pixels_and_bad_pbr_references(self):
        def extra_image(document,_):document['images'].append(copy.deepcopy(document['images'][0]))
        with patch.object(assets,'MAX_IMAGE_PIXELS',7),self.assertRaises(ValueError):assets.validate_glb(altered(extra_image))
        changes=[lambda d,_:d['images'][0].update(bufferView=0,mimeType='image/png'),
                 lambda d,_:d['textures'][0].update(source=10),lambda d,_:d['materials'][0].update(doubleSided='yes'),
                 lambda d,_:d['materials'][0]['pbrMetallicRoughness'].update(metallicFactor=2),
                 lambda d,_:d['materials'][0]['pbrMetallicRoughness'].update(baseColorFactor=[1,1,1,float('nan')]),
                 lambda d,_:d['textures'][0].update(sampler=0)]
        for index,change in enumerate(changes):
            with self.subTest(index=index),self.assertRaises(ValueError):assets.validate_glb(altered(change))

    def test_unused_images_textures_materials_and_meshes_do_not_bypass_native_decode_accounting(self):
        changes=[lambda d,_:d['images'].append(copy.deepcopy(d['images'][0])),
                 lambda d,_:d['textures'].append(copy.deepcopy(d['textures'][0])),
                 lambda d,_:d['materials'].append({'pbrMetallicRoughness':{'roughnessFactor':0.4}}),
                 lambda d,_:d['meshes'].append(copy.deepcopy(d['meshes'][0]))]
        for index,change in enumerate(changes):
            with self.subTest(index=index),self.assertRaises(ValueError):assets.validate_glb(altered(change))

    def test_mutated_bytes_never_leak_parser_exceptions(self):
        raw=textured_glb();randomizer=random.Random(14)
        for _ in range(100):
            changed=bytearray(raw);offset=randomizer.randrange(len(changed));changed[offset]^=randomizer.randrange(1,256)
            try:metadata=assets.validate_glb(bytes(changed))
            except ValueError:continue
            self.assertEqual(metadata['sha256'],hashlib.sha256(changed).hexdigest())


if __name__=='__main__':unittest.main()
