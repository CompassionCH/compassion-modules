# -*- coding: utf-8 -*-
# Copyright 2017 Simone Orsi
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from datetime import datetime
from odoo import models, fields


class HiddenWidget(models.AbstractModel):
    _name = 'cms_form_compassion.form.widget.hidden'
    _inherit = 'cms.form.widget.mixin'
    _w_template = 'cms_form_compassion.field_widget_hidden'
    _w_css_klass = 'field-hidden'


class PaymentAcquirer(models.AbstractModel):
    _name = 'cms_form_compassion.form.widget.payment'
    _inherit = 'cms.form.widget.one2many'
    _w_template = 'cms_form_compassion.widget_payment'

    def widget_init(self, form, fname, field, **kw):
        """ Form must have field amount and currency_id. """
        widget = super(PaymentAcquirer, self).widget_init(
            form, fname, field, **kw)
        widget.w_acquirers = self.env['payment.acquirer'].search(
            [('website_published', '=', True)]
        )
        return widget


class PaymentAcquirerHidden(models.AbstractModel):
    _name = 'cms_form_compassion.form.widget.payment.hidden'
    _inherit = 'cms_form_compassion.form.widget.payment'
    _w_template = 'cms_form_compassion.widget_payment_hidden'
    _w_css_klass = 'field-hidden'


class GeneralTerms(models.AbstractModel):
    _name = 'cms_form_compassion.form.widget.terms'
    _inherit = 'cms.form.widget.boolean'
    _w_template = 'cms_form_compassion.field_widget_gtc'
    _w_css_klass = 'field-boolean field-gtc'


class SimpleImage(models.AbstractModel):
    _name = 'cms_form_compassion.form.widget.simple.image'
    _inherit = 'cms.form.widget.image'
    _w_template = 'cms_form_compassion.field_widget_image_simple'


class SimpleImageRequired(models.AbstractModel):
    _name = 'cms_form_compassion.form.widget.simple.image.required'
    _inherit = 'cms.form.widget.image'
    _w_template = 'cms_form_compassion.field_widget_image_simple_required'


class Document(models.AbstractModel):
    _name = 'cms_form_compassion.form.widget.document'
    _inherit = 'cms.form.widget.binary.mixin'
    _w_template = 'cms_form_compassion.field_widget_document'


class ReadonlyWidget(models.AbstractModel):
    _name = 'cms_form_compassion.form.widget.readonly'
    _inherit = 'cms.form.widget.mixin'
    _w_template = 'cms_form_compassion.field_widget_readonly'


class TimeWidget(models.AbstractModel):
    _name = 'cms.form.widget.time'
    _inherit = 'cms.form.widget.char'
    _w_template = 'cms_form_compassion.field_time'


class CHDateWidget(models.AbstractModel):
    _name = 'cms.form.widget.date.ch'
    _inherit = 'cms.form.widget.date'
    _w_template = 'cms_form_compassion.field_widget_date_ch'

    def w_extract(self, **req_values):
        value = super(CHDateWidget, self).w_extract(**req_values)
        if value:
            # Convert the date to ORM format
            value = fields.Date.to_string(
                datetime.strptime(value, '%d.%m.%Y').date())
        return value
