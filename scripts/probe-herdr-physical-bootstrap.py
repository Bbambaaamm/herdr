#!/usr/bin/env python3
"""Exercise the complete physical bootstrap with installed Hermes, without a provider.

This is an explicit operator probe. It freezes host-approved source bytes into
private copies, runs only Hermes --version in an owned sandbox, persists and
physically verifies the continuation before allowing its acknowledgement.
It does not change a live service, credential, profile or release.
"""
from __future__ import annotations
import argparse,shutil,hashlib,importlib.machinery,importlib.util,json,os,shlex,stat,subprocess,sys,tempfile,time,uuid
from dataclasses import replace
from pathlib import Path

def inventory(source, *, max_bytes, max_file):
    files={};executable=[];total=0
    for directory,dirs,names in os.walk(source,followlinks=False):
        dirs[:]=sorted(name for name in dirs if name not in {"__pycache__","node_modules"}
                       and not (Path(directory)/name).is_symlink())
        for name in sorted(names):
            path=Path(directory)/name
            info=path.lstat()
            if not stat.S_ISREG(info.st_mode): continue
            if info.st_size>max_file: raise ValueError("runtime file exceeds approved bound")
            total+=info.st_size
            if total>max_bytes or len(files)>=65536: raise ValueError("runtime inventory exceeds bound")
            relative=path.relative_to(source).as_posix()
            files[relative]=hashlib.sha256(path.read_bytes()).hexdigest()
            if info.st_mode&0o111: executable.append(relative)
    return files,tuple(executable)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo-root",default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--tamper-stdlib",action="store_true")
    parser.add_argument("--deny-continuation",action="store_true")
    parser.add_argument("--tamper-runtime-library",action="store_true")
    parser.add_argument("--poison-loader",action="store_true")
    parser.add_argument("--stale-fence",action="store_true")
    ns=parser.parse_args()
    repo=Path(ns.repo_root).resolve()
    sys.path.insert(0,str(repo))
    from herdr.policy_launch import (ApprovedTree,HostPolicyLaunchFactory,CODE_TARGET,
        RUNTIME_TARGETS,verify_retained_policy_evidence)
    from herdr.security import (InvocationIdentity,NetworkAccess,ProcessPolicy,RiskClass,
        RuntimeAssurance,SecurityGrant,ToolRule,canonical_json_bytes)
    from herdr.capability import CapabilityScope,DataClass,Egress,Retention,Training
    loader=importlib.machinery.SourceFileLoader("herdr_physical_launcher_probe",
        str(repo/"agent-stack/bin/agent-hermes-policy-run"))
    spec=importlib.util.spec_from_loader(loader.name,loader)
    launcher=importlib.util.module_from_spec(spec);loader.exec_module(launcher)
    loader=importlib.machinery.SourceFileLoader("herdr_physical_sandbox_probe",
        str(repo/"agent-stack/bin/agent_durable_sandbox.py"))
    spec=importlib.util.spec_from_loader(loader.name,loader)
    sandbox=importlib.util.module_from_spec(spec);sys.modules[spec.name]=sandbox;loader.exec_module(sandbox)
    manifest={}
    names=set(subprocess.check_output(["git","-C",str(repo),"ls-files","-z"]).split(b"\0"))
    for line in (repo/"provenance/CANONICAL_SOURCE_MANIFEST.sha256").read_text().splitlines():
        name=line.split("  ",1)[1]
        if Path(name).is_absolute() or ".." in Path(name).parts: raise ValueError("invalid manifest source")
        names.add(name.encode())
    for name in names:
        if name:
            name=name.decode();path=repo/name
            if stat.S_ISREG(path.lstat().st_mode): manifest[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    code=ApprovedTree(repo,CODE_TARGET,manifest,
                      tuple(name for name in manifest if (repo/name).stat().st_mode&0o111),
                      max_bytes=64*1024*1024,max_file_bytes=8*1024*1024)
    runtime=[]
    for target in sorted(RUNTIME_TARGETS):
        files,executable=inventory(target,max_bytes=1024*1024*1024,max_file=128*1024*1024)
        runtime.append(ApprovedTree(target,target,files,executable,
                                   max_bytes=1024*1024*1024,max_file_bytes=128*1024*1024))
    with tempfile.TemporaryDirectory(prefix="herdr-physical-bootstrap-",dir="/home/agentops/tmp") as temp:
        host=Path(temp);storage=host/"authority";storage.mkdir(mode=0o700)
        workspace=host/"worktrees"/"workspace";workspace.mkdir(parents=True)
        config=host/"config";config.mkdir();releases=host/"releases";releases.mkdir()
        sandbox.HERDR_CONFIG=config;sandbox.HERDR_RELEASES=releases;sandbox.DEFAULT_WRITABLE=()
        cli=host/"herdr";cli.write_text("#!/bin/sh\nexit 0\n");cli.chmod(0o755)
        policy=host/"cli-policy";policy.write_text("#!/bin/sh\nexit 2\n");policy.chmod(0o555)
        result=host/"results"/"probe.result.json";result.parent.mkdir();result.touch()
        identity=InvocationIdentity("github:Bbambaaamm/herdr","physical-probe-agent","physical-parent",
            "physical-parent-task","physical-probe-task","physical-"+uuid.uuid4().hex,1)
        scope=CapabilityScope(providers=(),capabilities=("tool_use",),executors=(launcher.HERMES_EXECUTOR,),
            tools=("read_file",),permissions=("repo:read",),regions=("eu-central",),
            data_classes=(DataClass.INTERNAL,),input_modalities=("text",),output_modalities=("text",),
            max_cost_microusd=0,max_context_tokens=8192,max_egress=Egress.NONE,
            max_retention=Retention.ZERO,training=Training.EXCLUDED)
        grant=SecurityGrant(workspace_root=str(workspace),grant_id="physical-bootstrap-probe",
            identity=identity,scope=scope,tool_rules=(ToolRule("read_file",RiskClass.READ,
              ("path","offset","limit"),("path",),(str(workspace),)),),
            process=ProcessPolicy(False,(),NetworkAccess.NONE),runtime_assurance=RuntimeAssurance(
              False,None,NetworkAccess.NONE,(),False),provider_routes=(),credential_refs=(),
            approvals=(),approval_required_for=(),issued_at="2026-01-01T00:00:00+00:00",
            expires_at="2030-01-01T00:00:00+00:00")
        if ns.tamper_stdlib or ns.tamper_runtime_library:
            # Change only a private source copy and approve its changed snapshot
            # hash. The audit-known independent stdlib pin must still reject it.
            changed=host/"tampered-python";changed.mkdir()
            python=next(definition for definition in runtime if definition.target==launcher.PYTHON_ROOT)
            for name in python.files:
                destination=changed/name;destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(python.source/name,destination)
            relative=("lib/python3.11/encodings/__init__.py" if ns.tamper_stdlib
                      else "lib/libpython3.11.so.1.0")
            entry=changed/relative
            entry.write_bytes(entry.read_bytes()+bytes([10])+b"HERDR_PRIVATE_RUNTIME_CORRUPTION"+bytes([10]))
            files=dict(python.files);files[relative]=hashlib.sha256(entry.read_bytes()).hexdigest()
            runtime=[replace(definition,source=changed,files=files) if definition is python else definition
                     for definition in runtime]
        factory=HostPolicyLaunchFactory(code=code,runtime=tuple(runtime),storage=storage,
                                       authorize=lambda **kw:grant)
        launch=factory.prepare(identity=identity,workspace=workspace,tools=scope.tools,
                               permissions=scope.permissions)
        fd=os.open(workspace,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        info=os.fstat(fd);pin=sandbox.PinnedWorktree(workspace,fd,info.st_dev,info.st_ino,workspace.parent)
        marker="physical-"+uuid.uuid4().hex
        env={**os.environ,**launch.environment(),"HERDR_DURABLE_TASK_PANE":marker,
             "HERMES_HOME":"/tmp/herdr-isolated-home"}
        poison_marker=host/"results"/"native-constructor-executed"
        if ns.poison_loader:
            source=host/"loader-poison.c";library=host/"loader-poison.so"
            source.write_text('#include <stdio.h>\n__attribute__((constructor)) static void run(void){FILE *f=fopen('+
                              json.dumps(str(poison_marker))+',"w");if(f){fputs("executed",f);fclose(f);}}\n')
            subprocess.run(["/usr/bin/cc","-shared","-fPIC",str(source),"-o",str(library)],
                           check=True,capture_output=True,timeout=10)
            env.update(LD_PRELOAD=str(library),LD_AUDIT=str(library),
                       LD_LIBRARY_PATH=str(host),LD_TRACE_LOADED_OBJECTS="1",GLIBC_TUNABLES="unsafe")
        from herdr.launch_environment import sanitize_environment,require_clean_environment
        env=sanitize_environment(env);require_clean_environment(env)
        args=sandbox.command(workspace,cli,writable=(result,),policy=policy,
             child_workspace_writable=False,pinned_worktree=pin,policy_mount=launch.mount)
        process=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,
                                 stderr=subprocess.PIPE,env=env)
        try:
            pid=None
            for _ in range(150):
                if process.poll() is not None: raise RuntimeError(process.stderr.read(8192).decode())
                rows=[]
                for proc in Path("/proc").iterdir():
                    if not proc.name.isdigit(): continue
                    try:
                        with (proc/"environ").open("rb") as stream: raw=stream.read(262145)
                        if ("HERDR_DURABLE_TASK_PANE="+marker).encode() in raw.split(b"\0"):
                            rows.append({"pid":int(proc.name)})
                    except OSError: pass
                pid=sandbox.inner_pid({"foreground_processes":rows},marker)
                if pid: break
                time.sleep(.02)
            if not pid: raise RuntimeError("owned sandbox shell unavailable")
            if not sandbox.verify(pid,cli,marker,policy=policy,pinned_worktree=pin,
                                  child_workspace_writable=False,policy_mount=launch.mount):
                raise RuntimeError("physical sandbox not verified")
            attestation={"authority":"herdr-runtime","task_id":identity.task_id,
                "run_token":identity.run_token,"sandbox_pid":pid}
            launch.seal(pid,attestation,tools=scope.tools,permissions=scope.permissions)
            observations=[]
            durable=host/"continuation.json"
            def publish(proof):
                # This function runs while the stage-two process is blocked on ACK,
                # so the independent verifier observes the actual retained process.
                verify_retained_policy_evidence(proof,identity=identity,pid=pid,attestation=attestation)
                if ns.deny_continuation: return False
                with durable.open("xb") as stream:
                    stream.write(canonical_json_bytes(proof));stream.flush();os.fsync(stream.fileno())
                directory=os.open(host,os.O_RDONLY|os.O_DIRECTORY)
                try: os.fsync(directory)
                finally: os.close(directory)
                observations.append(proof)
                return True
            launch.set_continuation_sink(publish);launch.arm_bootstrap()
            script=("export HERDR_POLICY_FENCING_TOKEN=2; " if ns.stale_fence else "")
            script+="mkdir -p /tmp/herdr-isolated-home; hermes --version > "+shlex.quote(str(result))+" 2>&1\n"
            process.stdin.write(script.encode());process.stdin.flush()
            output=None
            denial=ns.tamper_stdlib or ns.tamper_runtime_library or ns.deny_continuation or ns.stale_fence
            expected=("before interpreter exec" if ns.tamper_stdlib or ns.tamper_runtime_library
                      else "identity mismatch" if ns.stale_fence else "authority")
            for _ in range(400):
                output=result.read_text() if result.stat().st_size else None
                if output and ((denial and expected in output) or (not denial and observations and "0.21.5" in output)):
                    break
                if process.poll() is not None: raise RuntimeError(process.stderr.read(8192).decode())
                time.sleep(.05)
            if denial:
                if (output is None or expected not in output or "HERDR_CORRUPT_STDLIB_EXECUTED" in output
                        or "0.21.5" in output or observations or durable.exists()
                        or launch._published_bootstrap_receipt is not None):
                    raise RuntimeError("invalid bootstrap denial evidence: "+str(output)[:4096])
                print(json.dumps({"status":"PASS","denied_before_hermes":True,
                    "case":("tampered_stdlib" if ns.tamper_stdlib else
                            "tampered_runtime_library" if ns.tamper_runtime_library else
                            "stale_fence" if ns.stale_fence else "durable_sink_denied"),
                    "live_provider_used":False,"live_config_changed":False},sort_keys=True))
                return 0
            if not observations or output is None or "0.21.5" not in output:
                raise RuntimeError("physical continuation/version probe failed: "+result.read_text()[:4096])
            if poison_marker.exists(): raise RuntimeError("native loader code executed before sanitization")
            receipt=launch._published_bootstrap_receipt
            if receipt is None or json.loads(durable.read_bytes())!=observations[0]:
                raise RuntimeError("durable continuation did not precede Hermes startup")
            print(json.dumps({"status":"PASS","physical_bootstrap":True,"socket_fd_bind":True,
                "schema_version":observations[0]["schema_version"],
                "pre_ack_physical_verification":True,"durable_receipt":True,
                "same_process_pinned_interpreter":True,"native_loader_controls_removed":True,
                "poison_loader":ns.poison_loader,"live_provider_used":False,
                "live_config_changed":False},sort_keys=True))
        finally:
            if process is not None:
                process.stdin.close()
                try: process.wait(timeout=3)
                except subprocess.TimeoutExpired: process.kill();process.wait(timeout=3)
            pin.close();launch.cleanup_after_pane_closed()
    return 0

if __name__=="__main__": raise SystemExit(main())
