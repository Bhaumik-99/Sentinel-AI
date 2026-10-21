import json
import urllib.request
from .config import settings
from .database import search_events, get_video

TOOLS = [{"type":"function","function":{"name":"search_events","description":"Retrieve stored object detections by class and optional video id.","parameters":{"type":"object","properties":{"label":{"type":"string"},"video_id":{"type":"integer"},"limit":{"type":"integer"}}}}},{"type":"function","function":{"name":"video_summary","description":"Retrieve metadata for a processed video.","parameters":{"type":"object","properties":{"video_id":{"type":"integer"}},"required":["video_id"]}}}]

def run_tool(name,args,scope=None):
    if name=="search_events":
        if scope is not None: args["video_id"]=scope
        rows=search_events(video_id=args.get("video_id"),label=args.get("label"),limit=max(1,min(int(args.get("limit",50)),100)))
        return {"events":[{"id":r["id"],"video_id":r["video_id"],"timestamp_seconds":r["timestamp_seconds"],"label":r["label"],"confidence":round(r["confidence"],3),"track_id":r["track_id"]} for r in rows]}
    if name=="video_summary":
        v=get_video(int(args["video_id"]))
        return {k:v[k] for k in ("id","filename","duration_seconds","fps","frame_count","processed_frames")} if v else {"error":"Video not found"}
    return {"error":"Unknown tool"}

def ask_agent(question, video_id=None):
    if not question.strip(): return {"answer":"Please enter a question.","evidence":[],"agent_enabled":False}
    messages=[{"role":"system","content":"You are Sentinel, a video evidence assistant. Use tools to retrieve detections. Do not claim you inspected raw video. A missing detection does not prove absence. Cite timestamps and distinguish detections from certainty."},{"role":"user","content":"Video scope: %s. Question: %s"%(video_id if video_id is not None else "all videos",question)}]
    evidence=[]
    for _ in range(4):
        payload={"model":settings.llm_model,"messages":messages,"tools":TOOLS,"stream":False}
        req=urllib.request.Request(settings.llm_base_url.rstrip("/")+"/api/chat",data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
        try:
            with urllib.request.urlopen(req,timeout=settings.llm_timeout_seconds) as resp: data=json.loads(resp.read().decode())
        except Exception as exc:
            return {"answer":"Local model is not available (%s). Start Ollama and run: ollama pull %s"%(type(exc).__name__,settings.llm_model),"evidence":evidence,"agent_enabled":False,"setup_hint":"ollama pull %s"%settings.llm_model}
        msg=data.get("message",{}); calls=msg.get("tool_calls",[])
        if not calls:
            return {"answer":msg.get("content","No answer returned."),"evidence":evidence,"agent_enabled":True,"model":settings.llm_model}
        messages.append(msg)
        for call in calls:
            fn=call.get("function",{}); name=fn.get("name",""); args=fn.get("arguments",{})
            if not isinstance(args,dict): args={}
            result=run_tool(name,args,video_id)
            if name=="search_events": evidence.extend(result.get("events",[]))
            messages.append({"role":"tool","tool_name":name,"content":json.dumps(result)})
    return {"answer":"The agent reached its tool-call limit. Please narrow the question.","evidence":evidence[:30],"agent_enabled":True,"model":settings.llm_model}
