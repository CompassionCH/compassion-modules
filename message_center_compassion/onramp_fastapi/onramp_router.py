from fastapi import APIRouter, Depends, Request

from odoo.addons.fastapi.dependencies import odoo_env

from .oauth_validation import auth_user, validate_headers

router = APIRouter()


# ruff: noqa: B008
@router.post("/", dependencies=[Depends(auth_user), Depends(validate_headers)])
async def onramp(
    req: Request,
    env: odoo_env = Depends(odoo_env),
):
    headers = req.headers
    body = await req.json()
    return env["onramp.service"].handle_incoming_message(
        headers=headers,
        body=body,
    )
