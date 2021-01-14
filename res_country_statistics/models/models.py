##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Wulliamoz <dwulliamoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields
from pandas_datareader import wb
import logging

_logger = logging.getLogger(__name__)


class ResCountryInfo(models.AbstractModel):
    """ add latest stat to the country """
    _inherit = "res.country"
    capital_city = fields.Char("capital city")
    statistics_ids = fields.Many2many(
        "res.country.stat",
        "res_country_stat_latest",
        string="latest stat",
        compute="_compute_latest_stats",
        track_visibility="onchange",
    )

    @api.multi
    def _compute_latest_stats(self):
        indicators = self.env['res.country.indicator'].search([])
        for record in self:
            stat = self.env['res.country.stat'].search([('country_id', '=', record.id)])
            country_statistics = []
            for i in indicators:
                res = stat.search([('indicator_id', '=', i.id)], order='year desc', limit=1)
                if res:
                    country_statistics.append(res.id)
            self.statistics_ids = country_statistics


class CountryIndicators(models.Model):
    _name = "res.country.indicator"
    _description = "Development indicator from the world bank"
    ref = fields.Char("Reference")
    name = fields.Char("Name")
    description = fields.Char("Description")
    type = fields.Selection([
        ("%pop", "% of population"),
        ("tot", "Total"),
        ("y", "Years"),
        ("p1000lb", "per 1000 live births")], readonly=True)


class CountryInformation(models.Model):
    _name = "res.country.stat"
    _description = "Field Office statistical information"
    year = fields.Integer("Year")
    country_id = fields.Many2one("res.country", "Country", readonly=False)
    indicator_id = fields.Many2one("res.country.indicator", "Indicator", readonly=False)
    value = fields.Float("Value")

    @api.model
    def load_wb_data(self, countries_list, from_year, to_year):
        indicators = self.env['res.country.indicator'].search([('ref', '!=', False)])
        dat = wb.download(indicator=indicators.mapped('ref'), country=countries_list, start=from_year, end=to_year)
        countries = self.env['res.country'].search([('code', 'in', countries_list)])
        for i in indicators:
            i_per_country = dat[i.ref]
            for c in countries:
                for year, value in i_per_country[c.with_context(lang='en_US').name].dropna().iteritems():
                    vals = {
                        'year': year,
                        'country_id': c.id,
                        'indicator_id': i.id,
                        'value': value
                    }
                    if not self.search([
                        ('year', '=', year),
                        ('country_id', '=', c.id),
                        ('indicator_id', '=', i.id),
                        ('value', '=', value)]):
                        self.create(vals)
