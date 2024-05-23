##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Jonathan Tarabbia <j.tarabbia@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import random

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class AppTile(models.Model):
    # internal field Odoo
    _name = "mobile.app.tile"
    _description = "Tile"
    _inherit = "compassion.mapped.model"
    _order = "view_order"

    # Fields of class
    priority = fields.Selection(
        [("High", "High"), ("Normal", "Normal"), ("Low", "Low")],
        "Priority",
        default="Normal",
        required=True,
    )
    name = fields.Char(required=True)
    display_name = fields.Char(
        "Name", compute="_compute_display_name", store=True, readonly=True
    )
    view_order = fields.Integer("View order", required=True, default=6000)
    is_automatic_ordering = fields.Boolean("Automatic ordering", default=True)
    start_date = fields.Datetime()
    end_date = fields.Datetime()
    active = fields.Boolean(default=True)
    visibility = fields.Selection(
        [("public", "Public"), ("private", "Private"), ("both", "Both")],
        required=True,
        help="Choose private if the sponsor must be logged in to see the tile",
    )
    model_id = fields.Many2one("ir.model", "Associated records", readonly=False)
    model = fields.Char(related="model_id.model")
    records_filter = fields.Char(
        "Records filter function",
        help="will use the filtered function on the associated records",
    )
    mode = fields.Selection(
        [("one", "Unique tile"), ("many", "One tile per record")],
        help="This defines how to process related data",
    )
    title = fields.Text(
        translate=True,
        help="Mako template enabled." "Use ctx['objects'] to get associated records.",
    )
    body = fields.Text(
        translate=True,
        help="Mako template enabled." "Use ctx['objects'] to get associated records.",
    )
    action_text = fields.Text(
        translate=True,
        help="Mako template enabled." "Use ctx['objects'] to get associated records.",
    )
    subtype_id = fields.Many2one(
        "mobile.app.tile.subtype", "Type", required=True, readonly=False
    )
    code = fields.Char(related="subtype_id.code")
    preview = fields.Binary(related="subtype_id.tile_preview", readonly=True)
    action_destination = fields.Selection(
        lambda s: s.env["mobile.app.tile.subtype"].select_action_destination(),
        required=True,
    )
    is_prayer = fields.Boolean(compute="_compute_is_prayer")
    prayer_title = fields.Text(
        translate=True,
        help="Mako template enabled." "Use ctx['objects'] to get associated records.",
    )
    prayer_body = fields.Text(
        translate=True,
        help="Mako template enabled." "Use ctx['objects'] to get associated records.",
    )

    @api.depends("subtype_id", "subtype_id.code", "name")
    def _compute_display_name(self):
        for tile in self:
            tile.display_name = "[{}] {}".format(tile.code, tile.name)

    def _compute_is_prayer(self):
        prayer_type = self.env.ref("mobile_app_connector.tile_type_prayer")
        for tile in self:
            tile.is_prayer = tile.subtype_id.type_id == prayer_type

    @api.onchange("subtype_id")
    def _onchange_subtype(self):
        if self.subtype_id:
            if self.subtype_id.default_body:
                self.body = self.subtype_id.default_body
            self.title = self.subtype_id.default_title
            self.action_text = self.subtype_id.default_action_text
            self.action_destination = self.subtype_id.default_action_destination
            self.model_id = self.subtype_id.default_model_id
            self.records_filter = self.subtype_id.default_records_filter

    @api.model
    def init_tiles(self, domain=None):
        """
        Use this to set all tiles to their default templates defined
        in the tile subtypes. Called at module init.
        :param domain: optional search domain to restrict the reinitialization
        :return: True
        """
        if domain is None:
            domain = []
        # We iterate on all language to force the translations to be applied
        # to the texts.
        for lang in self.env["res.lang"].search([("active", "=", True)]):
            for tile in self.search(domain).with_context(lang=lang.code):
                tile._onchange_subtype()
        return True

    def render_tile(self, tile_data=None):
        """
        This is the main function rendering the JSON for the mobile app.
        :param tile_data: this is a dict containing all data needed for
                          the tiles. The keys are the odoo models and values
                          are the record ids (list). Example :
                          {
                            'compassion.child': <compassion.child> recordset,
                            'res.partner': <res.partner> recordset,
                          }
        :return: Tiles for mobile app (list of dict)
        """
        res = []
        prayed_child = []
        if "compassion.child" in tile_data:
            num_children = len(tile_data["compassion.child"])
            num_prayers = len(self.filtered(lambda t: t.code == "PR1"))
        if tile_data is None:
            tile_data = {}
        for tile in self:
            tile_json = tile.data_to_json("mobile_app_tile")
            records = tile._get_records(tile_data)
            if records:
                # Convert text templates
                if tile.mode == "one":
                    text_data = tile._render_single_tile(records)
                    if text_data:
                        tile_json.update(text_data)
                        res.append(tile_json)
                elif tile.mode == "many":
                    if tile.code == "PR1":
                        to_pray_children = records.filtered(
                            lambda rec: rec.id not in prayed_child
                        )
                        # We drop tiles with expectation equal 1 tile / child
                        if (
                            not to_pray_children
                            or random.uniform(0, 1) > num_children / num_prayers
                        ):
                            continue
                        child = random.choice(to_pray_children)
                        text_data = tile._render_single_tile(child)
                        if text_data:
                            tile_json.update(text_data)
                            res.append(tile_json.copy())
                            prayed_child.append(child.id)
                    else:
                        for record in records:
                            text_data = tile._render_single_tile(record)
                            if text_data:
                                tile_json.update(text_data)
                                res.append(tile_json.copy())

            else:
                # Some tiles shouldn't rendered when no records are associated
                module = "mobile_app_connector.%s"
                no_render = (
                    self.env.ref(module % "tile_type_donation")
                    + self.env.ref(module % "tile_type_letter")
                    + self.env.ref(module % "tile_type_child")
                    + self.env.ref(module % "tile_type_community")
                )
                if (
                    tile.subtype_id.type_id not in no_render
                    and tile.subtype_id != self.env.ref(module % "tile_subtype_pr1")
                ):
                    res.append(tile_json)
        return res

    def _get_records(self, tile_data):
        """
        Retrieves and filters the associated records
        :param tile_data: All records given by the main hub method
        :return: filtered records needed for the tile
        """
        self.ensure_one()
        records = self.model and tile_data.get(self.model)
        if records and self.records_filter:
            try:
                records = records.filtered(safe_eval(self.records_filter))
            except Exception:
                _logger.error(
                    "Cannot filter recordset given the function", exc_info=True
                )
        return records

    def _render_single_tile(self, records):
        """
        Render mako template on a single tile object.
        :param records: associated records
        :return: JSON data of the tile.
        """
        try:
            self.ensure_one()
            template_obj = self.env["mail.template"].with_context(objects=records)
            res = {
                "Title": template_obj._render_template(self.title, self._name, self.id),
                "Body": template_obj._render_template(self.body, self._name, self.id),
                "ActionText": template_obj._render_template(
                    self.action_text, self._name, self.id
                ),
                "SortOrder": self.view_order,
                "IsAutomaticOrdering": self.is_automatic_ordering,
            }

            if self.prayer_title and self.prayer_body:
                res["PrayerPoint"] = {
                    "Body": template_obj._render_template(
                        self.prayer_body, self._name, self.id
                    ),
                    "Title": template_obj._render_template(
                        self.prayer_title, self._name, self.id
                    ),
                }

            if hasattr(records, "get_app_json"):
                res.update(records.get_app_json(multi=len(records) > 1))
        except Exception:
            _logger.error("Error rendering tile %s", self.name, exc_info=True)
            res = {}
        if not res.get("OrderDate"):
            res["OrderDate"] = self.create_date
        return res

    def data_to_json(self, mapping_name=None):
        res = super().data_to_json(mapping_name)
        if not res:
            res = {}
        for key, value in list(res.copy().items()):
            if key == "ActionText":
                if value:
                    res[key] = str(value)
                else:
                    res[key] = None
        return res
