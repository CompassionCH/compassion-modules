# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Kevin Cristi, Emanuel Cino
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import requests
import json
import pdb

from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.tools.config import config
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime
from dateutil.relativedelta import relativedelta

class compassion_project(orm.Model):
    """ A compassion project """
    _name = 'compassion.project'

    def _get_suspension_state(self, cr, uid, ids, field_name, args,
                              context=None):
        res = dict()

        for project in self.browse(cr, uid, ids, context):
            res[project.id] = 'none'
            if project.status == 'A' and not (
               project.disburse_gifts and project.disburse_funds and
               project.disburse_unsponsored_funds and
               project.new_sponsorships_allowed and
               project.additional_quota_allowed):
                res[project.id] = 'suspended' if project.disburse_funds \
                    else 'fund-suspended'
                if (res[project.id] == 'fund-suspended'): 
                    self.suspend_project(cr, uid, project.id, project.status_date, 3, context)
        return res

    def suspend_project(self, cr, uid, project_id, start, months,
                                context=None):
        """ When a project is suspended from GP, We update all contracts of
        sponsored children in the project, so that we don't create invoices
        during the period of suspension.
        """
        date_start = datetime.strptime(start, DF)
        date_end = date_start + relativedelta(months=months)
        project = self.browse(cr, uid, project_id, context)
        contract_obj = self.pool.get('recurring.contract')
        contract_ids = contract_obj.search(
            cr, uid, [('child_code', 'like', project.code),
                      ('state', 'in', ('active', 'waiting'))], context=context)
        invl_obj = self.pool.get('account.invoice.line')
        inv_line_ids = invl_obj.search(cr, uid, [
            ('contract_id', 'in', contract_ids),
            ('state', 'in', ('open', 'paid')),
            ('due_date', '>=', date_start.strftime(DF)),
            ('due_date', '<', date_end.strftime(DF))], context=context)
        inv_ids = set()
        # Cancel invoices in the period of suspension
        for inv_line in invl_obj.browse(cr, uid, inv_line_ids, context):
            invoice = inv_line.invoice_id
            if invoice.id not in inv_ids:
                inv_ids.add(invoice.id)
                if invoice.state == 'paid':
                    # Unreconcile entries
                    move_ids = [move.id for move in invoice.payment_ids]
                    self.pool.get('account.move.line')._remove_move_reconcile(
                        cr, uid, move_ids, context=context)
                    cr.commit()
                # Cancel invoice
                wf_service = netsvc.LocalService('workflow')
                wf_service.trg_validate(uid, 'account.invoice', invoice.id,
                                        'invoice_cancel', cr)
        # Advance next invoice date after end of suspension
        for contract in contract_obj.browse(cr, uid, contract_ids, context):
            next_inv_date = datetime.strptime(contract.next_invoice_date, DF)
            month_diff = relativedelta(date_end, next_inv_date).months
            if month_diff > 0:
                # If sponsorship is late, don't advance it too much
                if month_diff > months:
                    month_diff = months
                new_date = next_inv_date + relativedelta(months=month_diff)
                contract.write({'next_invoice_date': new_date.strftime(DF)})

            # Add a note in the contract
            self.pool.get('mail.thread').message_post(
                cr, uid, contract.id,
                "The project {0} was suspended and funds are retained <b>"
                "until {1}</b>.<br/>Invoices due in the suspension period "
                "are automatically cancelled.".format(
                    project.code, date_end.strftime("%B %Y")),
                "Project Suspended", 'comment',
                context={'thread_model': 'recurring.contract'})

        return True    
        
    _columns = {
        ######################################################################
        #                      1. General Information                        #
        ######################################################################
        'name': fields.char(_("Name"), size=128, required=True),
        'code': fields.char(_("Project code"), size=128, required=True),
        'country_id': fields.many2one('compassion.country', _('Country')),
        'type': fields.selection([
            ('CDSP', 'CDSP'),
            ('CSP', 'CSP')], _('Program type')),
        'start_date': fields.date(_('Partnership begining')),
        'stop_date': fields.date(_('Partnership ending')),
        'last_update_date': fields.date(_('Last update')),
        'suspension': fields.function(
            _get_suspension_state, type='selection', selection=[
                ('none', _('Not Suspended')),
                ('suspended', _('Suspended')),
                ('fund-suspended', _('Suspended & fund retained'))],
            string=_('Suspension'), 
            store=
            {'compassion.project': 
                (lambda self, cr, uid, ids, c={}:
                    ids, ['last_update_date'], 20)}
                    ),
        'status': fields.selection([
            ('A', _('Active')),
            ('P', _('Phase-out')),
            ('T', _('Terminated'))], _('Status')),
        'status_date': fields.date(_('Last status change')),
        'status_comment': fields.char(_('Status comment')),
        'disburse_funds': fields.boolean(_('Disburse funds')),
        'disburse_gifts': fields.boolean(_('Disburse gifts')),
        'disburse_unsponsored_funds': fields.boolean(_('Disburse unsponsored '
                                                       'funds')),
        'new_sponsorships_allowed': fields.boolean(_('New sponsorships '
                                                     'allowed')),
        'additional_quota_allowed': fields.boolean(_('Additional quota '
                                                     'allowed')),

        ######################################################################
        #                      2. Project Descriptions                       #
        ######################################################################
        'description_en': fields.text(_('English description')),
        'description_fr': fields.text(_('French description')),
        'description_de': fields.text(_('German description')),
        'description_it': fields.text(_('Italian description')),

        'needs_fr': fields.text(_('French needs')),
        'needs_de': fields.text(_('German needs')),
        'needs_it': fields.text(_('Italian needs')),

        ######################################################################
        #                      3. Community Information                      #
        ######################################################################
        'local_church_name': fields.char(_('Local church name')),
        'hiv_category': fields.selection([
            ('AFFCTD', _('Affected')),
            ('NOTAFF', _('Not affected'))],
            _('HIV/Aids category for project area')),
        'month_school_year_begins': fields.selection([
            ('1', _('January')), ('2', _('February')), ('3', _('March')),
            ('4', _('April')), ('5', _('May')), ('6', _('June')),
            ('7', _('July')), ('8', _('August')), ('9', _('September')),
            ('10', _('October')), ('11', _('November')), ('12', _('December'))
            ], _('Month school begins each year')),
        'country_denomination': fields.char(_('Local denomination')),
        'western_denomination': fields.char(_('Western denomination')),
        'community_name': fields.char(_('Community name')),
        'country_common_name': fields.text(_('Country common name')),

        ######################################################################
        #                    4. Miscellaneous Information
        #                       (retrieved from community API)
        ######################################################################
        # a. Automatic translated values
        'floor_material_ids': fields.many2many(
            'compassion.translated.value', 'project_property_to_value',
            'project_id', 'value_id', _('Floor material'),
            domain=[('property_name', '=', 'floor_material')]),
        'wall_material_ids': fields.many2many(
            'compassion.translated.value', 'project_property_to_value',
            'project_id', 'value_id', _('Wall material'),
            domain=[('property_name', '=', 'wall_material')]),
        'roof_material_ids': fields.many2many(
            'compassion.translated.value', 'project_property_to_value',
            'project_id', 'value_id', _('Roof material'),
            domain=[('property_name', '=', 'roof_material')]),
        'spoken_languages_ids': fields.many2many(
            'compassion.translated.value', 'project_property_to_value',
            'project_id', 'value_id', _('Spoken languages'),
            domain=[('property_name', '=', 'spoken_languages')]),
        'primary_diet_ids': fields.many2many(
            'compassion.translated.value', 'project_property_to_value',
            'project_id', 'value_id', _('Primary diet'),
            domain=[('property_name', '=', 'primary_diet')]),
        'health_problems_ids': fields.many2many(
            'compassion.translated.value', 'project_property_to_value',
            'project_id', 'value_id', _('Health problems'),
            domain=[('property_name', '=', 'health_problems')]),
        'primary_occupation_ids': fields.many2many(
            'compassion.translated.value', 'project_property_to_value',
            'project_id', 'value_id', _('Primary occupation'),
            domain=[('property_name', '=', 'primary_occupation')]),
        'terrain_description_ids': fields.many2many(
            'compassion.translated.value', 'project_property_to_value',
            'project_id', 'value_id', _('Terrain description'),
            domain=[('property_name', '=', 'terrain_description')]),
        # b. Static Values
        'gps_latitude': fields.float(_('GPS latitude')),
        'gps_longitude': fields.float(_('GPS longitude')),
        'unemployment_rate': fields.float(_('Unemployment rate')),
        'closest_city': fields.char(_('Closest city')),
        'community_population': fields.integer(_('Community population')),
        'monthly_income': fields.float(_('Monthly income')),
        # c. Non translated text
        'economic_needs': fields.text(_('Economic needs')),
        'education_needs': fields.text(_('Education needs')),
        'social_needs': fields.text(_('Social needs')),
        'spiritual_needs': fields.text(_('Spiritual needs')),
        'distance_from_closest_city': fields.text(_('Distance from closest '
                                                    'city')),
        # d. Age groups section
        'age_group_ids': fields.one2many(
            'compassion.project.age.group', 'project_id',
            _('Age group'),
            readonly=True, track_visibility="onchange"),
        }

    def update_informations(self, cr, uid, ids, context=None):
        """ Get the most recent informations for selected projects and update
            them accordingly. """
        if not isinstance(ids, list):
            ids = [ids]
        for project in self.browse(cr, uid, ids, context):
            self._get_age_groups(cr, uid, project, context)
            values, community_id = self._update_program_info(
                cr, uid, project, context)
            values.update(
                self._update_community_info(cr, uid, community_id, context))
            if values['type'] == 'CDSP':
                values.update(self._update_cdsp_info(cr, uid,
                                                     project.code, context))
            self.write(cr, uid, [project.id], values, context=context)
        return True

    def _update_program_info(self, cr, uid, project, context=None):
        """ Calls the "ProgramImplementors" REST API.
            Returns the information in a dictionary of the form
            {'field_name': 'value'}, and the community_id used
            to call the GetCommunity API.
            See http://developer.compassion.com/docs/read/
                private_cornerstone_test/REST_Get_Program_Implementor
            for more information.
        """
        prog_impl = self._cornerstone_fetch(project.code,
                                            'programimplementors')
        values = {
            'type': prog_impl.get('programImplementorTypeCode'),
            'local_church_name': prog_impl.get('organizationName'),
            'hiv_category': prog_impl.get('hIVCategory'),
            'month_school_year_begins': prog_impl.get(
                'monthSchoolYearBegins'),
            'country_denomination': prog_impl.get('countryDenomination'),
            'western_denomination': prog_impl.get('westernDenomination'),
            'community_name': prog_impl.get('communityName'),
            'country_id': self._update_country(
                cr, uid, prog_impl.get('isoCountryCode'), context),
            'country_common_name': prog_impl.get('countryCommonName'),
        }
        community_id = prog_impl.get('communityID')
        return {field_name: value for field_name, value in values.iteritems()
                if value}, community_id

    def generate_descriptions(self, cr, uid, project_id, context=None):
        return {
            'name': _('Description generation'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'project.description.wizard',
            'context': context,
            'target': 'new',
        }

    def _update_country(self, cr, uid, country_code, context=None):
        """ Finds the country having the given country_code or
            creates one.
            Returns the country_id of the country object.
        """
        country_obj = self.pool.get('compassion.country')
        country_ids = country_obj.search(
            cr, uid, [('iso_code', '=', country_code)], context=context)
        if country_ids:
            country_id = country_ids[0]
        else:
            country_id = country_obj.create(
                cr, uid, {'iso_code': country_code}, context=context)
            country_obj.update_informations(cr, uid, [country_id], context)
        return country_id

    def _get_age_groups(self, cr, uid, project, context=None):
        """ Get age group from compassion webservice and l
            Returns ids of generated age_groups or None if failed """
        # Delete old age_groups
        for age_group in project.age_group_ids:
            project.write({'age_group_ids': [(2, age_group.id)]})
        json_data = self._cornerstone_fetch(project.code + '/agegroups',
                                            'cdspimplementors')
        value_obj = self.pool.get('compassion.translated.value')
        age_project_obj = self.pool.get('compassion.project.age.group')
        for group in json_data['projectAgeGroupCollection']:
            values = list()
            vals = {
                'project_id': project.id,
                'low_age': group['lowAge'],
                'high_age': group['highAge'],
                'school_hours': group['schoolHours'],
            }
            values.extend(value_obj.get_value_ids(
                cr, uid, group['schoolDays'].split(','),
                'school_days', context))
            values.extend(value_obj.get_value_ids(
                cr, uid, group['schoolMonths'].split(','),
                'school_months', context))

            vals['school_days_ids'] = [(6, 0, [v for v in values if v])]
            age_project_obj.create(cr, uid, vals, context)
        return True

    def _update_community_info(self, cr, uid, community_id, context=None):
        """ Call the "REST Get Community" API from Compassion.
        See http://developer.compassion.com/docs/read/
            private_cornerstone_test/REST_Get_Community for more information.
        Returns: the information in a dictionary of the form
                 {'field_name': 'value'}
        """
        # Standard fields retrieval
        json_values = self._cornerstone_fetch(community_id, 'communities')
        values = {
            'unemployment_rate': json_values['unemploymentRate'],
            'community_population': json_values['communityPopulation'],
            'monthly_income': json_values['familyMonthlyIncome'],
            'economic_needs': json_values['economicNeeds'],
            'education_needs': json_values['educationalNeeds'],
            'social_needs': json_values['socialNeeds'],
            'spiritual_needs': json_values['spiritualNeeds'],
            'closest_city': json_values['closestCityName'],
            'distance_from_closest_city': json_values['distanceFrom'
                                                      'ClosestCity'],
        }

        # Automatic translated fields retrieval
        # Dictionary key -> JSON field name;
        # Dictionary value -> (Odoo field name, separator between values)
        json_misc_tags = {
            'terrainDescription': ('terrain_description', '/'),
            'typicalFloorBuildingMaterialDescription': ('floor_material', '/'),
            'typicalWallBuildingMaterialDescription': ('wall_material', '/'),
            'typicalRoofBuildingMaterialDescription': ('roof_material', '/'),
            'primaryEthnicGroup': ('spoken_languages', ', '),
            'primaryDiet': ('primary_diet', ','),
            'commonHealthProblems': ('health_problems', ', '),
            'primaryOccupationTitle': ('primary_occupation', '/'),
        }

        # Get the property values ids
        # (ids of 'compassion.translated.value' objects)
        multi_value = []
        value_obj = self.pool.get('compassion.translated.value')
        for json_key, field_tuple in json_misc_tags.iteritems():
            field_name = field_tuple[0]
            separator = field_tuple[1]

            multi_value.extend(value_obj.get_value_ids(cr, uid,
                               json_values[json_key].split(separator),
                               field_name, context))

        """ Only one field need to get all the many2many relations.
        Then all other fields will get their correct values
        because of the domain set on the property_name.
        This is because there is only one physical underlying
        many2many relation.
        [(6, 0, [ids])] is a standard way to set a many2many field in Odoo.
        """
        values['primary_diet_ids'] = [(6, 0, [v for v in multi_value if v])]

        return {field_name: value for field_name, value in values.iteritems()
                if value}

    def _update_cdsp_info(self, cr, uid, project_code, context=None):
        """ Call the "REST Get CDSP" API from Compassion.
        See http://developer.compassion.com/docs/read/
            private_cornerstone_test/Get_CDSP_Implementor
            for more information.
        Returns: the information in a dictionary of the form
                 {'field_name': 'value'}
        """
        json_values = self._cornerstone_fetch(project_code, 'cdspimplementors')
        values = {
            'name': json_values.get('name'),
            'start_date': json_values.get('startDate'),
            'stop_date': json_values.get('stopDate'),
            'last_update_date': json_values.get('lastUpdateDate'),
            'status': json_values.get('status'),
            'status_date': json_values.get('statusDate'),
            'status_comment': json_values.get('statusComment'),
            'description_en': json_values.get('description'),
            'gps_latitude': json_values.get(
                'gPSCoordinateLatitudeHighPrecision'),
            'gps_longitude': json_values.get(
                'gPSCoordinateLongitudeHighPrecision'),
            'disburse_funds': json_values.get('disburseFunds'),
            'disburse_gifts': json_values.get('disburseGifts'),
            'disburse_unsponsored_funds': json_values.get(
                'disburseUnsponsoredFunds'),
            'new_sponsorships_allowed': json_values.get(
                'newSponsorshipsAllowed'),
            'additional_quota_allowed': json_values.get(
                'additionalQuotaAllowed'),
        }
        return {field_name: value for field_name, value in values.iteritems()
                if value}

    def _cornerstone_fetch(self, project_code, api_mess):
        """ Construct the correct URL to call Compassion Cornerstone APIs.
        Returns the JSON object of the response."""
        url = config.get('compass_url')
        api_key = config.get('compass_api_key')
        if not url or not api_key:
            raise orm.except_orm('ConfigError',
                                 _('Missing compass_url or compass_api_key '
                                   'in conf file'))
        if url.endswith('/'):
            url = url[:-1]

        url += ('/ci/v1/' + api_mess + '/' + project_code + '?api_key='
                + api_key)

        # Send the request and retrieve the result.
        r = requests.get(url)
        if not r.status_code == 200:
            raise orm.except_orm(
                _('Error calling Cornerstone Service'),
                r.text)
        json_result = json.loads(r.text)
        return json_result
        