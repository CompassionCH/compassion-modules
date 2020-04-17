##############################################################################
#
#    Copyright (C) 2015-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino, Serpent Consulting Services Pvt. Ltd.
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64

from reportlab.graphics.barcode import createBarcodeDrawing

from odoo import fields, models, api

DPI = 150
ONE_INCH = 25.4


class LabelPrintWizard(models.TransientModel):
    _name = "label.print.wizard"
    _description = "Label Print Wizard"

    config_id = fields.Many2one(
        "label.config",
        "Label Type",
        required=True,
        default=lambda s: s.env.ref("label.label_4455"),
        readonly=False,
    )
    number_of_labels = fields.Integer(
        "Number of Labels (per item)", required=True, default=33
    )
    labels_per_page = fields.Integer(
        "Number of Labels per Pages", compute="_compute_labels_per_page"
    )
    brand_id = fields.Many2one(
        "label.brand",
        "Brand Name",
        required=True,
        default=lambda s: s.env.ref("label.herma4"),
        readonly=False,
    )

    @api.onchange("config_id")
    def _compute_labels_per_page(self):
        """
        Compute the number of labels per pages
        """
        for labels in self:
            if labels.config_id:
                rows = int(
                    (297 - self.config_id.left_margin - self.config_id.right_margin)
                    // (self.config_id.height or 1)
                )
                columns = float(210) // float(self.config_id.width or 1)
                self.labels_per_page = columns * rows

    @api.multi
    def get_report_data(self):
        if self._context is None or (
                not self._context.get("label_print")
                or not self._context.get("active_ids")
                or not self.config_id
        ):
            return False

        column = float(210) // float(self.config_id.width or 1)
        no_row_per_page = int(
            (297 - self.config_id.left_margin - self.config_id.right_margin)
            // (self.config_id.height or 1)
        )

        label_print_obj = self.env["label.print"]
        label_print_data = label_print_obj.browse(self._context.get("label_print"))

        data = {
            "rows": int(no_row_per_page),
            "columns": int(column),
            "number_labels": self.number_of_labels,
            "active_model": self.env.context.get("active_model"),
            "active_ids": self.env.context.get("active_ids"),
            "doc_ids": self.ids,
            "padding_top": label_print_data.padding_top,
            "padding_bottom": label_print_data.padding_bottom,
            "padding_left": label_print_data.padding_left,
            "padding_right": label_print_data.padding_right,
            "barcode_width": label_print_data.barcode_width,
            "barcode_height": label_print_data.barcode_height,
        }
        return data

    @api.multi
    def print_report(self):
        data = self.get_report_data()
        return self.env.ref("label.dynamic_label").report_action(
            self.ids, data=data, config=False)

    @api.model
    def barcode(self, barcode_type, value, width, height):
        """
        Copy method in report module because barcode is not working otherwise
        """
        if barcode_type == "UPCA" and len(value) in (11, 12, 13):
            barcode_type = "EAN13"
            if len(value) in (11, 12):
                value = f"0{value}"
        try:
            width, height = int(DPI * width // ONE_INCH), int(DPI * height // ONE_INCH)
            barcode = createBarcodeDrawing(
                barcode_type, value=value, format="png", width=width, height=height,
            )
            return base64.b64encode(barcode.asString("png")).decode("utf-8")
        except (ValueError, AttributeError):
            raise ValueError("Cannot convert into barcode.")
