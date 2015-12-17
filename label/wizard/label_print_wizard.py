# -*- coding: utf-8 -*-
import math

from openerp import fields, models, api, _
from openerp.tools import misc


class label_print_wizard(models.TransientModel):

    _name = 'label.print.wizard'

    name = fields.Many2one('label.config', _('Label Type'), required=True)
    number_of_labels = fields.Integer(_('Number of Labels (per item)'),
                                      required=True,
                                      default=0)
    labels_per_page = fields.Integer(_('Number of Labels per Pages'),
                                     compute="_compute_labels_per_page")
    brand_id = fields.Many2one('label.brand', _('Brand Name'), required=True)
    mm2px = fields.Float('mm to px')
    IN2MM = 25.4

    @api.model
    def default_get(self, fields):
        if self._context is None:
            self._context = {}
        result = super(label_print_wizard, self).default_get(fields)
        if self._context.get('label_print'):
            label_print_obj = self.env['label.print']
            label_print_data = label_print_obj.browse(
                self._context.get('label_print'))
            for field in label_print_data.sudo().field_ids:
                if field.type == 'barcode':
                    result['is_barcode'] = True
        return result

    @api.onchange('name')
    def _compute_labels_per_page(self):
        """
        Compute the number of labels per pages
        """
        for labels in self:
            if labels.name:
                rows = int((297-self.name.left_margin -
                            self.name.right_margin) /
                           (self.name.height or 1))
                columns = (float(210) / float(self.name.width or 1))
                self.labels_per_page = columns * rows

    @api.multi
    def print_report(self):
        if self._context is None:
            self._context = {}
        if (not self._context.get('label_print') or
                not self._context.get('active_ids') or
                not self.name):
            return False
        datas = {}
        column = (float(210) / float(self.name.width or 1))
        no_row_per_page = int((297-self.name.left_margin -
                               self.name.right_margin) /
                              (self.name.height or 1))

        label_print_obj = self.env['label.print']
        label_print_data = label_print_obj.browse(
            self._context.get('label_print'))

        ids = self.env.context['active_ids']
        rows_usable = int(math.ceil(float(math.ceil(
            self.number_of_labels*len(ids)) / int(column))))
        # dpi in mm
        self.mm2px = self.env.ref('label.paperformat_label').dpi / self.IN2MM
        datas = {
            'rows': int(no_row_per_page),
            'columns': int(column),
            'rows_usable': rows_usable,
            'model': self._context.get('active_model'),
            'ids': ids,
            'padding_top': label_print_data.padding_top,
            'padding_bottom': label_print_data.padding_bottom,
            'padding_left': label_print_data.padding_left,
            'padding_right': label_print_data.padding_right,
            'barcode_width': label_print_data.barcode_width,
            'barcode_height': label_print_data.barcode_height,
        }

        cr, uid, context = self.env.args
        context = dict(context)
        context.update({"label_print_id": self.env.context['label_print'],
                        'datas': datas})
        self.env.args = cr, uid, misc.frozendict(context)

        data = {
            'ids': self.ids,
            'model': 'label.config',
            'form': datas,
        }
        report_obj = self.env['report'].with_context(datas)
        return report_obj.get_action(self, 'label.report_label',
                                     data=data)
