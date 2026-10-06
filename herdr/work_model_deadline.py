"""Finite primary SDK transport deadline; uncertainty retains its reservation."""
from contextlib import contextmanager
import signal
import threading
import time
from .security import PolicyDenied

@contextmanager
def model_deadline(milliseconds):
    if (type(milliseconds) is not int or not 1<=milliseconds<=900000
            or threading.current_thread() is not threading.main_thread()
            or signal.getitimer(signal.ITIMER_REAL)!=(0.0,0.0)):
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

def validate_text_request(payload,agent):
    """The basic quote covers one finite non-streaming text completion."""
    from .work_cycle import require
    require(isinstance(payload,dict) and agent.api_mode=="chat_completions"
            and payload.get("model")==agent.model and payload.get("n",1)==1
            and payload.get("stream",False) is False,
            "budgeted text route mismatch")
    allowed={"model","messages","tools","tool_choice","max_tokens","max_completion_tokens",
             "temperature","top_p","stop","presence_penalty","frequency_penalty","seed",
             "response_format","parallel_tool_calls","n","stream","timeout"}
    require(set(payload)<=allowed and isinstance(payload.get("messages"),list)
            and 1<=len(payload["messages"])<=1024,"unsupported budgeted request profile")
    for message in payload["messages"]:
        require(isinstance(message,dict) and isinstance(message.get("role"),str)
                and isinstance(message.get("content"),(str,type(None))),
                "multimodal content needs its own finite quote")
    outputs=[payload[key] for key in ("max_tokens","max_completion_tokens") if key in payload]
    require(len(outputs)==1 and type(outputs[0]) is int and outputs[0]>0,
            "explicit single output ceiling required")
