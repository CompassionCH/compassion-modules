##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api, _


class CorrespondenceMetadata(models.AbstractModel):
    """ This class defines all metadata of a correspondence.
        This is an abstract class that should never be used for creating
        records.
    """

    _name = "correspondence.metadata"
    _description = "Metadata of letter"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    physical_attachments = fields.Selection(
        selection=[("sent_by_mail", _("Sent by mail")), ("not_sent", _("Not sent"))]
    )
    attachments_description = fields.Char()
    template_id = fields.Many2one("correspondence.template", "Template", readonly=False)
    source = fields.Selection(
        selection=[
            ("app", "Mobile app"),
            ("compassion", "Written by Compassion"),
            ("email", "E-Mail"),
            ("letter", "Scanned Letter"),
            ("mycompassion", "MyCompassion"),
            ("website", "Compassion website"),
        ],
        default="letter",
    )

    @api.model
    def get_fields(self):
        return [
            "physical_attachments",
            "attachments_description",
            "template_id",
            "source",
        ]

    def get_correspondence_metadata(self):
        """ Get the field values of one record.
        :return: Dictionary of values for the fields
        """
        self.ensure_one()
        vals = self.read(self.get_fields())[0]
        if vals.get("template_id"):
            vals["template_id"] = vals["template_id"][0]
        del vals["id"]
        return vals
