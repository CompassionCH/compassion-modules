##############################################################################
#
#    Copyright (C) 2014-2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino, Cyril Sester
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import base64
import logging
from datetime import date
from urllib.request import urlopen

from odoo import models, fields, api

logger = logging.getLogger(__name__)


class GenericChild(models.AbstractModel):
    """ Generic information of children shared by subclasses:
        - compassion.child : sponsored children
        - compassion.global.child : available children in global pool
    """

    _name = "compassion.generic.child"
    _inherit = ["compassion.mapped.model"]
    _description = "Generic Child"

    # General Information
    #####################
    global_id = fields.Char("Global ID", required=True, readonly=True)
    correspondence_language_id = fields.Many2one(
        "res.lang.compassion", "Correspondence language", readonly=False
    )
    local_id = fields.Char("Local ID", size=11, help="Child reference", readonly=True)
    project_id = fields.Many2one("compassion.project", "Project", readonly=False)
    field_office_id = fields.Many2one(
        "compassion.field.office",
        "Field office",
        related="project_id.field_office_id",
        readonly=False,
    )
    name = fields.Char()
    firstname = fields.Char()
    lastname = fields.Char()
    preferred_name = fields.Char()
    gender = fields.Selection([("F", "Female"), ("M", "Male")], readonly=True)
    birthdate = fields.Date(readonly=True)
    age = fields.Integer(readonly=True, compute="_compute_age")
    is_orphan = fields.Boolean(readonly=True)
    is_area_hiv_affected = fields.Boolean()
    beneficiary_state = fields.Selection("_get_availability_state", readonly=True)
    sponsorship_status = fields.Selection(
        [("Sponsored", "Sponsored"), ("Unsponsored", "Unsponsored"), ], readonly=True
    )
    unsponsored_since = fields.Date(readonly=True)
    image_url = fields.Char()
    thumbnail_url = fields.Char(compute="_compute_image_thumb")

    @api.model
    def _get_availability_state(self):
        return [
            ("Available", "Available"),
            ("Active", "Active"),
            ("Change Commitment Hold", "Change Commitment Hold"),
            ("Consignment Hold", "Consignment Hold"),
            ("Delinquent Mass Cancel Hold", "Delinquent Mass Cancel Hold"),
            ("E-Commerce Hold", "E-Commerce Hold"),
            ("Inactive", "Inactive"),
            ("Ineligible", "Ineligible"),
            ("No Money Hold", "No Money Hold"),
            ("Reinstatement Hold", "Reinstatement Hold"),
            ("Reservation Hold", "Reservation Hold"),
            ("Sponsor Cancel Hold", "Sponsor Cancel Hold"),
            ("Sponsored", "Sponsored"),
            ("Sub Child Hold", "Sub Child Hold"),
        ]

    @api.model
    def get_fields(self):
        return [
            "global_id",
            "local_id",
            "project_id",
            "name",
            "firstname",
            "lastname",
            "preferred_name",
            "gender",
            "birthdate",
            "age",
            "is_orphan",
            "beneficiary_state",
            "sponsorship_status",
            "unsponsored_since",
            "correspondence_language_id",
            "image_url",
        ]

    def get_child_vals(self):
        """ Get the required field values of one record for other record
            creation.
            :return: Dictionary of values for the fields
        """
        self.ensure_one()
        vals = self.read(self.get_fields())[0]
        if vals.get("correspondence_language_id"):
            vals["correspondence_language_id"] = vals["correspondence_language_id"][0]
        if vals.get("project_id"):
            vals["project_id"] = vals["project_id"][0]

        del vals["id"]
        return vals

    def _compute_age(self):
        today = date.today()
        for child in self:
            born = child.birthdate
            child.age = born and (
                today.year
                - born.year
                - ((today.month, today.day) < (born.month, born.day))
            )

    def _compute_image_thumb(self):
        self._load_image(True, False)

    @api.model
    def json_to_data(self, json, mapping_name=None):
        odoo_data = super().json_to_data(json, mapping_name)

        # Put firstname in preferred_name if not defined
        preferred_name = odoo_data.get("preferred_name")
        if not preferred_name:
            odoo_data["preferred_name"] = odoo_data.get("firstname")
        if 'hold_expiration_date' in odoo_data:
            odoo_data['hold_expiration_date'] = odoo_data['hold_expiration_date'].replace('T', ' ')
            odoo_data['hold_expiration_date'] = odoo_data['hold_expiration_date'].replace('Z', '')
        return odoo_data

    def _load_image(self, thumb=False, binar=False):
        if thumb:
            height = 180
            width = 180
            cloudinary = "g_face,c_thumb,h_" + str(height) + ",w_" + str(width)
            for child in self.filtered("image_url"):
                # url are typically under this format:
                # https://media.ci.org/image/upload/w_150/ChildPhotos/Published/
                # 06182814_539e18.jpg
                image_split = (child.image_url).split("/")
                try:
                    ind = image_split.index("w_150")
                    image_split[ind] = cloudinary
                    url = "/".join(image_split)
                    child.thumbnail_url = url
                except ValueError:
                    logger.error("Wrong child image received: " + str(child.image_url))

        if binar:
            for child in self.filtered("image_url"):
                url = child.image_url if not thumb else child.thumbnail_url
                try:
                    child.portrait = base64.encodebytes(urlopen(url).read())
                except:
                    logger.error("Image cannot be fetched : " + str(url))


class GlobalChild(models.TransientModel):
    """ Available child in the global childpool
    """

    _name = "compassion.global.child"
    _inherit = "compassion.generic.child"
    _description = "Global Child"

    portrait = fields.Binary(compute="_compute_image_portrait")
    fullshot = fields.Binary(compute="_compute_image_fullshot")

    color = fields.Integer(compute="_compute_color")
    is_special_needs = fields.Boolean()
    field_office_id = fields.Many2one(store=True, readonly=False)
    search_view_id = fields.Many2one("compassion.childpool.search", readonly=False)
    priority_score = fields.Float(help="How fast the child should be " "sponsored")
    holding_global_partner_id = fields.Many2one(
        "compassion.global.partner", "Holding global partner", readonly=False
    )
    waiting_days = fields.Integer()
    hold_expiration_date = fields.Datetime()
    source_code = fields.Char("origin of the hold")

    def _compute_color(self):
        available = self.filtered(lambda c: c.beneficiary_state == "Available")
        for child in available:
            child.color = 4 if child.gender == "M" else 9
        for child in self - available:
            child.color = 7 if child.gender == "M" else 5

    def _compute_image_portrait(self):
        self._load_image(True, True)

    def _compute_image_fullshot(self):
        self._load_image(False, True)
