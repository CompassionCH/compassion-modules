# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Mathier <emmanuel.mathier@gmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import fields, models, api, _
from PIL import Image
from cStringIO import StringIO
# from PIL import Image
#from PIL import ImageDraw
#from PIL import ImageFont
#import urllib.request
import io
#import binascii
import pdb

class SponsorshipCorrespondence(models.Model):

    """ This class holds the data of a Communication Kit between
    a child and a sponsor.
    """

    _name = 'sponsorship.correspondence'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    sponsorship_id = fields.Many2one(
        'recurring.contract', 'Sponsorship', required=True)
    name = fields.Char(compute='_set_name')
    partner_id = fields.Many2one(
        related='sponsorship_id.correspondant_id', store=True)
    child_id = fields.Many2one(related='sponsorship_id.child_id', store=True)
    # Field used for identifying correspondence
    kit_id = fields.Integer('Kit id', copy=False, readonly=True)
    letter_type = fields.Selection(selection=[
        ('S2B', _('Sponsor to beneficiary')),
        ('B2S', _('Beneficiary to sponsor'))], required=True)
    communication_type = fields.Selection(selection=[
        ('scheduled', _('Scheduled')),
        ('response', _('Response')),
        ('thank_you', _('Thank you')),
        ('third_party', _('Third party')),
        ('christmas', _('Christmas')),
        ('introduction', _('Introduction'))])
    state = fields.Selection(selection=[
        ('new', _('New')),
        ('to_translate', _('To translate')),
        ('translated', _('Translated')),
        ('quality_checked', _('Quality checked')),
        ('rejected', _('Rejected')),
        ('sent', _('Sent')),
        ('delivered', _('Delivered'))], default='new')
    is_encourager = fields.Boolean()
    mandatory_review = fields.Boolean(compute='_set_partner_review',
                                      readonly=False, store=True)
    letter_image = fields.Many2one('ir.attachment', required=True)
    #letter_image_preview = fields.Many2one('ir.attachment', compute='_set_preview')
    attachments_ids = fields.Many2many('ir.attachment')
    physical_attachments = fields.Selection(selection=[
        ('none', _('None')),
        ('sent_by_mail', _('Sent by mail')),
        ('not_sent', _('Not sent'))])
    attachments_description = fields.Text()
    supporter_languages_ids = fields.Many2many(
        related='partner_id.spoken_langs_ids',
        store=True, readonly=True)
    beneficiary_language_ids = fields.Many2many(
        related='child_id.project_id.country_id.\
spoken_langs_ids', store=True)
    # First spoken lang of partner
    original_language_id = fields.Many2one(
        'res.lang.compassion', compute='_set_original_language', store=True)
    destination_language_id = fields.Many2one(
        'res.lang.compassion', compute='_set_original_language', store=True)
    template_id = fields.Selection(selection=[
        ('template_1', _('Template 1')),
        ('template_2', _('Template 2')),
        ('template_3', _('Template 3')),
        ('template_4', _('Template 4')),
        ('template_5', _('Template 5'))], required=True)
    original_text = fields.Text()
    translated_text = fields.Text()
    source = fields.Selection(selection=[
        ('letter', _('Letter')),
        ('email', _('E-Mail')),
        ('website', _('Compassion website'))])

    _sql_constraints = [
        ('kit_id',
         'unique(kit_id)',
         _('The kit id already exists in database.'))
    ]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    @api.depends('sponsorship_id')
    def _set_name(self):
        if self.sponsorship_id:
            self.name = str(
                self.sponsorship_id.partner_codega) + " - " + str(
                    self.child_id.code)
        else:
            self.name = _('New correspondence')

    @api.depends('sponsorship_id', 'letter_type')
    def _set_original_language(self):
        if self.letter_type == 'S2B':
            if self.partner_id.spoken_langs_ids:
                self.original_language_id = self.partner_id\
                    .spoken_langs_ids[0]
            if self.child_id.project_id.country_id.spoken_langs_ids:
                self.destination_language_id = self.child_id.project_id\
                    .country_id.spoken_langs_ids[0]
        if self.letter_type == 'B2S':
            if self.child_id.project_id.country_id.spoken_langs_ids:
                self.original_language_id = self.child_id.project_id\
                    .country_id.spoken_langs_ids[0]
            if self.partner_id.spoken_langs_ids:
                self.destination_language_id = self.partner_id\
                    .spoken_langs_ids[0]

    @api.depends('sponsorship_id')
    def _set_partner_review(self):
        if self.partner_id.mandatory_review:
            self.mandatory_review = True
        else:
            self.mandatory_review = False

    # @api.depends('letter_image')
    # def _set_preview(self):
    #     if self.letter_image:
            # buff = StringIO()
            # buff.write(self.letter_image.datas)
            # buff.seek(0)

            # # stream = bytes(self.letter_image.datas)
            # # pdb.set_trace()
            # # RGBbytes = ''.join([ stream[i+2:i+3] + stream[i+1:i+2] + stream[i:i+1] for i in range(0, len(stream) -1, 4)])
            # pdb.set_trace()
            # im = Image.open(buff)
            # pdb.set_trace()
            # im.save(fake_file_to_read, "JPEG", quality=100)
            # self.letter_image_preview = fake_file_to_read.read()

        # if self.letter_image:
        #     fake_file_to_write = StringIO()
        #     fake_file_to_write.write(self.letter_image.datas)
        #     im = Image.open(fake_file_to_write)
        #     im.thumbnail(im.size)
        #     im.save(fake_file_to_read, "JPEG", quality=100)
        #     self.letter_image_preview = fake_file_to_read.read

# /tmp/sbc_compassion/File_
#io.BytesIO(RGBbytes)

# from PIL import Image
# from PIL import ImageDraw
# from PIL import ImageFont
# import urllib.request
# import io
# import binascii

# data = urllib.request.urlopen('http://pastebin.ca/raw/2311595').read()
# r_data = binascii.unhexlify(data)
# #r_data = "".unhexlify(chr(int(b_data[i:i+2],16)) for i in range(0, len(b_data),2))

# stream = io.BytesIO(r_data)

# img = Image.open(stream)
# draw = ImageDraw.Draw(img)
# font = ImageFont.truetype("arial.ttf",14)
# draw.text((0, 220),"This is a test11",(255,255,0),font=font)
# draw = ImageDraw.Draw(img)
# img.save("a_test.png")

#  outfile = os.path.splitext(os.path.join(root, name))[0] + ".jpg"


#  im = Image.open('test.jpg')
# im.save('test.tiff')

        # if self.letter_image:
        #     fake_file_to_write = StringIO()
        #     fake_file_to_write.write(self.letter_image.datas)
        #     im = Image.open(fake_file_to_write)
        #     im.thumbnail(im.size)
        #     im.save(fake_file_to_read, "JPEG", quality=100)
        #     self.letter_image_preview = fake_file_to_read.read