##############################################################################
#
#    Copyright (C) 2015-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino, Serpent Consulting Services Pvt. Ltd.
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models
from odoo.osv.orm import browse_record
from odoo.tools.safe_eval import safe_eval
from copy import deepcopy
from math import ceil


class ReportDynamicLabel(models.TransientModel):
    _name = 'report.label.report_label'
    _description = "Construct report from page"

    def get_data(self, row, columns, records, nber_labels):
        """
        Function called in the xml in order to get the datas for one page
        (in dynamic_label.xml).
        If multiple ids are given, the labels will be grouped by ids (therefore
        N Bob, then N Will, ...).

        :param int row: Number of row for one page of labels
        :param int columns: Number of columns of labels
        :param records: recordset used for the labels
        :param int nber_labels: Number of labels of each ids

        :returns: Data to print
        :rtype: list[page,row,columns,value] = dict
        """
        label_print_obj = self.env['label.print']
        label_print_data = label_print_obj.browse(
            self.env.context.get('label_print'))

        tot = nber_labels * len(records)
        tot_page = int(ceil(float(ceil(tot) // (columns*row))))
        # return value
        result = []
        for i in range(tot_page):
            result.append(
                [[[{'type': '', 'style': '', 'value': ''}] for i in
                  range(columns)] for j in range(row)])
        # current indices
        cur_row = 0
        cur_col = 0
        cur_page = 0
        # loop over all the items
        for record in records:
            # value to add
            vals = []
            # loop over each field for one label
            for field in label_print_data.sudo().field_ids:
                if field.python_expression and field.python_field:
                    value = safe_eval(field.python_field, {'obj': record})

                elif field.field_id.name:
                    value = getattr(record, field.field_id.name)

                if not value:
                    continue

                if isinstance(value, browse_record):
                    model_obj = self.pool.get(value._name)
                    value = safe_eval(
                        "obj." + model_obj._rec_name, {'obj': value})

                if not value:
                    value = ''

                # always put the image or barcode in first in order
                # to make a column for it
                first = False
                if field.type == 'barcode':
                    first = True

                # style is for CSS in HTML
                vals_dict = {'value': value,
                             'type': field.type,
                             'style': "font-size:" +
                             str(field.fontsize)+"px;"}
                if first:
                    vals.insert(0, vals_dict)
                else:
                    vals.append(vals_dict)
            for i in range(nber_labels):
                result[cur_page][cur_row][cur_col] = deepcopy(vals)
                cur_col += 1
                if cur_col >= columns:
                    cur_col = 0
                    cur_row += 1
                if cur_row >= row:
                    cur_page += 1
                    cur_row = 0
        return result

    @api.multi
    def get_report_values(self, docids, data=None):
        if docids is None:
            docids = data['doc_ids']
        label_print_records = self.env['label.print.wizard'].browse(docids)
        if data is None:
            data = {}
        data.update({
            'doc_ids': docids,
            'doc_model': "label.print.wizard",
            'docs': label_print_records,
            'env': self.env,
            'label_data': self.get_data(
                data['rows'], data['columns'],
                self.env[self.env.context.get('active_model')].browse(data['active_ids']),
                data['number_labels'])
        })
        return data
