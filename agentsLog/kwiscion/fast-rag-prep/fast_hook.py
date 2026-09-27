"""Only auxiliary generation budgets differ from reviewed filtered RAG V2."""
import study_hook_v2 as v2

QUERY_CAP=512
JUDGE_CAP=384
RETRY_CAP=1024

class Hook(v2.Hook):
 def step(self,case,attempt,history,c,route=None):
  body,settings=super().step(case,attempt,history,c,route)
  kind=self.current['kind']
  if kind in ('query','judge'):
   cap=RETRY_CAP if attempt else QUERY_CAP if kind=='query' else JUDGE_CAP
   body['think']=False;body['options']['num_predict']=cap
   settings.update(think=False,cap=cap,name='auxiliary_fast' if attempt==0 else 'auxiliary_fast_retry',escalation_note=None)
  return body,settings

def install(root,engine):
 hook=Hook(root,engine)
 engine.step=hook.step;engine.accepted=hook.accepted;engine.usable_partial=hook.partial;engine.stage_barrier=hook.barrier
 return hook
