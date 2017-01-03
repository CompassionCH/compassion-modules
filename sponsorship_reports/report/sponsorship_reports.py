# -*- coding: utf-8 -*-

from openerp import tools
from openerp import models, fields, api


class SponsorshipContractReport(models.Model):
    _name = "sponsorship.contract.report"
    _description = "Sponsorship Statistics"
    _auto = False


    start_date = fields.Date(readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    advocate_id = fields.Many2one('res.partner', string='Advocate', readonly=True)
    activation_date = fields.Date(readonly=True)
    end_date = fields.Date(readonly=True)
    departure_fy = fields.Integer(string='Departure Fiscal Year', readonly=True)
    fy = fields.Integer(string='Fiscal Year', readonly=True)
    aquisition_fy = fields.Integer(string='Aquisition Fiscal Year', readonly=True)
    lang = fields.Selection([
        ("de_DE", 'German'),
        ("fr_CH", 'French'),
        ("en_US", 'English'),
        ("it_IT", 'Italian'),
        ], readonly=True)    
    paid_month = fields.Selection([
        (1, 'July'),
        (2, 'August'),
        (3, 'September'),
        (4, 'October'),
        (5, 'November'),
        (6, 'December'),
        (7, 'January'),
        (8, 'February'),
        (9, 'March'),
        (10, 'April'),
        (11, 'May'),
        (12, 'June'),
        ], readonly=True)
    departure_month = fields.Selection([
        (1, 'July'),
        (2, 'August'),
        (3, 'September'),
        (4, 'October'),
        (5, 'November'),
        (6, 'December'),
        (7, 'January'),
        (8, 'February'),
        (9, 'March'),
        (10, 'April'),
        (11, 'May'),
        (12, 'June'),
        ], readonly=True)
    aquisition_month_int = fields.Integer(readonly=True)
    aquisition_month = fields.Selection([
        (1, 'July'),
        (2, 'August'),
        (3, 'September'),
        (4, 'October'),
        (5, 'November'),
        (6, 'December'),
        (7, 'January'),
        (8, 'February'),
        (9, 'March'),
        (10, 'April'),
        (11, 'May'),
        (12, 'June'),
        ], readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('terminated', 'Terminated'),
        ('cancelled', 'Cancelled'),
        ('mandate', 'waiting mandate'),
        ('waiting', 'waiting payment'),
        ], readonly=True)
    end_reason = fields.Char(string='Reason', readonly=True)
    origin_id = fields.Many2one('recurring.contract.origin', string='Commitment origin')
    origin_type = fields.Selection([
        ('event', 'event'),
        ('marketing', 'marketing'),
        ('other', 'other'),
        ('sub', 'sub'),
        ('transfer', 'transfer'),
        ],readonly=True)
    event_name = fields.Char(string='Event', readonly=True)
    event_type = fields.Char(string='Event type', readonly=True)

    _order = 'start_date desc'

    def _select(self):
        select_str = """
            select 
            rc.id,rc.partner_id,o.partner_id as advocate_id,rp.lang,activation_date,rc.start_date,
            case 
                when extract(month from(rc.activation_date))>6
                then extract(month from(rc.activation_date))-6
                else extract(month from(rc.activation_date))+6
            end as paid_month, 
            case 
                when extract(month from(rc.activation_date))>6 
                then extract(year from(rc.activation_date)) +1 
                else extract(year from(rc.activation_date)) 
            end as fy ,
            case 
                when extract(month from(rc.start_date))>6
                then extract(month from(rc.start_date))-6
                else extract(month from(rc.start_date))+6
            end as aquisition_month,
            case 
                when extract(month from(rc.start_date))>6
                then extract(month from(rc.start_date))-6
                else extract(month from(rc.start_date))+6
            end as aquisition_month_int, 
            case 
                when extract(month from(rc.start_date))>6 
                then extract(year from(rc.start_date)) +1 
                else extract(year from(rc.start_date))
            end as aquisition_fy ,
            rc.state,rc.end_reason,rc.end_date,
            case 
                when extract(month from(rc.end_date))>6
                then extract(month from(rc.end_date))-6
                else extract(month from(rc.end_date))+6
            end as departure_month, 
            case 
                when extract(month from(rc.end_date))>6
                then extract(month from(rc.end_date))-6
                else extract(month from(rc.end_date))+6
            end as departure_fy ,
            rc.origin_id ,o.type as origin_type,
            e.name as event_name, e.type as event_type
        """
        return select_str


    def _from(self):
        from_str = """
            recurring_contract rc
            left join res_partner rp on rp.id=rc.partner_id
            left join recurring_contract_origin o on o.id=rc.origin_id
            left join crm_event_compassion e on e.id=o.event_id
        """
        return from_str

    def _group_by(self):
        group_by_str = """
        """
        return group_by_str

    def init(self,cr):
        # self._table = sponsorship_contract_report
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM 
            %s 
            where rc.type in ('SC','S')
            %s
        )""" % (
                    self._table, self._select(), self._from(), self._group_by()))