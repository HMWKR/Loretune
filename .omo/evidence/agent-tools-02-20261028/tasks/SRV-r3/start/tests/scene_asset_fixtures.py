"""Self-authored GLB fixtures; no downloaded models or third-party textures."""
import json
import base64
import struct
import zlib


def pack_glb(document, binary):
    encoded=json.dumps(document,separators=(',',':'),allow_nan=True).encode('utf-8')
    encoded+=b' '*((-len(encoded))%4)
    binary=bytes(binary);binary+=b'\0'*((-len(binary))%4)
    length=12+8+len(encoded)+8+len(binary)
    return (struct.pack('<4sII',b'glTF',2,length)+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+
            struct.pack('<II',len(binary),0x004e4942)+binary)


def glb_parts(raw):
    json_length=struct.unpack_from('<I',raw,12)[0]
    document=json.loads(raw[20:20+json_length])
    binary_start=20+json_length+8
    binary=raw[binary_start:binary_start+document['buffers'][0]['byteLength']]
    return document,binary


def png(width=2,height=2):
    def chunk(kind,content):
        return struct.pack('>I',len(content))+kind+content+struct.pack('>I',zlib.crc32(kind+content)&0xffffffff)
    rows=[]
    colors=[b'\xff\x20\x20\xff',b'\x20\x40\xff\xff',b'\x20\xff\x40\xff',b'\xff\xff\xff\xff']
    for y in range(height):rows.append(b'\0'+b''.join(colors[(x+y*width)%4] for x in range(width)))
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6,0,0,0))+
            chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b''))


def jpeg():
    """Self-authored red 8x8 JPEG, encoded once with local FFmpeg lavfi."""
    return base64.b64decode('/9j/4AAQSkZJRgABAgAAAQABAAD//gAPTGF2YzYzLjEuMTAyAP/bAEMACAQEBAQEBQUFBQUFBgYGBgYGBgYGBgYGBgcHBwgICAcHBwYGBwcICAgICQkJCAgICAkJCgoKDAwLCw4ODhERFP/EAEwAAQEAAAAAAAAAAAAAAAAAAAAGAQEBAAAAAAAAAAAAAAAAAAAGBxABAAAAAAAAAAAAAAAAAAAAABEBAAAAAAAAAAAAAAAAAAAAAP/AABEIAAgACAMBIgACEQADEQD/2gAMAwEAAhEDEQA/AIsATX9//9k=')


def textured_glb():
    """A unit-radius cube with six UV faces and an embedded 2x2 RGBA texture."""
    faces=[
        ((0,0,1),[(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]),
        ((0,0,-1),[(1,-1,-1),(-1,-1,-1),(-1,1,-1),(1,1,-1)]),
        ((1,0,0),[(1,-1,1),(1,-1,-1),(1,1,-1),(1,1,1)]),
        ((-1,0,0),[(-1,-1,-1),(-1,-1,1),(-1,1,1),(-1,1,-1)]),
        ((0,1,0),[(-1,1,1),(1,1,1),(1,1,-1),(-1,1,-1)]),
        ((0,-1,0),[(-1,-1,-1),(1,-1,-1),(1,-1,1),(-1,-1,1)]),
    ]
    positions=[];normals=[];uv=[];indices=[]
    for index,(normal,vertices) in enumerate(faces):
        positions.extend(c for vertex in vertices for c in vertex)
        normals.extend(c for _ in vertices for c in normal)
        uv.extend((0,0,1,0,1,1,0,1))
        indices.extend(index*4+i for i in (0,1,2,0,2,3))
    binary=bytearray();views=[]
    def add(data,target=None):
        binary.extend(b'\0'*((-len(binary))%4));offset=len(binary);binary.extend(data)
        view={'buffer':0,'byteOffset':offset,'byteLength':len(data)}
        if target is not None:view['target']=target
        views.append(view);return len(views)-1
    p=add(struct.pack('<'+'f'*len(positions),*positions),34962)
    n=add(struct.pack('<'+'f'*len(normals),*normals),34962)
    t=add(struct.pack('<'+'f'*len(uv),*uv),34962)
    i=add(struct.pack('<'+'H'*len(indices),*indices),34963)
    image=add(png())
    document={
        'asset':{'version':'2.0','generator':'Loretune self-authored test fixture'},
        'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0,'name':'Textured cube'}],
        'meshes':[{'primitives':[{'attributes':{'POSITION':0,'NORMAL':1,'TEXCOORD_0':2},'indices':3,'material':0}]}],
        'accessors':[
            {'bufferView':p,'componentType':5126,'count':24,'type':'VEC3','min':[-1,-1,-1],'max':[1,1,1]},
            {'bufferView':n,'componentType':5126,'count':24,'type':'VEC3'},
            {'bufferView':t,'componentType':5126,'count':24,'type':'VEC2'},
            {'bufferView':i,'componentType':5123,'count':36,'type':'SCALAR'},
        ],
        'bufferViews':views,'buffers':[{'byteLength':len(binary)}],
        'images':[{'bufferView':image,'mimeType':'image/png'}],
        'textures':[{'source':0}],
        'materials':[{'pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicFactor':0,'roughnessFactor':0.65}}],
    }
    return pack_glb(document,binary)
