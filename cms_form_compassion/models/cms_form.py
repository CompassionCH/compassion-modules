import json
import logging
import traceback
from datetime import datetime, timedelta

from odoo import models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class CMSForm(models.AbstractModel):
    _inherit = "cms.form"

    #######################################################################
    #                         Field validation                            #
    #######################################################################

    @property
    def submit_icon(self):
        return ""

    @property
    def submit_text(self):
        return _("Submit")

    def form_make_field_wrapper_klass(self, fname, field, **kw):
        """ Allow to hide fields. """
        res = super().form_make_field_wrapper_klass(fname, field, **kw)
        if "field-hidden" in field["widget"]._w_css_klass:
            res += " field-hidden"
        return res

    #######################################################################
    #                          Errors logging                             #
    #######################################################################

    def form_process(self, **kw):
        """Catch, log and propagate the error thrown during the form processing"""
        try:
            super().form_process(**kw)
        except Exception as error:
            self._handle_exception(error, **kw)
            raise

    def _handle_exception(self, err, **kw):
        def truncate_strings(params, length=50):
            for k, v in params.items():
                if isinstance(v, dict):
                    truncate_strings(v)
                elif isinstance(v, str):
                    params[k] = len(v) > length and v[:length] + "... [TRUNCATED]" or v

        _logger.warning(
            "Exception occurred during form submission. Creating log "
            "entry in database."
        )

        err_class = err.__class__.__name__
        err_name = f"'{err_class}' in '{self._name}'"

        # We are handling an exception, rollback previous DB transactions
        self.env.cr.rollback()
        self.env.clear()

        # count the number of recent, similar errors
        last_week_dt = (datetime.now() + timedelta(days=-7)).strftime(
            DEFAULT_SERVER_DATETIME_FORMAT
        )
        err_count = 1 + self.env["ir.logging"].sudo().search_count(
            [("create_date", ">", last_week_dt), ("name", "=", err_name)]
        )
        err_count_message = f"Occurred {err_count} times in the last 7 days.\n\n"

        message = ((err_count > 1) and err_count_message or "") + traceback.format_exc(
            20
        )

        # Retrieve user input data
        # In some cases, fields can be excessively long (images, letters etc.)
        # We don't want to store these in the logs
        try:
            user_input = self.form_render_values["form_data"]
            truncate_strings(user_input, 50)
        except Exception as e:
            user_input = str(e)

        log_data = {
            "name": err_name,
            "type": "server",
            "message": message,
            "path": "",
            "line": "",
            "func": "",
            "context_data": json.dumps(
                {
                    # Additional data for debugging
                    "form_name": self._name,
                    "error_count": err_count,
                    "error_message": str(err),
                    "error_type": err_class,
                    "user_id": self.env.uid,
                    "user_input": user_input,
                },
                skipkeys=True,
                indent=4,
                ensure_ascii=True,
                sort_keys=True,
                default=str
            ),
        }

        # We are handling an exception, we need to commit the db transactions
        self.env["ir.logging"].sudo().create(log_data)
        self.env.cr.commit()  # pylint: disable=invalid-commit
