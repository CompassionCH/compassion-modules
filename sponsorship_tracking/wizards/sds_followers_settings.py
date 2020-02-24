##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class SdsFollowerSettings(models.TransientModel):
    """ Settings configuration for any Notifications."""
    _name = 'sds.follower.settings'
    _inherit = 'res.config.settings'
    _description = 'SDS Followers Settings'

    # Users to notify after Child Departure
    sub_fr = fields.Many2one(
        'res.users', string='Sub sponsorships (FR)',
        domain=[('share', '=', False)], readonly=False
    )
    sub_de = fields.Many2one(
        'res.users', string='Sub sponsorships (DE)',
        domain=[('share', '=', False)], readonly=False

    )
    sub_it = fields.Many2one(
        'res.users', string='Sub sponsorships (IT)',
        domain=[('share', '=', False)], readonly=False
    )
    sub_en = fields.Many2one(
        'res.users', string='Sub sponsorships (EN)',
        domain=[('share', '=', False)], readonly=False
    )

    @api.multi
    def set_sub_fr(self):
        self.env['ir.config_parameter'].set_param(
            'sponsorship_tracking.sub_follower_fr', str(self.sub_fr.id))

    @api.multi
    def set_sub_de(self):
        self.env['ir.config_parameter'].set_param(
            'sponsorship_tracking.sub_follower_de', str(self.sub_de.id))

    @api.multi
    def set_sub_it(self):
        self.env['ir.config_parameter'].set_param(
            'sponsorship_tracking.sub_follower_it', str(self.sub_it.id))

    @api.multi
    def set_sub_en(self):
        self.env['ir.config_parameter'].set_param(
            'sponsorship_tracking.sub_follower_en', str(self.sub_en.id))

    @api.model
    def get_default_values(self, _fields):
        param_obj = self.env['ir.config_parameter']
        fr = param_obj.get_param(
            'sponsorship_tracking.sub_follower_fr', self.env.uid)
        de = param_obj.get_param(
            'sponsorship_tracking.sub_follower_de', self.env.uid)
        it = param_obj.get_param(
            'sponsorship_tracking.sub_follower_it', self.env.uid)
        en = param_obj.get_param(
            'sponsorship_tracking.sub_follower_en', self.env.uid)
        return {
            'sub_fr': int(fr),
            'sub_de': int(de),
            'sub_it': int(it),
            'sub_en': int(en),
        }

    @api.model
    def get_param(self, param):
        """ Retrieve a single parameter. """
        return self.get_default_values([param])[param]
