"""Retired benchmark-derived prototype. Runway is not a Loretune connection.
The prior unactivated prototype is preserved in
 docs/qa/benchmark-provider-correction-20261025/historical-inactive/.
No credential loading, endpoint or runtime transport remains here.
"""
class RunwayImage:
    def __init__(self,*args,**kwargs):
        raise ValueError('Runway는 벤치마크입니다. 공급자 연결 대상이 아닙니다.')
