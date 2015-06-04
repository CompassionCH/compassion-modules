# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Kevin Cristi, Emanuel Cino, David Coninckx
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, fields, api, exceptions, _
from project_description_fr import Project_description_fr
from project_description_de import Project_description_de
from project_description_it import Project_description_it
import re


class project_description_wizard(models.TransientModel):
    _name = 'project.description.wizard'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    project_id = fields.Many2one(
        'compassion.project', 'Project code',
        default=lambda self: self._get_project_id())
    # Complete descriptions
    keep_desc_fr = fields.Boolean('Update french description')
    keep_desc_de = fields.Boolean('Update german description')
    keep_desc_it = fields.Boolean('Update italian description')
    desc_fr = fields.Html(
        'French description', default=lambda self: self._get_desc('fr'))
    desc_de = fields.Html(
        'German description', default=lambda self: self._get_desc('de'))
    desc_it = fields.Html(
        'Italian description', default=lambda self: self._get_desc('it'))
    desc_en = fields.Text(
        'English description', default=lambda self: self._get_desc('en'))
    # Needs descriptions
    needs_desc_fr = fields.Text(
        'French needs description',
        default=lambda self: self._get_needs('fr'))
    needs_desc_de = fields.Text(
        'German needs description',
        default=lambda self: self._get_needs('de'))
    needs_desc_it = fields.Text(
        'Italian needs description',
        default=lambda self: self._get_needs('it'))
    project_property_value_ids = fields.Many2many(
        'compassion.translated.value',
        compute='_set_value_ids', default=lambda self: self._set_value_ids(),
        inverse='_write_values')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _get_project_id(self):
        # Retrieve the id of the project from context
        return self.env.context.get('active_id', False)

    def _set_value_ids(self):
        project_id = self.env.context.get('active_id')
        if not project_id:
            return False

        query = '''SELECT rel.value_id
                   FROM project_property_to_value as rel,
                        compassion_translated_value as val
                   WHERE rel.project_id = %s
                   AND rel.value_id = val.id
                   AND val.is_tag = false
                   ORDER BY val.value_en, val.property_name''' % project_id
        self.env.cr.execute(query)
        value_ids = [x[0] for x in self.env.cr.fetchall()]
        self.write({'project_property_value_ids': [(6, 0, value_ids)]})
        return value_ids

    def _write_values(self):
        # Values are automatically propagated into related objects
        return True

    def _get_needs(self, lang):
        """ Returns the needs descrption of the given language.
        It will either generate it from a pattern or retrieve the
        last saved description if one exist. """
        project = self.env['compassion.project'].browse(
            self.env.context.get('active_id'))
        res = False
        if lang == 'fr':
            res = project.needs_fr or \
                Project_description_fr._get_needs_pattern_fr(project)
        elif lang == 'de':
            res = project.needs_de or \
                Project_description_de._get_needs_pattern_de(project)
        elif lang == 'it':
            res = project.needs_it or \
                Project_description_it._get_needs_pattern_it(project)

        return res + '\n\n'     # Fix for display of the textfield

    def _get_desc(self, lang):
        project = self.env['compassion.project'].browse(
            self.env.context.get('active_id'))
        res = False
        if lang == 'fr':
            res = Project_description_fr.gen_fr_translation(project)
        elif lang == 'de':
            res = Project_description_de.gen_de_translation(project)
        elif lang == 'it':
            res = Project_description_it.gen_it_translation(project)
        elif lang == 'en':
            res = project.description_en

        return res + '\n\n'     # Fix for display of the textfield

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def generate_descriptions(self):
        self.ensure_one()
        project = self.project_id

        desc_fr = Project_description_fr.gen_fr_translation(
            project)
        desc_de = Project_description_de.gen_de_translation(
            project)
        desc_it = Project_description_it.gen_it_translation(
            project)

        self.write({
            'desc_fr': desc_fr,
            'desc_de': desc_de,
            'desc_it': desc_it,
            'desc_en': self.desc_en,
        })

        return {
            'name': _('Descriptions generation'),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'auto_description_form',
            'view_type': 'form',
            'target': 'new',
        }

    @api.multi
    def validate_descriptions(self):
        """ Save the selected descriptions in the project. """
        self.ensure_one()
        vals = dict()
        p = re.compile(r'<.*?>')  # Remove HTML markers
        if self.keep_desc_fr:
            vals['description_fr'] = p.sub('', self.desc_fr +
                                           self.needs_desc_fr.strip('\n'))
            vals['needs_fr'] = self.needs_desc_fr
        if self.keep_desc_de:
            vals['description_de'] = p.sub('', self.desc_de +
                                           self.needs_desc_de.strip('\n'))
            vals['needs_de'] = self.needs_desc_de
        if self.keep_desc_it:
            vals['description_it'] = p.sub('', self.desc_it +
                                           self.needs_desc_it.strip('\n'))
            vals['needs_it'] = self.needs_desc_it

        if not vals:
            raise exceptions.Warning(
                'ValueError',
                _('No description selected. Please select one or click cancel'
                  ' to abort current task.'))
        self.project_id.write(vals)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
