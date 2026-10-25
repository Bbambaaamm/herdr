"""Current authenticated Codex summary protocol at the real collector seam."""
from copy import deepcopy
import hashlib,json
import pytest
import agent_completion_evidence as collector
from herdr.evidence import EvidenceError,digest
from test_completion_collector import proof_fixture,install_transport

HEADER="<!-- codex-pull-request-review-summary -->\n<!-- codex-review-state:v1 "
def summary_row(head):
    state={"code_review":{"commit_sha":head,"has_any_findings":False,
        "has_unresolved_findings":False,"status":"completed"},
        "security_review":{"commit_sha":None,"has_any_findings":None,
        "has_unresolved_findings":None,"status":None}}
    row={"id":7,"user":{"login":collector.BOT,"type":"Bot"},
        "created_at":"2026-10-03T19:00:00Z","updated_at":"2026-10-03T22:00:00Z"}
    return row,state
def with_state(row,state,reviewed_at=None):
    row=deepcopy(row)
    when=reviewed_at or row["updated_at"]
    row["body"]=(HEADER+json.dumps(state)+" -->\n\n## Codex Review Summary\n"
        "| 📝 **Code Review** | ✅ **Completed** <relative-time datetime="+chr(34)+when+chr(34)+">"+when+"</relative-time> | "+chr(96)+str(state["code_review"]["commit_sha"])[:7]+chr(96)+" | Draft marked ready |\n")
    return row
def install_snapshots(monkeypatch,artifact,plan,pr,checks,first,second=None,reviews=()):
    install_transport(monkeypatch,artifact,plan,pr,checks,first[0],reviews=reviews)
    original=collector.github
    calls=[0]
    def api(path):
        if "/issues/" in path:
            calls[0]+=1
            return deepcopy(first if calls[0]==1 or second is None else second)
        return deepcopy(original(path))
    monkeypatch.setattr(collector,"github",api)

def test_current_summary_collects_exact_commit_and_preserves_raw_digest(monkeypatch):
    artifact,plan,pr,checks,_=proof_fixture()
    row,state=summary_row(artifact.commit_sha);row=with_state(row,state)
    install_snapshots(monkeypatch,artifact,plan,pr,checks,[row])
    proof=collector.collect_github(plan,artifact,4)
    assert proof["review"]["comment_id"]==row["id"]
    assert proof["review"]["commit_sha"]==artifact.commit_sha
    assert proof["review"]["body_digest"]==digest(row["body"])

def test_current_summary_edit_time_supersedes_earlier_same_commit_review(monkeypatch):
    artifact,plan,pr,checks,_=proof_fixture()
    row,state=summary_row(artifact.commit_sha);row=with_state(row,state)
    reviews=[{"id":1,"commit_id":artifact.commit_sha,"user":{"login":collector.BOT},
        "submitted_at":"2026-10-03T21:00:00Z","state":"COMMENTED"}]
    install_snapshots(monkeypatch,artifact,plan,pr,checks,[row],reviews=reviews)
    assert collector.collect_github(plan,artifact,4)["review"]["commit_sha"]==artifact.commit_sha

def test_current_summary_newer_same_commit_findings_still_block(monkeypatch):
    artifact,plan,pr,checks,_=proof_fixture()
    row,state=summary_row(artifact.commit_sha);row=with_state(row,state)
    reviews=[{"id":1,"commit_id":artifact.commit_sha,"user":{"login":collector.BOT},
        "submitted_at":"2026-10-03T23:00:00Z","state":"COMMENTED"}]
    install_snapshots(monkeypatch,artifact,plan,pr,checks,[row],reviews=reviews)
    with pytest.raises(EvidenceError):collector.collect_github(plan,artifact,4)

@pytest.mark.parametrize("status",[None,"pending","in_progress","failed","cancelled"])
def test_current_summary_incomplete_or_failed_status_denied(monkeypatch,status):
    artifact,plan,pr,checks,_=proof_fixture()
    row,state=summary_row(artifact.commit_sha);state["code_review"]["status"]=status
    install_snapshots(monkeypatch,artifact,plan,pr,checks,[with_state(row,state)])
    with pytest.raises(EvidenceError):collector.collect_github(plan,artifact,4)

@pytest.mark.parametrize("field",["has_any_findings","has_unresolved_findings"])
@pytest.mark.parametrize("value",[True,None,0,"false"])
def test_current_summary_flags_are_strict_clean_booleans(monkeypatch,field,value):
    artifact,plan,pr,checks,_=proof_fixture()
    row,state=summary_row(artifact.commit_sha);state["code_review"][field]=value
    install_snapshots(monkeypatch,artifact,plan,pr,checks,[with_state(row,state)])
    with pytest.raises(EvidenceError):collector.collect_github(plan,artifact,4)

