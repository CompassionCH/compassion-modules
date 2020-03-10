##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api, fields


class GenerateCommunicationWizard(models.TransientModel):
    _inherit = "partner.communication.generate.wizard"

    success_story_id = fields.Many2one(
        "success.story",
        "Success Story",
        domain=[("type", "=", "story")],
        readonly=False,
    )
    print_subject = fields.Boolean(default=True)
    print_header = fields.Boolean()

    @api.multi
    def generate(self):
        return super(
            GenerateCommunicationWizard,
            self.with_context(
                default_print_subject=self.print_subject,
                default_print_header=self.print_header,
                default_success_story_id=self.success_story_id.id,
            ),
        ).generate()
