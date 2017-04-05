# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import base64
from bs4 import BeautifulSoup
from wand.image import Image

from openerp import api, fields, models
from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.session import ConnectorSession


class CorrespondenceS2bGenerator(models.Model):
    """ Generation of S2B Letters with text.
    """
    _name = 'correspondence.s2b.generator'
    _description = 'Correspondence Generator'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    state = fields.Selection([
        ('draft', 'Draft'),
        ('preview', 'Preview'),
        ('done', 'Done')
    ], default='draft')
    name = fields.Char(required=True)
    date = fields.Date()
    s2b_template_id = fields.Many2one(
        'correspondence.template', 'S2B Template', required=True)
    report = fields.Many2one(
        'ir.actions.report.xml',
        related='s2b_template_id.report_id'
    )
    background = fields.Binary(
        related='s2b_template_id.template_image'
    )
    selection_domain = fields.Char(default="[('state', '=', 'active')]")
    sponsorship_ids = fields.Many2many(
        'recurring.contract', string='Sponsorships', required=True
    )
    sponsorship_id = fields.Many2one(
        'recurring.contract', help='Current sponsorship for letter generation'
    )
    language_id = fields.Many2one(
        'res.lang.compassion', 'Language',
        default=lambda s: s.env.ref(
            'child_compassion.lang_compassion_english')
    )
    body_html = fields.Html(
        required=True,
        help='You can use the following tags to replace with values :\n\n'
        '* %child%: child name\n'
        '* %age%: child age (1, 2, 3, ...)\n'
        '* %firstname%: sponsor firstname\n'
        '* %lastname%: sponsor lastname\n'
    )
    body_backup = fields.Html()
    letter_ids = fields.One2many(
        'correspondence', 'generator_id', 'Letters'
    )
    nb_letters = fields.Integer(compute='_compute_nb_letters')
    preview_image = fields.Binary(readonly=True)

    def _compute_nb_letters(self):
        for generator in self:
            generator.nb_letters = len(generator.letter_ids)

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.onchange('selection_domain')
    def onchange_domain(self):
        if self.selection_domain:
            self.sponsorship_ids = self.env['recurring.contract'].search(
                eval(self.selection_domain))

    @api.multi
    def preview(self):
        """ Generate a picture for preview.
        """
        pdf = self._get_pdf(self.sponsorship_ids[0], preview=True)
        with Image(blob=pdf) as pdf_image:
            preview = base64.b64encode(pdf_image.make_blob(format='jpeg'))
        return self.write({'state': 'preview', 'preview_image': preview})

    @api.multi
    def edit(self):
        """ Generate a picture for preview.
        """
        return self.write({'state': 'draft'})

    @api.multi
    def generate_letters(self):
        """
        Launch S2B Creation job
        :return: True
        """
        session = ConnectorSession.from_env(self.env)
        generate_s2b_job.delay(session, self._name, self.id)
        return self.write({
            'state': 'done',
            'date': fields.Date.today(),
        })

    @api.multi
    def generate_letters_job(self):
        """
        Create S2B Letters
        :return: True
        """
        letters = self.env['correspondence']
        for sponsorship in self.sponsorship_ids:
            pdf = self._get_pdf(sponsorship)
            raw_text = BeautifulSoup(self.body_html).text.replace(
                '\n', '\n' * 2)
            letters += letters.create({
                'sponsorship_id': sponsorship.id,
                'letter_image': base64.b64encode(pdf),
                'template_id': self.s2b_template_id.id,
                'direction': 'Supporter To Beneficiary',
                'source': 'compassion',
                'original_language_id': self.language_id.id,
                'original_text': raw_text,
            })
            self.body_html = self.body_backup
        self.letter_ids = letters
        return True

    @api.multi
    def open_letters(self):
        letters = self.letter_ids
        return {
            'name': letters._description,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': letters._name,
            'context': self.env.context,
            'domain': [('id', 'in', letters.ids)],
            'target': 'current',
        }

    def _get_pdf(self, sponsorship, preview=False):
        """ Generates a PDF given a sponsorship. """
        sponsor = sponsorship.correspondant_id
        child = sponsorship.child_id
        keywords = {
            '%child%': child.preferred_name,
            '%age%': str(child.age),
            '%firstname%': sponsor.firstname or sponsor.name,
            '%lastname%': sponsor.firstname and sponsor.lastname or '',
        }
        html_text = self.body_html
        for keyword, replacement in keywords.iteritems():
            html_text = html_text.replace(keyword, replacement)

        self.write({
            'body_html': html_text,
            'body_backup': self.body_html,
            'sponsorship_id': sponsorship.id
        })
        pdf = self.env['report'].get_pdf(self, self.report.report_name)
        if preview:
            self.body_html = self.body_backup
        return pdf


def related_action_s2b(session, job):
    model = job.args[0]
    object_id = job.args[1]
    action = {
        'type': 'ir.actions.act_window',
        'res_model': model,
        'view_type': 'form',
        'view_mode': 'form',
        'res_id': object_id,
    }
    return action


@job(default_channel='root.sbc_compassion')
@related_action(action=related_action_s2b)
def generate_s2b_job(session, model, generator_id):
    """Job for generating S2B Letters."""
    generator = session.env[model].browse(generator_id)
    generator.generate_letters_job()
