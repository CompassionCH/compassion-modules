# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging
from odoo import api, models, _, fields
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

try:
    import regex as re
    from pyquery import PyQuery
    from bs4 import BeautifulSoup
except ImportError:
    _logger.warning("Please install python pyquery, regex and bs4")


def safe_replace(original, to_replace, replacement):
    """
    Utility that will replace the string except in the HTML tag attributes
    :param original: original string
    :param to_replace: string to replace
    :param replacement: replacement string
    :return: new string with the replacement done
    """
    def _replace(match):
        if match.group(1):
            return match.group(0)
        else:
            return replacement
    replace_regex = re.escape(to_replace.replace('\\', ''))
    in_attr = r'((?:<[^<>]*?"[^<>]*?){1}' + replace_regex + \
        r'(?:[^<>]*?"[^<>]*?>){1})'
    regex = in_attr + r'|(' + replace_regex + r')'
    return re.sub(regex, _replace, original)


class CommunicationRevision(models.Model):
    _name = 'partner.communication.revision'
    _inherit = 'mail.thread'
    _rec_name = 'config_id'
    _description = 'Communication template revision'
    _order = 'config_id asc,revision_number desc'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    config_id = fields.Many2one(
        'partner.communication.config',
        'Communication type',
        required=True,
        ondelete='cascade'
    )
    model = fields.Char(related='config_id.model_id.model', readonly=True)
    lang = fields.Selection('select_lang', required=True)
    revision_number = fields.Float(default=1.0)
    revision_date = fields.Date(default=fields.Date.today())
    state = fields.Selection([
        ('pending', 'Pending'),
        ('submit', 'Submitted'),
        ('corrected', 'Corrected'),
        ('approved', 'Approved'),
        ('active', 'Active'),
    ], default='active')
    is_master_version = fields.Boolean()
    subject = fields.Char()
    subject_correction = fields.Char()
    body_html = fields.Html(related='config_id.email_template_id.body_html')
    raw_template_edit_mode = fields.Boolean()
    simplified_text = fields.Html(sanitize=False)
    user_id = fields.Many2one('res.users', 'Responsible', domain=[
        ('share', '=', False)], track_visibility='onchange')
    correction_user_id = fields.Many2one('res.users', 'Corrector', domain=[
        ('share', '=', False)], track_visibility='onchange')
    update_user_id = fields.Many2one('res.users', 'Modified by')
    proposition_text = fields.Html()
    proposition_correction = fields.Html()
    compare_lang = fields.Selection('select_lang')
    compare_text = fields.Html()
    compare_subject = fields.Char()
    preview_text = fields.Html()
    keyword_ids = fields.One2many(
        'partner.communication.keyword', 'revision_id', 'Keywords'
    )
    show_all_keywords = fields.Boolean()
    edit_keyword_ids = fields.One2many(
        'partner.communication.keyword',
        compute='_compute_keyword_ids', inverse='_inverse_keyword_ids',
        string='Keywords'
    )
    if_keyword_ids = fields.One2many(
        'partner.communication.keyword',
        compute='_compute_keyword_ids', inverse='_inverse_keyword_ids',
        string='Conditional text'
    )
    for_keyword_ids = fields.One2many(
        'partner.communication.keyword',
        compute='_compute_keyword_ids', inverse='_inverse_keyword_ids',
        string='Loops'
    )
    is_proposer = fields.Boolean(compute='_compute_allowed')
    is_corrector = fields.Boolean(compute='_compute_allowed')
    display_name = fields.Char(compute='_compute_display_name')

    _sql_constraints = [
        ('unique_revision', 'unique(config_id,lang)',
         'You can only have one revision per language'),
    ]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def select_lang(self):
        langs = self.env['res.lang'].search([])
        config_id = self.env.context.get('config_id')
        valid_langs = None
        if config_id:
            revisions = self.config_id.browse(config_id).revision_ids.filtered(
                lambda r: r.state in ('approved', 'active'))
            valid_langs = revisions.mapped('lang')
        return [(lang.code, lang.name) for lang in langs if
                not config_id or lang.code in valid_langs]

    @api.multi
    def _compute_keyword_ids(self):
        for revision in self:
            revision.edit_keyword_ids = revision.keyword_ids.filtered(
                lambda k: (
                    (revision.show_all_keywords and k.type in ('code', 'var'))
                    or k.type == 'code'
                ) and (revision.show_all_keywords or k.is_visible))
            revision.if_keyword_ids = revision.keyword_ids.filtered(
                lambda k: k.type == 'if' and (revision.show_all_keywords or
                                              k.is_visible))
            revision.for_keyword_ids = revision.keyword_ids.filtered(
                lambda k: 'for' in k.type and (revision.show_all_keywords or
                                               k.is_visible))

    @api.multi
    def _inverse_keyword_ids(self):
        return True

    @api.constrains('correction_user_id')
    def _check_corrector(self):
        for rev in self:
            if rev.correction_user_id and \
                    rev.correction_user_id == rev.user_id:
                raise ValidationError(_(
                    "Corrector cannot be the same person as the one making "
                    "the new version."))
        return True

    @api.multi
    def _compute_allowed(self):
        user = self.env.user
        admin = self.env.ref('base.group_erp_manager') in user.groups_id
        for rev in self:
            rev.is_proposer = user == rev.user_id or admin
            rev.is_corrector = user == rev.correction_user_id or admin

    @api.multi
    def _compute_display_name(self):
        for rev in self:
            rev.display_name = rev.config_id.name + ' - ' + \
                rev.lang.upper()[:2]

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.multi
    def write(self, vals):
        """
        Push back the enhanced text in translation of the mail.template.
        Update revision date and number depending on edit mode.
        """
        if 'correction_user_id' in vals:
            self.message_subscribe_users([vals['correction_user_id']])

        if 'simplified_text' not in vals or self.env.context.get('no_update'):
            return super(CommunicationRevision, self).write(vals)

        for revision in self.filtered('simplified_text'):
            vals['update_user_id'] = self.env.uid
            super(CommunicationRevision, revision).write(vals)

            # 2. Push back the template text
            # Set the conditionals texts
            revision.with_context(save_mode=True).refresh_text()
            revision.config_id.email_template_id.with_context(
                lang=revision.lang).body_html = revision._enhance_text()
        return True

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def edit_revision(self):
        """
        View helper to open a revision in edit mode.
        This will increment a small step in the
        revision number but not change the revision date.
        :return: action window
        """
        self.ensure_one()
        new_revision_number = self.revision_number + 0.01
        self.revision_number = new_revision_number
        self.revision_date = fields.Date.today()
        return self._open_revision()

    @api.multi
    def new_revision(self):
        """
        View helper to open a revision in edit mode.
        This will increase the revision number and the date meaning we will
        modify the text model more than just a few corrections.
        :return: action window
        """
        self.ensure_one()
        this_revision_number = self.revision_number + 1.0
        current_revision_number = self.config_id.revision_number
        new_revision_number = max([
            this_revision_number, current_revision_number])
        revision_vals = {
            'revision_number': int(new_revision_number),
            'revision_date': fields.Date.today(),
            'state': 'active'
        }
        if new_revision_number > current_revision_number:
            self.config_id.write(revision_vals)
        self.write(revision_vals)
        return self._open_revision()

    @api.multi
    def edit_proposition(self):
        """ This is used to open the revision proposition text. """
        self.ensure_one()
        return self._open_revision(form_view_mode='proposition')

    @api.multi
    def show_revision(self):
        self.ensure_one()
        return self._open_revision(form_view_mode='readonly')

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def refresh_text(self):
        """
        Save the current text in the if clause and refresh the selected
        clauses.
        """
        text = PyQuery(self.simplified_text)
        for key in self.keyword_ids.filtered(
                lambda k: k.type in ('if', 'for', 'for_ul')):
            text_selector = text('#' + key.html_id)
            current_text = text_selector.html()
            # Save the current text in the correct if clause
            if key.edit_changed % 2 == 0:
                edit_value = key.edit_value
            else:
                edit_value = not key.edit_value
            if current_text is not None:
                key.set_text(current_text, edit_value)
            if key.edit_changed and not self._context.get('save_mode'):
                # Now we fetch the current clause text
                text_selector.html(key.get_text())
                key.write({'edit_changed': 0})
        self.with_context(no_update=True).simplified_text = text.html()
        return True

    @api.multi
    def open_preview(self):
        preview_model = 'partner.communication.revision.preview'
        working_mode = self._context.get('working_revision')
        context = {
            'revision_id': self.id,
            'lang': self.lang,
        }
        if working_mode:
            # The preview is from the revision edition mode, we fetch the
            # working texts.
            context['working_text'] = self.proposition_text
            context['working_subject'] = self.subject

            if self.state == 'submit':
                context['working_text'] = self.proposition_correction
                context['working_subject'] = self.subject_correction
        preview = self.env[preview_model].with_context(context).create({
            'revision_id': self.id,
            'state': 'working_revision' if working_mode else 'active_revision'
        })
        preview.preview()
        return {
            'name': 'Preview',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': preview_model,
            'res_id': preview.id,
            'context': self.with_context(context).env.context,
            'target': 'new',
        }

    # Revision proposition buttons
    @api.multi
    def submit_proposition(self):
        return self._open_submit_text_wizard()

    @api.multi
    def validate_proposition(self):
        subject = '[{}] Revision approved'.format(self.display_name)
        body = 'The text for {} was approved.'.format(self.display_name)
        if not self.is_master_version:
            self.approve(subject, body)
        return self.with_context(body=body, subject=subject)._open_validation()

    @api.multi
    def submit_correction(self):
        return self._open_submit_text_wizard()

    def _open_submit_text_wizard(self):
        return {
            'name': 'Submit text',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'partner.communication.submit.revision',
            'context': self.with_context(
                active_id=self.id, form_view_ref=False,
                config_id=False).env.context,
            'target': 'new',
        }

    @api.multi
    def validate_correction(self):
        self.write({
            'proposition_text': self.proposition_correction,
            'subject': self.subject_correction
        })
        body = 'The text for {} was approved.'.format(self.display_name)
        subject = '[{}] Corrections approved'.format(self.display_name)
        if not self.is_master_version:
            self.approve(subject, body)

        return self.with_context(body=body, subject=subject)._open_validation()

    @api.multi
    def edit_correction(self):
        return self.write({
            'state': 'pending',
            'proposition_text': self.proposition_correction,
            'proposition_correction': False
        })

    @api.multi
    def discard_correction(self):
        return self.write({
            'state': 'pending',
            'proposition_correction': False
        })

    @api.multi
    def approve(self, subject=None, body=None):
        self.write({
            'proposition_correction': False,
            'subject_correction': False,
            'state': 'approved',
            'compare_text': False,
            'compare_subject': False,
        })
        subject = self._context.get('subject', subject)
        body = self._context.get('body', body)
        self.notify_proposition(subject, body)

    @api.multi
    def notify_proposition(self, subject, body):
        # Post a message that is sent to watchers
        self.message_post(
            body=body, subject=subject, type='comment',
            subtype='mail.mt_comment', content_subtype='plaintext'
        )

    @api.multi
    def cancel_approve(self):
        """ Set back a text approved in revision mode. """
        return {
            'name': 'Cancel proposition',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'partner.communication.cancel.proposition',
            'context': self.with_context(
                active_id=self.id, form_view_ref=False,
                config_id=False).env.context,
            'target': 'new',
        }

    @api.onchange('compare_lang')
    def onchange_compare_lang(self):
        master = self.search([
            ('config_id', '=', self.config_id.id),
            ('lang', '=', self.compare_lang),
            ('state', 'in', ('approved', 'active'))
        ])
        self.compare_text = master.proposition_text
        self.compare_subject = master.subject
        self._origin.write({
            'compare_text': master.proposition_text,
            'compare_subject': master.subject
        })

    @api.multi
    def open_translation_view(self):
        # Trick to avoid overriding raw template text changes
        self.raw_template_edit_mode = True
        return self.config_id.open_translation_view()

    @api.multi
    def reload_text(self):
        text = self.with_context(lang=self.lang).body_html
        self.raw_template_edit_mode = False
        self.with_context(
            no_update=True).simplified_text = self._simplify_text(text)

    @api.multi
    def toggle_all_keywords(self):
        for record in self:
            record.show_all_keywords = not record.show_all_keywords
        return True

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.multi
    def _open_validation(self):
        # After master version is approved, we must setup the translations
        if self.is_master_version:
            return {
                'name': 'Validate proposition',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'partner.communication.validate.proposition',
                'context': self.with_context(
                    active_id=self.id, form_view_ref=False,
                    config_id=False).env.context,
                'target': 'new',
            }
        return True

    @api.multi
    def _open_revision(self, form_view_mode=None):
        """
        Fetches the text from the mail.template and open the revision view
        :param form_view_mode: Specify a form view.
        :return: action for opening the revision view
        """
        # We don't need to update keywords when accessing the proposition
        # text (config id in context for that case)
        if not self.env.context.get('config_id'):
            self.reload_text()
        form_view = 'partner_communication_revision.revision_form'
        if form_view_mode:
            form_view += '_' + form_view_mode
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'res_model': self._name,
            'target': 'current',
            'context': self.with_context(form_view_ref=form_view).env.context
        }

    @api.multi
    def _simplify_text(self, text):
        """
        Converts the mail_template raw text to a simplified version,
        readable to any user.
        :return: the simplified text
        """
        self.ensure_one()
        previous_keywords = self.keyword_ids
        found_keywords = self.env['partner.communication.keyword']
        simplified_text, keywords = self._replace_setters(text)
        found_keywords |= keywords
        simplified_text, keywords = self._replace_inline_code(simplified_text)
        found_keywords |= keywords
        nested_position = 1
        if_keyword_index = 1
        for_keyword_index = 1
        while '% if' in simplified_text:
            simplified_text, keywords = self._replace_if(
                simplified_text, nested_position, if_keyword_index)
            found_keywords |= keywords
            if_keywords = keywords.filtered(lambda k: k.type == 'if')
            if_keyword_index += len(if_keywords)
            for_keyword_index += len(keywords - if_keywords)
            nested_position += 1
        nested_position = 1
        while '% for' in simplified_text:
            simplified_text, keywords = self._replace_for(
                simplified_text, nested_position, for_keyword_index)
            found_keywords |= keywords
            for_keyword_index += len(keywords)
            nested_position += 1
        if self._context.get('unstore_keywords'):
            # Remove found keywords
            (found_keywords - previous_keywords).unlink()
        else:
            # Remove invalid keywords that are no more in the template
            (previous_keywords - found_keywords).unlink()
        return simplified_text

    def _replace_inline_code(self, text):
        """
        Finds and replace the ${} portions of the mail.template.
        It will create keyword records
        :param text: mail.template text
        :return: simplified text
        """
        code_regex = r'\$\{.+?\}'
        simple_text = self._replace_keywords(text, 'code', code_regex)
        return simple_text

    def _replace_setters(self, text):
        """
        Finds and replace the % set var = object
        of the mail.template text. It will create keyword records.
        :param text: mail.template text
        :return: simplified text without the setters code, found keywords
        """
        return self._replace_keywords(text, 'var', r'% set (.+?)=(.*)', True)

    def _replace_keywords(self, text, kw_type, pattern, is_black=False):
        """
        Finds and replace keywords
        :param text: mail.template text
        :param kw_type: keyword type
        :param pattern: pattern used for finding the keywords in the template
        :param is_black: set to true to force the color black for the keyword
        :return: simplified text without the keywords code, found keywords
        """
        setter_pattern = re.compile(pattern)
        simple_text = text
        keywords = self.env['partner.communication.keyword']
        keyword_number = 1
        # Find first match
        for match in setter_pattern.finditer(text):
            raw_code = match.group(0).strip()
            if not raw_code:
                continue
            keyword = self.keyword_ids.filtered(
                lambda k: k.raw_code == raw_code and (
                    k.index == keyword_number if kw_type == 'var' else 1))
            if not keyword:
                vals = {
                    'raw_code': raw_code,
                    'type': kw_type,
                    'revision_id': self.id,
                    'position': match.start()
                }
                if is_black:
                    vals['color'] = 'black'
                keyword = keywords.create(vals)
                # Recompute replacement html
                keyword.env.invalidate_all()
            keywords += keyword
            keyword_number += 1
            simple_text = safe_replace(
                simple_text, raw_code, keyword.replacement)
        return simple_text, keywords

    def _replace_if(self, text, nested_position, keyword_number=1):
        """
        Finds and replace the % if: ... % endif
        of the mail.template. It will create keyword records for
        each if found.
        :param text: mail.template text
        :param nested_position: counts how nested if the current pass
        :param keyword_number: counts how many if we found
        :return: simplified text without the if code, keywords found
        """
        # Scan for non-nested % if, % else codes
        if_pattern = re.compile(r'(% if .*?:$)(.*?)(% endif)',
                                flags=re.DOTALL | re.MULTILINE)
        simple_text = text
        keywords = self.env['partner.communication.keyword']
        for match in if_pattern.finditer(text, overlapped=True):
            raw_code = match.group(1).strip()
            if_text = match.group(2)
            start_if = match.start()
            end_if = match.end()
            # Nested ifs : we first convert the sub-ifs and then finish
            # with the root if
            number_nested = if_text.count('% if')
            if number_nested > 0:
                continue
            keyword = self.keyword_ids.filtered(
                lambda k: k.raw_code == raw_code and k.index == keyword_number)

            # Convert nested for loops in if text
            if_text, for_keywords = self._replace_for(if_text, 1)
            keywords += for_keywords

            if_parts = if_text.split('% else:')
            true_text = if_parts[0]
            false_text = if_parts[1].strip() if len(if_parts) > 1 else False
            if not keyword:
                # Create a new keyword object by extracting the text
                keyword = self.keyword_ids.create({
                    'raw_code': raw_code,
                    'revision_id': self.id,
                    'true_text': true_text.strip(),
                    'false_text': false_text,
                    'type': 'if',
                    'position': start_if,
                    'nested_position': nested_position
                })
            else:
                keyword.write({
                    'true_text': true_text,
                    'false_text': false_text,
                    'position': start_if,
                    'nested_position': nested_position
                })
            keywords += keyword
            keyword_number += 1
            simple_text = simple_text.replace(text[start_if:end_if],
                                              keyword.replacement)
        return simple_text, keywords

    def _replace_for(self, text, nested_position, keyword_number=1):
        """
        Finds and replace the % for: ... % endfor loops
        of the mail.template. It will create keyword records for
        each loop found.
        :param text: mail.template text
        :param nested_position: counts how nested if the current pass
        :param keyword_number: counts how many for we found
        :return: simplified text without the if code, keywords found
        """
        # Regex for finding text wrapped in loops
        loop_regex = r'(% for .*?:$)(.*?)(% endfor)'
        ul_loop_regex = r'(?:<ul[^<]*?)(% for .*?:$)(.*?)(% endfor)(.*?</ul>)'

        # First scan for ul_loops
        for_pattern = re.compile(ul_loop_regex, flags=re.DOTALL | re.MULTILINE)
        simple_text, found_keywords = self._replace_for_type(
            text, nested_position, keyword_number, 'for_ul', for_pattern)
        keyword_number += len(found_keywords)

        # Then scan for regular loops
        for_pattern = re.compile(loop_regex, flags=re.DOTALL | re.MULTILINE)
        simple_text, keywords = self._replace_for_type(
            simple_text, nested_position, keyword_number, 'for', for_pattern)
        found_keywords |= keywords

        return simple_text, found_keywords

    def _replace_for_type(self, text, nested_position, keyword_number,
                          for_type, for_pattern):
        simple_text = text
        keywords = self.env['partner.communication.keyword']
        for match in for_pattern.finditer(text, overlapped=True):
            raw_code = match.group(1).strip()
            for_text = match.group(2)
            start_for = match.start()
            end_for = match.end()
            # Nested for : skip to next for loop which is not encapsulating
            # another loop. The while loop will take care of it later.
            number_nested = for_text.count('% for')
            if number_nested > 0:
                continue
            keyword = self.keyword_ids.filtered(
                lambda k: k.raw_code == raw_code and
                k.index == keyword_number and k.type == for_type)
            if not keyword:
                # Create a new keyword object by extracting the text
                keyword = self.keyword_ids.create({
                    'raw_code': raw_code,
                    'revision_id': self.id,
                    'true_text': for_text.strip(),
                    'type': for_type,
                    'position': start_for,
                    'nested_position': nested_position
                })
            else:
                keyword.write({
                    'true_text': for_text,
                    'position': start_for,
                    'nested_position': nested_position
                })
            keywords += keyword
            keyword_number += 1
            simple_text = simple_text.replace(text[start_for:end_for],
                                              keyword.replacement)
        return simple_text, keywords

    @api.multi
    def _enhance_text(self):
        """
        Transforms a simplified text into a valid mail.template text.
        :return: mail.template text
        """
        self.ensure_one()
        # Parse and set back the keywords into raw template code
        html_text = PyQuery(self.simplified_text.replace('\n', ''))

        def sort_keywords(kw):
            # Replace first if/for-clauses, then var, then code
            index = kw.position
            if kw.type == 'if' or 'for' in kw.type:
                index += 2*len(self.body_html) * kw.nested_position
                # Take if and for in the appearing order in the text
                index -= kw.position
            elif kw.type == 'var':
                index += len(self.body_html)
            return index

        keywords = self.keyword_ids.sorted(sort_keywords, reverse=True)
        # Replace automatic-generated keywords
        for keyword in keywords:
            keyword_text = html_text('#' + keyword.html_id)
            keyword_text.replace_with(keyword.final_text)

        # Replace user added keywords
        template_text = html_text.html()
        for keyword in keywords.filtered(lambda k: k.type == 'code'):
            to_replace = u"[{}]".format(keyword.short_code)
            template_text = template_text.replace(to_replace, keyword.raw_code)
        final_text = PyQuery(BeautifulSoup(template_text).prettify())
        return final_text('body').html()
