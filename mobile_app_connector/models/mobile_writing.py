##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError

logger = logging.getLogger(__name__)


class AppWriting(models.Model):
    _name = 'mobile.app.writing'
    _description = 'Mobile App Writing'
    _order = 'state asc, print_count asc, date_start asc'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char('Category title', translate=True, required=True)
    icon = fields.Char('FontAwesome icon name', required=True)
    external_url = fields.Char(translate=True)
    date_start = fields.Date(
        readonly=True,
        states={'new': [('readonly', False)]}
    )
    date_stop = fields.Date(
        readonly=True,
        states={'new': [('readonly', False)]}
    )
    active = fields.Boolean()
    state = fields.Selection([
        ('new', 'New'),
        ('active', 'Active'),
        ('used', 'Used')
        ], compute='_compute_state', store=True, default='new')

    template_ids = fields.Many2many('correspondence.template',
                                    string="Templates")

    print_count = fields.Integer(readonly=True)
    position = fields.Integer()

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    @api.depends('active')
    def _compute_state(self):
        for writing in self:
            if writing.active:
                writing.state = 'active'
            else:
                writing.state = 'used' if writing.print_count else 'new'

    @api.multi
    @api.constrains('date_start', 'date_stop')
    def _check_dates(self):
        for writing in self:
            date_start = fields.Date.from_string(writing.date_start)
            date_stop = fields.Date.from_string(writing.date_stop)
            if date_start and date_stop and date_stop <= date_start:
                raise ValidationError(_("Period is not valid"))

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.model
    def validity_cron(self):
        today = fields.Date.today()
        active_writings = self.search([
            ('active', '=', True),
        ])
        current_writings = self.search([
            ('date_start', '<=', today),
            ('date_stop', '>=', today),
        ])
        without_dates_writings = self.search([
            ('date_start', '=', None),
            ('date_stop', '=', None),
        ])
        # Deactivate old stories
        (active_writings - current_writings - without_dates_writings).write(
            {'active': False})
        # Activate current stories
        current_writings.write({'active': True})

    @api.multi
    def mobile_get_templates(self, **params):
        actives = self.env['mobile.app.writing'].search(
            [('active', '=', True)])

        return [
            x.sudo().get_json() for x in actives
        ]

    @api.multi
    def get_json(self):
        self.ensure_one()
        web_base_url = \
            self.env['ir.config_parameter'].get_param('web.external.url')
        base_url = web_base_url + "/web/image/" + self.template_ids[0]._name \
            + "/"
        return {
            'templates': [
                {'templateURL': base_url + str(t.id) + "/template_image",
                 'id': str(t.id)} for t in self.template_ids
            ],
            'categoryIconString': self.icon,
            'label': self.name,
            'position': self.position,
        }
