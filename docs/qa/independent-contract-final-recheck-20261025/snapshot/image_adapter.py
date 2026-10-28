"""Explicit synthetic image adapter for offline pipeline tests; not an AI model."""
import hashlib,struct,zlib
class SyntheticImageAdapter:
 mode='fake';external_calls=0
 def generate(self,request):
  if not isinstance(request,dict) or set(request)!={'prompt','width','height'}:raise ValueError('지원하지 않는 이미지 입력')
  if not isinstance(request['prompt'],str) or not 1<=len(request['prompt'])<=2000:raise ValueError('프롬프트 길이 오류')
  w,h=request['width'],request['height']
  if any(type(v) is not int or not 32<=v<=256 for v in [w,h]):raise ValueError('fixture 크기 범위 오류')
  def chunk(kind,data):return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
  raw=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+bytes([30,70,140])*w)*h))+chunk(b'IEND',b'')
  return dict(bytes=raw,sha256=hashlib.sha256(raw).hexdigest(),mime='image/png',provenance='synthetic-solid-color-fixture; not AI',external_calls=0)
