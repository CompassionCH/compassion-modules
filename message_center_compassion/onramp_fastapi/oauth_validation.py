import logging
from functools import lru_cache

import requests
from fastapi import Depends, Header, HTTPException, Request, status

from odoo.tools import config

from odoo.addons.fastapi.dependencies import odoo_env

_logger = logging.getLogger(__name__)

try:
    import jwt
    from jwt import PyJWK
    from jwt.exceptions import PyJWTError
except ImportError as e:
    _logger.error("Please install python pyjwt")
    raise e

# Put any authorized sender here. Its address must be part of the headers
# in order to handle a request.
AUTHORIZED_SENDERS = [
    "OnrampSimulator",
    "CISalesforce",
    "CISFDC",
    "CINetsuite",
    "SFDC-CI",
    "SFCI",
    "SponsorshipPool",
    "AMInterventions",
    "event-handlers-get-expired-reservations",
]


@lru_cache(maxsize=128)
def _decode_token_with_certs(token: str, cert_urls: tuple[str, ...]) -> dict | None:
    """Iterates through certificate URLs and their keys to decode the token."""
    for cert_url in cert_urls:
        try:
            response = requests.get(cert_url.strip(), timeout=5)
            response.raise_for_status()
            keys = response.json().get("keys", [])
        except (requests.RequestException, ValueError):
            _logger.warning("Failed to fetch or parse keys from %s", cert_url)
            continue

        for key_data in keys:
            try:
                public_key = PyJWK(key_data).key
                return jwt.decode(
                    token,
                    key=public_key,
                    algorithms=["RS256"],
                    options={"verify_signature": True},
                )
            except (PyJWTError, TypeError, KeyError):
                continue
    return None


@lru_cache(maxsize=128)
def _get_client_id(
    authorization: str,
):
    cert_urls_str = config.get("connect_token_cert")
    if not cert_urls_str:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Odoo configuration 'connect_token_cert' is not set.",
        )

    try:
        token_type, access_token = authorization.split()
        if token_type.lower() != "bearer":
            raise ValueError("Authorization header must be Bearer token")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format.",
        ) from e

    cert_urls = tuple(url.strip() for url in cert_urls_str.split(","))
    jwt_decoded = _decode_token_with_certs(access_token, cert_urls)

    if not jwt_decoded:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate the token.",
        )

    if "write" not in jwt_decoded.get("scope", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token does not have the required 'write' scope.",
        )

    client_id = jwt_decoded.get("client_id") or jwt_decoded.get("ClientID")
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client ID not found in token.",
        )

    return client_id


# ruff: noqa: B008
def auth_user(env: odoo_env = Depends(odoo_env), authorization: str = Header(...)):
    client_id = _get_client_id(authorization)
    user = (
        env["res.users"]
        .with_context(active_test=False)
        .search([("login", "=", client_id)])
    )
    if not user:
        _logger.error("Unauthorized user: %s", client_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized user.",
        )


# ruff: noqa: B008
def validate_headers(request: Request, env: odoo_env = Depends(odoo_env)):
    x_cim_from_address = request.headers.get("x-cim-FromAddress")
    x_cim_toaddress = request.headers.get("x-cim-ToAddress")
    x_cim_messagetype = request.headers.get("x-cim-MessageType")
    if not x_cim_messagetype:
        _logger.error("Unauthorized messagetype: %s", x_cim_messagetype)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing message type header",
        )
    if x_cim_from_address not in AUTHORIZED_SENDERS:
        _logger.error("Unauthorized sender: %s", x_cim_from_address)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wrong value for 'from' header",
        )
    company_obj = env["res.company"]
    param_obj = env["res.config.settings"]
    companies = company_obj.search([])
    country_codes = companies.mapped("partner_id.country_id.code") + [
        param_obj.get_param("connect_gpid")
    ]
    if x_cim_toaddress not in country_codes:
        _logger.error("Unauthorized toaddress: %s", x_cim_toaddress)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wrong value for 'to' header",
        )
