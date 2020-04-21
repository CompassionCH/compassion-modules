# Copyright 2017 Simone Orsi
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import models


class HiddenWidget(models.AbstractModel):
    _name = "cms_form_compassion.form.widget.hidden"
    _inherit = "cms.form.widget.mixin"
    _w_template = "cms_form_compassion.field_widget_hidden"
    _w_css_klass = "field-hidden"


class PaymentAcquirer(models.AbstractModel):
    _name = "cms_form_compassion.form.widget.payment"
    _inherit = "cms.form.widget.one2many"
    _w_template = "cms_form_compassion.widget_payment"

    def widget_init(self, form, fname, field, **kw):
        """ Form must have field amount and currency_id. """
        widget = super().widget_init(form, fname, field, **kw)
        widget.w_acquirers = self.env["payment.acquirer"].search(
            [("website_published", "=", True)]
        )
        return widget


class PaymentAcquirerHidden(models.AbstractModel):
    _name = "cms_form_compassion.form.widget.payment.hidden"
    _inherit = "cms_form_compassion.form.widget.payment"
    _w_template = "cms_form_compassion.widget_payment_hidden"
    _w_css_klass = "field-hidden"


class GeneralTerms(models.AbstractModel):
    _name = "cms_form_compassion.form.widget.terms"
    _inherit = "cms.form.widget.boolean"
    _w_template = "cms_form_compassion.field_widget_gtc"
    _w_css_klass = "field-boolean field-gtc"


class SimpleImage(models.AbstractModel):
    _name = "cms_form_compassion.form.widget.simple.image"
    _inherit = "cms.form.widget.image"
    _w_template = "cms_form_compassion.field_widget_image_simple"

    def w_extract(self, **req_values):
        """
        - Save uploaded picture in storage to reload it in case of
        validation error (to avoid the user to have to re-upload it).
        - Set keepcheck to no, allows to override existing image in any case. """
        req_values.setdefault(self.w_fname + "_keepcheck", "no")
        value = req_values.get(self.w_fname)
        if hasattr(value, "seek"):
            value.seek(0)
        if value:
            value = self.form_to_binary(value, **req_values)
            self.w_form.request.session[self.w_fname] = value
        else:
            value = self.w_form.request.session.get(self.w_fname)
        return value


class SimpleImageRequired(models.AbstractModel):
    _name = "cms_form_compassion.form.widget.simple.image.required"
    _inherit = "cms.form.widget.image"
    _w_template = "cms_form_compassion.field_widget_image_simple_required"


class Document(models.AbstractModel):
    _name = "cms_form_compassion.form.widget.document"
    _inherit = "cms_form_compassion.form.widget.simple.image"
    _w_template = "cms_form_compassion.field_widget_document"


class ReadonlyWidget(models.AbstractModel):
    _name = "cms_form_compassion.form.widget.readonly"
    _inherit = "cms.form.widget.mixin"
    _w_template = "cms_form_compassion.field_widget_readonly"


class TimeWidget(models.AbstractModel):
    _name = "cms.form.widget.time"
    _inherit = "cms.form.widget.char"
    _w_template = "cms_form_compassion.field_time"


class CHDateWidget(models.AbstractModel):
    _name = "cms.form.widget.date.ch"
    _inherit = "cms.form.widget.date"
    w_date_format = "dd.mm.yyyy"
    w_date_week_start_day = "1"

    def get_placeholder(self):
        # Get correct placeholder depending on language
        placeholders = {
            "fr_CH": "JJ.MM.AA",
            "de_DE": "TT.MM.JJ",
            "it_IT": "GG.MM.AA",
            "en_US": "DD.MM.YY",
        }
        return placeholders.get(self.env.lang)

    def widget_init(self, form, fname, field, **kw):
        widget = super().widget_init(form, fname, field, **kw)
        if not widget.w_data['dp']:
            widget.w_data['dp'] = {}
        widget.w_data['dp'].update({
            'weekStartDay': widget.w_date_week_start_day,
            'locale': '-'.join([self.env.lang[:2]] * 2)
        })
        widget.w_placeholder = widget.get_placeholder()
        return widget
