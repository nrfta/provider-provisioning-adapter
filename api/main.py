import asyncio
import logging
import subprocess
import traceback
from asyncio.subprocess import PIPE, create_subprocess_exec
from functools import partial
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Literal, Callable

import httpx
import httpsig
from fastapi import FastAPI, Depends, Response, Request, status

from .config import Settings, get_settings
from .model import ServiceRequest, CallbackUrls


class SmallTraceFmt(logging.Formatter):
    def formatException(self, exc_info) -> str:
        """
        Override default format of logging.exception() messages. Only print the last stack item
        :param exc_info:
        :return: exception stack ås string
        """
        exc_type, exc_val, exc_traceback = exc_info
        trace = traceback.format_exception(exc_type,
                                           value=exc_val,
                                           tb=exc_traceback,
                                           limit=1, chain=False)
        trace[-1] = trace[-1].rstrip()  # Remove trailing newline
        return ''.join(trace)


logger = logging.getLogger('SONAR_INTEGRATION')
logger.setLevel(logging.WARNING)
ch = RotatingFileHandler(filename="logs-test.txt", backupCount=3, maxBytes=2_097_152)  # maxBytes==2MiBs
ch.setLevel(logging.WARNING)
formatter = SmallTraceFmt("[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

scripts = {
    "provision": "ppa_service_create",
    "replace": "ppa_service_modify",
    "unprovision": "ppa_service_remove"
}
background_tasks = set()
app = FastAPI()


async def run(script: Path, data: str, timeout: int) -> Literal["success", "error"]:
    try:
        process = await create_subprocess_exec(f'{script}', f"{data}", stdout=PIPE, stdin=PIPE, stderr=PIPE)
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        logger.info(stdout.decode())
        if stderr or process.returncode != 0:
            raise subprocess.SubprocessError(stderr.decode())
    except (asyncio.TimeoutError, subprocess.SubprocessError):
        logger.exception(f'The {script.name} script exited with an error')
        return "error", stderr.decode()
    return "success"


def post_callback(task: asyncio.Task, /, *, urls: CallbackUrls) -> None:
    try:
        # TODO: add message param for both errors and successes
        url = urls[task.result()]
        (httpx.post(url)).raise_for_status()
    except httpx.HTTPError:
        logger.exception(f'Failed to post callback to sonar')
    finally:
        background_tasks.discard(task)


@app.middleware("http")
async def http_signature(request: Request,
                         call_next: Callable) -> Response:
    # Unable to pass settings as a dependency due to FastAPI passing middleware directly to Starlette
    settings = get_settings()
    verifier = httpsig.HeaderVerifier(
        headers=request.headers,
        secret=settings.ppa_key_secret,
        required_headers=['(request-target)', 'date'],
        method='POST',
        path='/service-event'
    )
    if not verifier.verify():
        return status.HTTP_403_FORBIDDEN
    return await call_next(request)


@app.post("/service-event")
async def sonar_webhook(service_req: ServiceRequest,
                        settings: Settings = Depends(get_settings)) -> Response:
    script = scripts[service_req.type]
    task = asyncio.create_task(
        run(settings[script], service_req.json(), settings.ppa_service_timeout)
    )
    background_tasks.add(task)
    callback = partial(post_callback, urls=service_req.callback_urls)
    task.add_done_callback(callback)
    return status.HTTP_202_ACCEPTED