@pytest.mark.parametrize("head",[None,"a"*10,"d"*40])
def test_current_summary_missing_short_or_other_commit_denied(monkeypatch,head):
    artifact,plan,pr,checks,_=proof_fixture()
    row,state=summary_row(head)
    install_snapshots(monkeypatch,artifact,plan,pr,checks,[with_state(row,state)])
    with pytest.raises(EvidenceError):collector.collect_github(plan,artifact,4)

def test_current_summary_clean_requested_security_review_supported(monkeypatch):
    artifact,plan,pr,checks,_=proof_fixture()
    row,state=summary_row(artifact.commit_sha)
    state["security_review"]=deepcopy(state["code_review"])
    install_snapshots(monkeypatch,artifact,plan,pr,checks,[with_state(row,state)])
    assert collector.collect_github(plan,artifact,4)["review"]["comment_id"]==row["id"]

@pytest.mark.parametrize("fault",["pending","findings","other_commit","partial"])
def test_current_summary_requested_security_review_must_also_pass(monkeypatch,fault):
    artifact,plan,pr,checks,_=proof_fixture()
    row,state=summary_row(artifact.commit_sha)
    state["security_review"]=deepcopy(state["code_review"])
    if fault=="pending":state["security_review"]["status"]="in_progress"
    elif fault=="findings":state["security_review"]["has_any_findings"]=True
    elif fault=="other_commit":state["security_review"]["commit_sha"]="d"*40
    else:state["security_review"]["status"]=None
    install_snapshots(monkeypatch,artifact,plan,pr,checks,[with_state(row,state)])
    with pytest.raises(EvidenceError):collector.collect_github(plan,artifact,4)

@pytest.mark.parametrize("fault",["version","duplicate","unknown","malformed","extra_marker"])
def test_current_summary_invalid_protocol_cannot_supply_review(monkeypatch,fault):
    artifact,plan,pr,checks,_=proof_fixture()
    row,state=summary_row(artifact.commit_sha)
    if fault=="unknown":state["unapproved_extension"]={}
    row=with_state(row,state)
    if fault=="version":row["body"]=row["body"].replace("state:v1 ","state:v2 ",1)
    elif fault=="duplicate":row["body"]=row["body"].replace('"has_any_findings": false','"has_any_findings": true, "has_any_findings": false',1)
    elif fault=="malformed":row["body"]=HEADER+"not-json -->\n"
    elif fault=="extra_marker":row["body"]+=HEADER+"{} -->\n"
    install_snapshots(monkeypatch,artifact,plan,pr,checks,[row])
    with pytest.raises(EvidenceError):collector.collect_github(plan,artifact,4)

@pytest.mark.parametrize("fault",["actor","type"])
def test_current_summary_needs_authenticated_bot_identity(monkeypatch,fault):
    artifact,plan,pr,checks,_=proof_fixture()
    row,state=summary_row(artifact.commit_sha);row=with_state(row,state)
    if fault=="actor":row["user"]["login"]="worker"
    else:row["user"]["type"]="User"
    install_snapshots(monkeypatch,artifact,plan,pr,checks,[row])
    with pytest.raises(EvidenceError):collector.collect_github(plan,artifact,4)

def test_current_summary_pending_state_blocks_legacy_clean_receipt(monkeypatch):
    artifact,plan,pr,checks,legacy=proof_fixture()
    row,state=summary_row(artifact.commit_sha);state["code_review"]["status"]="in_progress"
    install_snapshots(monkeypatch,artifact,plan,pr,checks,[legacy,with_state(row,state)])
    with pytest.raises(EvidenceError):collector.collect_github(plan,artifact,4)

@pytest.mark.parametrize("fault",["pending","removed","other_commit"])
def test_current_summary_changes_block_even_if_newer_legacy_selected(monkeypatch,fault):
    artifact,plan,pr,checks,legacy=proof_fixture()
    legacy["created_at"]="2026-10-03T23:00:00Z"
    row,state=summary_row(artifact.commit_sha);first=[with_state(row,state),legacy]
    if fault=="removed":second=[legacy]
    else:
        row["updated_at"]="2026-10-04T00:00:00Z"
        if fault=="pending":state["code_review"]["status"]="in_progress"
        else:state["code_review"]["commit_sha"]="d"*40
        second=[with_state(row,state),legacy]
    install_snapshots(monkeypatch,artifact,plan,pr,checks,first,second)
    with pytest.raises(EvidenceError):collector.collect_github(plan,artifact,4)

