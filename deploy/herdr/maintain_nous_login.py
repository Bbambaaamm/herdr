"""Maintain the original Nous login through its official SDK, outside worker admission.

The operator runs this as the login owner. It never receives a copied refresh
credential, changes a model budget, or prints credential bytes.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import time

SDK = Path('/opt/herdr/releases/p0-5035d92-test/hermes')


def expires(token):
    try:
        part=token.split('.')[1]
        return int(json.loads(base64.urlsafe_b64decode(part+'='*((-len(part))%4)))['exp'])
    except (AttributeError,IndexError,ValueError,TypeError,KeyError):
        return 0


def maintain(auth, required_seconds, *, now=time.time):
    if type(required_seconds) is not int or required_seconds<=0:
        raise ValueError('invalid_required_credential_lifetime')
    state=auth.get_provider_auth_state('nous') or {}
    current=state.get('agent_key') or state.get('access_token')
    refresh_required=expires(current)-now()<required_seconds
    # One official locked resolver call; no extra retry on invalid_grant or timeout.
    creds=auth.resolve_nous_runtime_credentials(timeout_seconds=25,force_refresh=refresh_required,
                                               stale_access_token=current if refresh_required else None)
    if creds.get('provider')!='nous' or creds.get('base_url','').rstrip('/')!='https://inference-api.nousresearch.com/v1':
        raise RuntimeError('official_inference_route_changed')
    remaining=expires(creds.get('api_key'))-now()
    return {'credential_ready':remaining>=required_seconds,'required_validity_seconds':required_seconds,
            'remaining_validity_seconds':max(0,int(remaining)), 'official_resolver_calls':1,
            'standard_renewal_requested':refresh_required,'model_calls':0,'credentials_exported':False}


def main():
    import sys
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--required-validity-seconds',required=True,type=int)
    args=parser.parse_args()
    if os.geteuid()!=1001 or os.environ.get('HOME')!='/home/agentops' or os.environ.get('HERMES_HOME')!='/home/agentops/.hermes/profiles/quantlab':
        raise SystemExit('original_login_owner_and_profile_required')
    sys.path[:0]=[str(SDK),str(SDK/'venv/lib/python3.11/site-packages')]
    from hermes_cli import auth
    try:
        result=maintain(auth,args.required_validity_seconds)
        print(json.dumps(result,sort_keys=True))
        return 0 if result['credential_ready'] else 2
    except BaseException as error:
        print(json.dumps({'credential_ready':False,'error_type':type(error).__name__,
                          'reason_code':'official_login_maintenance_stopped','automatic_retry_allowed':False,
                          'model_calls':0,'credentials_exported':False}))
        return 1


if __name__=='__main__':raise SystemExit(main())
