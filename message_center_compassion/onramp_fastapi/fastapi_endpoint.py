from odoo import fields, models

from .onramp_router import router as onramp_router


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[("onramp", "Onramp Endpoint")], ondelete={"onramp": "cascade"}
    )

    def _get_fastapi_routers(self):
        if self.app == "onramp":
            return [onramp_router]
        return super()._get_fastapi_routers()
