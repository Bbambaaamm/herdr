"""Finite primary SDK transport deadline; uncertainty retains its reservation."""
from contextlib import contextmanager
import os
import signal
import threading
import time
from .security import PolicyDenied

@contextmanager
def _worker_deadline(milliseconds):
    # Interactive Hermes executes turns in a worker thread. A hard process
    # deadline cannot be swallowed by that thread's SDK/error handlers.
    lock=threading.Lock();finished=False
    deadline=time.monotonic()+milliseconds/1000
    def expired():
        with lock:
            if not finished:os._exit(124)
    timer=threading.Timer(max(0,deadline-time.monotonic()),expired)
    timer.daemon=True
    timer.start()
    try:
        yield
    finally:
        with lock:
            if time.monotonic()>=deadline:os._exit(124)
            finished=True
        timer.cancel()

@contextmanager
def model_deadline(milliseconds):
    if type(milliseconds) is not int or not 1<=milliseconds<=900000:
        raise PolicyDenied("budgeted_transport_deadline_unavailable")
    if threading.current_thread() is not threading.main_thread():
        with _worker_deadline(milliseconds):
            yield
        return
    if signal.getitimer(signal.ITIMER_REAL)!=(0.0,0.0):
        raise PolicyDenied("budgeted_transport_deadline_unavailable")
    previous=signal.getsignal(signal.SIGALRM)
    deadline=time.monotonic()+milliseconds/1000
    timed_out=False
    def expired(signum,frame):
        nonlocal timed_out
        timed_out=True
        signal.setitimer(signal.ITIMER_REAL,0.01)
        raise PolicyDenied("budgeted_transport_timeout_reconcile_original")
    signal.signal(signal.SIGALRM,expired)
    signal.setitimer(signal.ITIMER_REAL,milliseconds/1000)
    try:
        yield
        if timed_out or time.monotonic()>=deadline:
            raise PolicyDenied("budgeted_transport_timeout_reconcile_original")
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)

def _validate_nous_extensions(body,agent):
    """Only the pinned Nous SDK's bounded metadata and reasoning controls."""
    from .work_cycle import require
    require(getattr(agent,"provider",None)=="nous"
            and getattr(agent,"base_url",None)=="https://inference-api.nousresearch.com/v1",
            "unsupported Nous extension route")
    require(isinstance(body,dict) and set(body)<={"tags","session_id","reasoning"},
            "unsupported Nous extension fields")
    if "tags" in body:
        tags=body["tags"]
        require(isinstance(tags,list) and 1<=len(tags)<=8
                and all(isinstance(tag,str) and 1<=len(tag)<=256 for tag in tags),"bounded Nous tags required")
    if "session_id" in body:
        require(isinstance(body["session_id"],str) and 1<=len(body["session_id"])<=256,
                "bounded Nous session metadata required")
    if "reasoning" in body:
        reasoning=body["reasoning"]
        require(isinstance(reasoning,dict) and set(reasoning)<={"enabled","effort"},
                "unsupported Nous reasoning fields")
        if "enabled" in reasoning:require(type(reasoning["enabled"]) is bool,"boolean Nous reasoning flag required")
        if "effort" in reasoning:
            require(isinstance(reasoning["effort"],str)
                    and reasoning["effort"] in ("none","minimal","low","medium","high","xhigh","max"),
                    "bounded Nous reasoning effort required")

def validate_text_request(payload,agent):
    """One finite non-streaming text completion with closed Nous SDK metadata."""
    from .work_cycle import require
    require(isinstance(payload,dict) and agent.api_mode=="chat_completions"
            and payload.get("model")==agent.model and payload.get("n",1)==1
            and payload.get("stream",False) is False,
            "budgeted text route mismatch")
    allowed={"model","messages","tools","tool_choice","max_tokens","max_completion_tokens",
             "temperature","top_p","stop","presence_penalty","frequency_penalty","seed",
             "response_format","parallel_tool_calls","n","stream","timeout","extra_body"}
    require(set(payload)<=allowed and isinstance(payload.get("messages"),list)
            and 1<=len(payload["messages"])<=1024,"unsupported budgeted request profile")
    if "extra_body" in payload:_validate_nous_extensions(payload["extra_body"],agent)
    for message in payload["messages"]:
        require(isinstance(message,dict) and isinstance(message.get("role"),str)
                and isinstance(message.get("content"),(str,type(None))),
                "multimodal content needs its own finite quote")
    outputs=[payload[key] for key in ("max_tokens","max_completion_tokens") if key in payload]
    require(len(outputs)==1 and type(outputs[0]) is int and outputs[0]>0,
            "explicit single output ceiling required")
