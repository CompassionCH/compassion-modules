# -*- coding: utf-8 -*-

from openerp import tools
from openerp import models, fields, api


class SponsorshipLevelReport(models.Model):
    _name = "sponsorship.level.report"
    _description = "Sponsorship level Statistics"
    _auto = False
    fy = fields.Integer(string='Fiscal Year', readonly=True)
    date_level = fields.Date(readonly=True)
    spn = fields.Integer(string='net spn', readonly=True)
    spn_level = fields.Integer(string='total net spn', readonly=True)
    lang = fields.Selection([
    ("de_DE", 'German'),
    ("fr_CH", 'French'),
    ("en_US", 'English'),
    ("it_IT", 'Italian'),
    ], readonly=True)    
    
    def init(self,cr):
        # self._table = sponsorship_level_report
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            select date_level::date, date_level::date as id,
            case 
                when extract(month from(date_level))>6 
                then extract(year from(date_level)) +1 
                else extract(year from(date_level)) 
            end as fy,
            lang,sum(spn) as spn,
            sum(spn) over (partition by lang order by date_level) as spn_level
            from (
                select rc.activation_date as date_level, lang,count(rc.id) as spn
                from recurring_contract rc
                left join res_partner rp on rp.id=rc.partner_id
                where rc.state not in ('cancelled','waiting','mandate') and rc.activation_date is not null
                group by lang, activation_date
                
                union 
                
                select rc.end_date as date_level, lang,
                count(rc.id)*-1 as spn  
                from recurring_contract rc
                left join res_partner rp on rp.id=rc.partner_id
                where rc.state ='terminated' and rc.end_date is not null
                group by lang, end_date
            ) histo
            group by date_level,lang,spn
        )"""  % ( self._table))