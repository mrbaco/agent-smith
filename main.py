from typing import Optional
from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    BackgroundTasks,
    HTTPException,
    Header,
    Request,
    Response,
    status
)

import subprocess
import requests
import hashlib
import hmac
import json
import os

load_dotenv('.env')

app = FastAPI()

def run_script():
    try:
        result = subprocess.run(
            [os.getenv('SCRIPT_PATH')],
            capture_output=True,
            shell=True,
            text=True,
            env=os.environ.copy(),
            timeout=60
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail='Error in script execution'
            )

        requests.get(os.getenv('SUCCEED_WEBHOOK_URL'))

    except Exception:
        requests.get(os.getenv('FAILED_WEBHOOK_URL'))

@app.post("/", status_code=status.HTTP_204_NO_CONTENT)
async def main(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: Optional[str] = Header(None),
    x_github_event: Optional[str] = Header(None)
):
    if not x_hub_signature_256:
        raise HTTPException(
            status_code=403,
            detail='x-hub-signature-256 header is missing'
        )

    body = await request.body()

    hash_object = hmac.new(
        os.getenv('TOKEN').encode(),
        msg=body,
        digestmod=hashlib.sha256
    )
    expected_signature = 'sha256=' + hash_object.hexdigest()

    if not hmac.compare_digest(expected_signature, x_hub_signature_256):
        raise HTTPException(
            status_code=403,
            detail='Request signatures didn\'t match'
        )

    if x_github_event != 'pull_request':
        raise HTTPException(
            status_code=403,
            detail='Only "pull_request" events allowed'
        )

    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail='Invalid JSON in request body'
        )

    if body.get('action', None) != 'closed':
        return

    pull_request = body.get('pull_request', { })

    if pull_request.get('merged_at', None) is None:
        return

    if not pull_request.get('base', { }).get('ref', None) in ['main', 'master']:
        return

    if not os.access(os.getenv('SCRIPT_PATH'), os.X_OK):
        raise HTTPException(
            status_code=500,
            detail='Script is not executable'
        )

    background_tasks.add_task(run_script)

    return Response(status_code=status.HTTP_202_ACCEPTED)
