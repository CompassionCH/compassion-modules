# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Jonathan Tarabbia <j.tarabbia@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from ..mappings.mobile_app_tile_mapping import TileMapping
from odoo import api, models, fields

_logger = logging.getLogger(__name__)


class AppTile(models.Model):
    # internal field Odoo
    _name = 'mobile.app.tile'
    _description = 'Tile'
    _order = 'view_order'

    # Fields of class
    priority = fields.Selection([
        ('High', 'High'),
        ('Normal', 'Normal'),
        ('Low', 'Low')
    ], 'Priority', default='Normal', required=True)
    name = fields.Char(required=True)
    view_order = fields.Integer('View order', required=True)
    start_date = fields.Datetime()
    end_date = fields.Datetime()
    is_active = fields.Boolean('Active', default=True)
    visibility = fields.Selection(
        [('public', 'Public'), ('private', 'Private'), ('both', 'Both')],
        required=True,
        help='Choose private if the sponsor must be logged in to see the tile'
    )
    model_id = fields.Many2one('ir.model', "Associated records")
    model = fields.Char(related='model_id.model')
    mode = fields.Selection([
        ('one', 'Unique tile'),
        ('many', 'One tile per record')
    ], help='This defines how to process related data')
    title = fields.Text(
        translate=True,
        help="Mako template enabled."
             "Use ctx['objects'] to get associated records."
    )
    body = fields.Text(
        translate=True,
        help="Mako template enabled."
             "Use ctx['objects'] to get associated records."
    )
    action_text = fields.Text(
        translate=True,
        help="Mako template enabled."
             "Use ctx['objects'] to get associated records."
    )
    subtype_id = fields.Many2one(
        'mobile.app.tile.subtype', 'Type', required=True)
    preview = fields.Binary(related='subtype_id.tile_preview', readonly=True)
    action_destination = fields.Selection(
        lambda s: s.env['mobile.app.tile.subtype'].select_action_destination(),
        required=True)

    @api.onchange('subtype_id')
    def _onchange_subtype(self):
        if self.subtype_id:
            self.body = self.subtype_id.default_body
            self.title = self.subtype_id.default_title
            self.action_text = self.subtype_id.default_action_text
            self.action_destination =\
                self.subtype_id.default_action_destination
            self.model_id = self.subtype_id.default_model_id

    @api.multi
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
        tile_mapping = TileMapping(self.env)
        res = []
        if tile_data is None:
            tile_data = {}
        for tile in self:
            tile_json = tile_mapping.get_connect_data(tile)
            records = tile.model and tile_data.get(tile.model)
            if records:
                # Convert text templates
                if tile.mode == 'one':
                    tile_json.update(tile._render_single_tile(records))
                    res.append(tile_json)
                elif tile.mode == 'many':
                    for record in records:
                        tile_json.update(tile._render_single_tile(record))
                        res.append(tile_json.copy())
            else:
                if tile_json['Type'] != 'Letter':
                    res.append(tile_json)
        return res

    def _render_single_tile(self, records):
        """
        Render mako template on a single tile object.
        :param records: associated records
        :return: JSON data of the tile.
        """
        self.ensure_one()
        template_obj = self.env['mail.template'].with_context(objects=records)
        res = {
            'Title': template_obj.render_template(
                self.title, self._name, self.id),
            'Body': template_obj.render_template(
                self.body, self._name, self.id),
            'ActionText': template_obj.render_template(
                self.action_text, self._name, self.id),
        }
        if hasattr(records, 'get_app_json'):
            res.update(records.get_app_json(multi=len(records) > 1))
        return res