def test_current_summary_newest_edit_not_largest_comment_id_is_selected(monkeypatch):
    artifact,plan,pr,checks,legacy=proof_fixture()
    row,state=summary_row(artifact.commit_sha);row=with_state(row,state)
    install_snapshots(monkeypatch,artifact,plan,pr,checks,[legacy,row])
    assert collector.collect_github(plan,artifact,4)["review"]["comment_id"]==row["id"]

def test_approved_branch_collects_exact_selected_branch(monkeypatch):
    artifact,plan,pr,checks,comment=proof_fixture()
    plan["base_branch"]="review/approved";pr["base"]["ref"]="review/approved"
    install_transport(monkeypatch,artifact,plan,pr,checks,comment)
    assert collector.collect_github(plan,artifact,4)["review"]["commit_sha"]==artifact.commit_sha

@pytest.mark.parametrize("actual",["main","review/other"])
def test_approved_branch_same_commit_wrong_branch_denied(monkeypatch,actual):
    artifact,plan,pr,checks,comment=proof_fixture()
    plan["base_branch"]="review/approved";pr["base"]["ref"]=actual
    install_transport(monkeypatch,artifact,plan,pr,checks,comment)
    with pytest.raises(EvidenceError):collector.collect_github(plan,artifact,4)

def test_approved_branch_legacy_plan_still_requires_main(monkeypatch):
    artifact,plan,pr,checks,comment=proof_fixture()
    pr["base"]["ref"]="review/approved"
    install_transport(monkeypatch,artifact,plan,pr,checks,comment)
    with pytest.raises(EvidenceError):collector.collect_github(plan,artifact,4)

def test_current_summary_security_edit_does_not_refresh_older_code_review(monkeypatch):
    artifact,plan,pr,checks,_=proof_fixture()
    row,state=summary_row(artifact.commit_sha)
    row["updated_at"]="2026-10-03T23:00:00Z"
    row=with_state(row,state,reviewed_at="2026-10-03T20:00:00Z")
    reviews=[{"id":1,"commit_id":artifact.commit_sha,"user":{"login":collector.BOT},
        "submitted_at":"2026-10-03T21:00:00Z","state":"COMMENTED"}]
    install_snapshots(monkeypatch,artifact,plan,pr,checks,[row],reviews=reviews)
    with pytest.raises(EvidenceError):collector.collect_github(plan,artifact,4)

def test_current_summary_legacy_edits_do_not_refresh_review_freshness(monkeypatch):
    artifact,plan,pr,checks,legacy=proof_fixture()
    legacy["updated_at"]="2026-10-03T23:00:00Z"
    reviews=[{"id":1,"commit_id":artifact.commit_sha,"user":{"login":collector.BOT},
        "submitted_at":"2026-10-03T21:00:00Z","state":"COMMENTED"}]
    install_snapshots(monkeypatch,artifact,plan,pr,checks,[legacy],reviews=reviews)
    with pytest.raises(EvidenceError):collector.collect_github(plan,artifact,4)

@pytest.mark.parametrize("selected,actual,duplicate,accepted", [
    (None,"main",False,True),
    ("review/approved","review/approved",False,True),
    ("review/approved","main",False,False),
    (None,"review/approved",False,False),
    ("review/approved","review/approved",True,False),
])
def test_local_host_handoff_discovers_only_the_approved_base(monkeypatch,selected,actual,duplicate,accepted):
    artifact,plan,pr,checks,comment=proof_fixture()
    if selected is not None:plan["base_branch"]=selected
    pr["base"]["ref"]=actual;pr["number"]=4
    install_transport(monkeypatch,artifact,plan,pr,checks,comment)
    original=collector.github
    def api(path):
        if path==f"repos/{plan['repo']}/commits/{artifact.commit_sha}/pulls?per_page=100":
            return [deepcopy(pr),deepcopy(pr)] if duplicate else [deepcopy(pr)]
        return deepcopy(original(path))
    monkeypatch.setattr(collector,"github",api)
    if accepted:
        assert collector.collect_local_handoff(plan,artifact,None)["review"]["commit_sha"]==artifact.commit_sha
    else:
        with pytest.raises(EvidenceError):collector.collect_local_handoff(plan,artifact,None)
