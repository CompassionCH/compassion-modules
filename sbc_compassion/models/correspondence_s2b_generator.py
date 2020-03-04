##############################################################################
#
#    Copyright (C) 2016-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import logging

from io import BytesIO

from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.addons.queue_job.job import job, related_action

_logger = logging.getLogger(__name__)

try:
    from PyPDF2 import PdfFileReader, PdfFileWriter
    from wand.image import Image
except ImportError:
    _logger.debug('Please install wand to use SBC module')


class CorrespondenceS2bGenerator(models.Model):
    """ Generation of S2B Letters with text.
    """
    _name = 'correspondence.s2b.generator'
    _description = 'Correspondence Generator'
    _order = 'date desc'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    state = fields.Selection([
        ('draft', 'Draft'),
        ('preview', 'Preview'),
        ('done', 'Done')
    ], default='draft')
    name = fields.Char(required=True)
    date = fields.Datetime(default=fields.Datetime.now)
    image_ids = fields.Many2many('ir.attachment', string='Attached images')
    s2b_template_id = fields.Many2one(
        'correspondence.template', 'S2B Template', required=True)
    background = fields.Binary(
        related='s2b_template_id.template_image'
    )
    selection_domain = fields.Char(
        default="[('state', '=', 'active'), ('child_id', '!=', False)]")
    sponsorship_ids = fields.Many2many(
        'recurring.contract', string='Sponsorships', required=True
    )
    language_id = fields.Many2one('res.lang.compassion', 'Language')
    body = fields.Text(
        required=True,
        help='You can use the following tags to replace with values :\n\n'
        '* %child%: child name\n'
        '* %age%: child age (1, 2, 3, ...)\n'
        '* %firstname%: sponsor firstname\n'
        '* %lastname%: sponsor lastname\n',
        oldname='body_html'
    )
    letter_ids = fields.One2many(
        'correspondence', 'generator_id', 'Letters'
    )
    nb_letters = fields.Integer(compute='_compute_nb_letters')
    preview_image = fields.Binary(readonly=True)
    preview_pdf = fields.Binary(readonly=True)
    filename = fields.Char(compute='_compute_filename')
    month = fields.Selection('_get_months')

    source = fields.Selection(selection=[
        ('letter', _('Letter')),
        ('email', _('E-Mail')),
        ('website', _('Compassion website')),
        ('app', _('Mobile app')),
        ('compassion', _('Written by Compassion'))], default='compassion')

    def _compute_nb_letters(self):
        for generator in self:
            generator.nb_letters = len(generator.letter_ids)

    @api.model
    def _get_months(self):
        return self.env['compassion.child']._get_months()

    def _compute_filename(self):
        for generator in self:
            generator.filename = generator.name + '.pdf'

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.onchange('selection_domain')
    def onchange_domain(self):
        if self.selection_domain:
            self.sponsorship_ids = self.env['recurring.contract'].search(
                safe_eval(self.selection_domain))

    @api.onchange('month')
    def onchange_month(self):
        if self.month:
            domain = safe_eval(self.selection_domain)
            month_select = ('child_id.birthday_month', '=', self.month)
            index = 0
            for search_filter in domain:
                if search_filter[0] == 'child_id.birthday_month':
                    index = domain.index(search_filter)
            if index:
                domain[index] = month_select
            else:
                domain.append(month_select)
            self.selection_domain = str(domain)

    @api.multi
    def preview(self):
        """ Generate a picture for preview.
        """
        pdf = self._get_pdf(self.sponsorship_ids[:1])[0]
        if self.s2b_template_id.layout == 'CH-A-3S01-1':
            # Read page 2
            in_pdf = PdfFileReader(BytesIO(pdf))
            output_pdf = PdfFileWriter()
            out_data = BytesIO()
            output_pdf.addPage(in_pdf.getPage(1))
            output_pdf.write(out_data)
            out_data.seek(0)
            pdf = out_data.read()

        with Image(blob=pdf) as pdf_image:
            preview = base64.b64encode(pdf_image.make_blob(format='jpeg'))

        pdf_image = base64.b64encode(pdf)

        return self.write({
            'state': 'preview',
            'preview_image': preview,
            'preview_pdf': pdf_image,
        })

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
        self.with_delay().generate_letters_job()
        return self.write({
            'state': 'done',
            'date': fields.Datetime.now(),
        })

    @api.multi
    @job(default_channel='root.sbc_compassion')
    @related_action(action='related_action_s2b')
    def generate_letters_job(self):
        """
        Create S2B Letters
        :return: True
        """
        letters = self.env['correspondence']
        for sponsorship in self.sponsorship_ids:
            text = self._get_text(sponsorship)
            vals = {
                'sponsorship_id': sponsorship.id,
                'store_letter_image': False,
                'template_id': self.s2b_template_id.id,
                'direction': 'Supporter To Beneficiary',
                'source': self.source,
                'original_language_id': self.language_id.id,
                'original_text': text,
            }
            if self.image_ids:
                vals['original_attachment_ids'] = [(0, 0, {
                    'datas_fname': atchmt.datas_fname,
                    'datas': atchmt.datas,
                    'name': atchmt.name,
                    'res_model': letters._name,
                }) for atchmt in self.image_ids]
            letters += letters.create(vals)

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

    def _get_text(self, sponsorship):
        """ Generates the text given a sponsorship. """
        self.ensure_one()
        sponsor = sponsorship.correspondent_id
        child = sponsorship.child_id
        keywords = {
            '%child%': child.preferred_name,
            '%age%': str(child.age),
            '%firstname%': sponsor.firstname or sponsor.name,
            '%lastname%': sponsor.firstname and sponsor.lastname or '',
        }
        text = self.body
        for keyword, replacement in list(keywords.items()):
            text = text.replace(keyword, replacement)

        return text

    def _get_pdf(self, sponsorship):
        """ Generates a PDF given a sponsorship. """
        self.ensure_one()
        sponsor = sponsorship.correspondent_id
        child = sponsorship.child_id
        text = self._get_text(sponsorship)

        header = f"{sponsor.global_id} - {sponsor.name} - \n" \
                 f"{child.local_id} - {child.lastname +' '+ child.firstname}"\
                 f" - {'Female' if child.gender == 'F' else 'Male'}" \
                 f" - {str(child.age)}"

        return self.s2b_template_id.generate_pdf(
            sponsorship.name,
            (header, ''),  # Headers (front/back)
            {'Original': [text]},  # Text
            self.mapped('image_ids.datas')  # Images
        ), text
