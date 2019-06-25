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

from odoo.tools.safe_eval import safe_eval
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
    display_name = fields.Char(
        'Name', compute='_compute_display_name', store=True, readonly=True)
    view_order = fields.Integer('View order', required=True, default=6000)
    is_automatic_ordering = fields.Boolean("Automatic ordering", default=True)
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
    records_filter = fields.Char(
        'Records filter function',
        help='will use the filtered function on the associated records'
    )
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
    code = fields.Char(related='subtype_id.code')
    preview = fields.Binary(related='subtype_id.tile_preview', readonly=True)
    action_destination = fields.Selection(
        lambda s: s.env['mobile.app.tile.subtype'].select_action_destination(),
        required=True)

    @api.depends('subtype_id', 'subtype_id.code', 'name')
    def _compute_display_name(self):
        for tile in self:
            tile.display_name = u'[{}] {}'.format(tile.code, tile.name)

    @api.onchange('subtype_id')
    def _onchange_subtype(self):
        if self.subtype_id:
            self.body = self.subtype_id.default_body
            self.title = self.subtype_id.default_title
            self.action_text = self.subtype_id.default_action_text
            self.action_destination =\
                self.subtype_id.default_action_destination
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
        for lang in self.env['res.lang'].search([('active', '=', True)]):
            for tile in self.search(domain).with_context(lang=lang.code):
                tile._onchange_subtype()
        return True

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
            records = tile._get_records(tile_data)
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
                # Some tiles shouldn't rendered when no records are associated
                module = 'mobile_app_connector.%s'
                no_render = self.env.ref(module % 'tile_type_donation') + \
                    self.env.ref(module % 'tile_type_letter') +\
                    self.env.ref(module % 'tile_type_child')
                if tile.subtype_id.type_id not in no_render:
                    res.append(tile_json)
        return res

    @api.multi
    def render_unpaid_tile(self, unpaid_tile=None):
        """
        This is the secondary function rendering part of the JSON
        for the mobile app.
        :param unpaid_tile: this is a dict containing all data needed for
                          the tiles. The keys are the odoo models and values
                          are the record ids (list). Example :
                          {
                            'compassion.child': <compassion.child> recordset,
                            'res.partner': <res.partner> recordset,
                          }
        :return: Tiles of awaiting payments for mobile app (list of dict)
        """
        self.ensure_one()
        unpaid_mapping = TileMapping(self.env)
        res = []
        if unpaid_tile is None:
            unpaid_tile = {}
        tile_json = unpaid_mapping.get_connect_data(self)
        records = self._get_records(unpaid_tile)
        if records:
            # Convert text templates
            if self.mode == 'one':
                tile_json.update(self._render_single_tile(records))
                tile_json['Child']['SupporterGroupId'] = self.env.user.id
                res.append(tile_json)
            elif self.mode == 'many':
                for record in records:
                    tile_json.update(self._render_single_tile(record))
                    tile_json['Child']['SupporterGroupId'] = self.env.user.id
                    res.append(tile_json.copy())
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
            except:
                _logger.error(
                    'Cannot filter recordset given the function',
                    exc_info=True
                )
        return records

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
            'SortOrder': self.view_order,
            'IsAutomaticOrdering': self.is_automatic_ordering,
        }

        if hasattr(records, 'get_app_json'):
            res.update(records.get_app_json(multi=len(records) > 1))
        return res
