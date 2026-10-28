"""Responses HTTP adapters. Disabled by default; no env reads, retries or redirects.
A trusted server supplies a verified token counter. No undocumented count endpoint
is invented and no credential is touched if the counter/connection is unavailable.
"""
import json
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import HTTPError
import chat_models

class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None

class ResponsesAdapter:
 def __init__(self,selection,credential_supplier=None,*,enabled=False,transport=None,counter=None):
  self.spec=chat_models.contract(selection)
  if self.spec['provider'] not in {'openai','xai'}:raise ValueError('Responses provider required')
  self.selection=selection;self.provider=self.spec['provider'];self.model=self.spec['model']
  self.supplier=credential_supplier;self.enabled=enabled;self.transport=transport;self.counter=counter
  self.mode='contract-fake' if transport is not None else self.provider+'-live'
 def count(self,body):
  if self.counter is None:raise ValueError('verified token counter unavailable; no submission')
  return self.counter(body)
 def complete(self,body):
  if body.get('model')!=self.model or body.get('store') is not False or body.get('stream',False) or body.get('background',False):raise ValueError('request contract mismatch')
  if self.transport is not None:
   return self.transport(self.spec['endpoint'],{'content-type':'application/json'},body)
  if not self.enabled or self.supplier is None or self.counter is None:raise ValueError('provider disabled')
  key=None;headers=None
  try:
   key=self.supplier(self.spec['environment'])
   if not isinstance(key,str) or not key or any(c in key for c in '\r\n'):raise ValueError()
   headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'}
   request=Request(self.spec['endpoint'],data=json.dumps(body).encode(),headers=headers,method='POST')
   with build_opener(NoRedirect()).open(request,timeout=60) as response:
    raw=response.read(100001)
    if len(raw)>100000:raise ValueError()
    result=json.loads(raw)
    if key in json.dumps(result):raise ValueError()
    result['_request_id']=response.headers.get('x-request-id') or response.headers.get('request-id')
    return result
  except HTTPError as exc:
   exc.close();raise ValueError('provider response unavailable; no retry') from None
  except Exception:raise ValueError('provider response unavailable; no retry') from None
  finally:key=None;headers=None
