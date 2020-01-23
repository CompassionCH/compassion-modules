# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
import traceback
import json
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


def _form_validate_date_fields(value, **req_values):
    try:
        if value:
            datetime.strptime(value, '%d.%m.%Y')
    except ValueError:
        return "date", _('Dates should follow the format "dd.mm.yyyy"')
    return 0, 0


class CMSForm(models.AbstractModel):
    _inherit = 'cms.form'

    #######################################################################
    #                         Field validation                            #
    #######################################################################

    _form_validators = {
        'date': _form_validate_date_fields
    }

    #######################################################################
    #                          Errors logging                             #
    #######################################################################

    def form_process(self, **kw):
        """Catch, log and propagate the error thrown during the form processing"""
        try:
            super(CMSForm, self).form_process(**kw)
        except Exception as error:
            self._handle_exception(error, **kw)
            raise

    def _handle_exception(self, err, **kw):
        def truncate_strings(params, length=50):
            for k, v in params.iteritems():
                if isinstance(v, dict):
                    truncate_strings(v)
                elif isinstance(v, (str, unicode)):
                    params[k] = len(v) > length and v[:length] + "... [TRUNCATED]" or v

        _logger.info("Exception occurred during form submission. Creating log "
                     "entry in database.")

        err_class = err.__class__.__name__
        err_name = "'{}' in '{}'".format(err_class, self._name)

        # We are handling an exception, rollback previous DB transactions
        self.env.cr.rollback()
        self.env.invalidate_all()

        # count the number of recent, similar errors
        last_week_dt = (datetime.now() + timedelta(days=-7)).strftime(
            DEFAULT_SERVER_DATETIME_FORMAT)
        err_count = 1 + self.env['ir.logging'].sudo().search_count([
            ('create_date', '>', last_week_dt),
            ('name', '=', err_name)
        ])
        err_count_message = "Occurred %d times in the last 7 days.\n\n" % err_count

        message = "{}{}".format(
            (err_count > 1) and err_count_message or "",
            traceback.format_exc(20)
        )

        # Retrieve user input data
        # In some cases, fields might be excessively long (images, letters etc.)
        # We don't want to store these in the logs
        try:
            user_input = self.form_render_values['form_data']
            truncate_strings(user_input, 50)
        except Exception as e:
            user_input = str(e)

        log_data = {
            'name': err_name,
            'type': 'server',
            'message': message,
            'path': "",
            'line': "",
            'func': "",
            'context_data': json.dumps({
                # Additional data for debugging
                'form_name': self._name,
                'error_count': err_count,
                'error_message': str(err),
                'error_type': err_class,
                'user_input': user_input,
            }, skipkeys=True, indent=4, ensure_ascii=True, sort_keys=True),
        }

        # We are handling an exception, we need to commit the db transactions
        self.env['ir.logging'].sudo().create(log_data)
        self.env.cr.commit()
