##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import logging
from urllib.request import urlopen

from odoo import models, fields, api, _

logger = logging.getLogger(__name__)


class ChildPictures(models.Model):
    _name = "compassion.child.pictures"
    _description = "Child picture"
    _order = "date desc, id desc"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    child_id = fields.Many2one(
        "compassion.child", "Child", required=True, ondelete="cascade", readonly=False
    )
    fullshot = fields.Binary(attachment=True)
    headshot = fields.Binary(attachment=True)
    image_url = fields.Char()
    date = fields.Date("Date of pictures", default=fields.Date.today)
    fname = fields.Char(compute="_compute_filename")
    hname = fields.Char(compute="_compute_filename")
    _error_msg = "Image cannot be fetched: No image url available"

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _compute_filename(self):
        for pictures in self:
            date = fields.Date.to_string(pictures.date)
            code = pictures.child_id.local_id
            pictures.fname = code + " " + date + " fullshot.jpg"
            pictures.hname = code + " " + date + " headshot.jpg"

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ Fetch new pictures from GMC webservice when creating
        a new Pictures object. Check if picture is the same as the previous
        and attach the pictures to the last case study.
        """

        pictures = super().create(vals)

        same_url = pictures._find_same_picture_by_url()
        if same_url:
            pictures.child_id.message_post(
                body=_("The picture was the same"), subject=_("Picture update")
            )
            pictures.unlink()
            return False

        # Retrieve Headshot
        image_date = pictures._get_picture("Headshot", width=180, height=180)
        # Retrieve Fullshot
        image_date = image_date and pictures._get_picture(
            "Fullshot", width=800, height=1200
        )

        if not image_date:
            # We could not retrieve a picture, we cancel the creation
            pictures.child_id.message_post(
                body=_(pictures._error_msg), subject=_("Picture update"))
            pictures.unlink()
            return False

        # Find if same pictures already exist
        same_pictures = pictures._find_same_picture()
        if same_pictures:
            # That case is not likely to happens, it means that the url has
            #  changed, while the picture stay unchanged.
            pictures.child_id.message_post(
                body=_("The picture was the same"), subject=_("Picture update")
            )
            pictures.unlink()
            return False

        pictures.write({"date": image_date})
        return pictures

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.multi
    def _find_same_picture_by_url(self):
        self.ensure_one()
        same_url = self.search(
            [
                ("child_id", "=", self.child_id.id),
                ("image_url", "=", self.image_url),
                ("id", "!=", self.id),
            ]
        )
        return same_url

    @api.multi
    def _find_same_picture(self):
        self.ensure_one()
        pics = self.search([("child_id", "=", self.child_id.id)])
        same_pics = pics.filtered(
            lambda record: record.fullshot == self.fullshot
            and record.headshot == self.headshot
            and record.id != self.id
        )
        return same_pics

    @api.multi
    def _get_picture(self, pic_type="Headshot", width=300, height=400):
        """ Gets a picture from Compassion webservice """
        self.ensure_one()
        if pic_type.lower() == "headshot":
            cloudinary = (
                "g_face,c_thumb,h_" + str(height) + ",w_" + str(width) + ",z_1.2"
            )
        elif pic_type.lower() == "fullshot":
            cloudinary = "w_" + str(width) + ",h_" + str(height) + ",c_fit"

        _image_date = False
        for picture in self.filtered("image_url"):
            try:
                image_split = picture.image_url.split("/")
                if "upload" in picture.image_url:
                    ind = image_split.index("upload")
                else:
                    ind = image_split.index("media.ci.org")
                image_split[ind + 1] = cloudinary
                url = "/".join(image_split)
                data = base64.encodebytes(urlopen(url).read())
                _image_date = picture.child_id.last_photo_date or fields.Date.today()
                if pic_type.lower() == "headshot":
                    self.headshot = data
                elif pic_type.lower() == "fullshot":
                    self.fullshot = data
            except:
                self._error_msg = (
                    "Image cannot be fetched, invalid image "
                    "url : " + picture.image_url
                )
                logger.error("Image cannot be fetched : " + picture.image_url)
                continue

        return _image_date
