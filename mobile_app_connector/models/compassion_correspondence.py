# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api, fields
from ..mappings.compassion_correspondence_mapping import \
    MobileCorrespondenceMapping, FromLetterMapping
from werkzeug.exceptions import NotFound

from datetime import date, timedelta


class CompassionCorrespondence(models.Model):
    _inherit = 'correspondence'

    @api.multi
    def get_app_json(self, multi=False):
        """
        Called by HUB when data is needed for a tile
        :param multi: used to change the wrapper if needed
        :return: dictionary with JSON data of the children
        """
        child = self.sudo().mapped('child_id')
        if not self:
            return {}
        mapping = FromLetterMapping(self.env)
        wrapper = 'Letters' if multi else 'Letter'
        if len(self) == 1:
            data = mapping.get_connect_data(self)
        else:
            data = []
            for letter in self:
                data.append(mapping.get_connect_data(letter))
        unread_recently = not(self.email_read and self.email_read <
                              fields.Date.to_string(
                                  date.today() + timedelta(days=3)))
        return {
            'Child': child.get_app_json_no_wrap(),
            wrapper: data,
            'OrderDate': self.sent_date or self.status_date,
            'UnReadRecently': unread_recently,
            }

    @api.model
    def mobile_post_letter(self, json_data, **parameters):
        """
            Mobile app method:
            POST a letter between a child and a sponsor

            :param parameters: all request parameters
            :return: sample response
        """
        # Validate required parameters
        self._validate_required_fields([
            'TemplateID',
            'Message',
            'Need',
            'supporterId',
            'base64string'
            ], json_data)
        mapping = MobileCorrespondenceMapping(self.env)
        vals = mapping.get_vals_from_connect(json_data)
        letter = self.env['correspondence'].create(vals)

        if letter:
            return "Letter Submitted"
        else:
            return "Letter could not be created and was not submitted"

    @api.model
    def mobile_get_letters(self, **other_params):
        """
        Mobile app method:
        Returns all the letters from a Child
        :param needid: beneficiary id
        :param supgrpid: sponsor id
        """
        partner_id = self._get_required_param('supgrpid', other_params)
        child_id = self._get_required_param('needid', other_params)
        letters = self.search([
            ('partner_id', '=', int(partner_id)),
            ('child_id', '=', int(child_id)),
            ('direction', '=', 'Beneficiary To Supporter')
        ])

        mapper = FromLetterMapping(self.env)
        return [mapper.get_connect_data(letter) for letter in letters]

    @api.model
    def mobile_letter_pdf(self, **other_params):
        host = self.env['ir.config_parameter'].get_param('web.external.url')
        letter_id = other_params.get('correspondenceid')
        if letter_id:
            letter = self.browse(int(letter_id))
            if letter.exists() and letter.letter_image:
                return host + "/b2s_image?id=" + letter.uuid
        raise NotFound("Letter with id {} not found".format(letter_id))

    def _validate_required_fields(self, fields, params):
        missing = [key for key in fields if key not in params]
        if missing:
            raise ValueError(
                'Required parameters {}'.format(','.join(missing)))

    def _get_required_param(self, key, params):
        if key not in params:
            raise ValueError('Required parameter {}'.format(key))
        return params[key]
