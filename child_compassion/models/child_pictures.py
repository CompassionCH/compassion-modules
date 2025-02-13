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
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from odoo import _, api, fields, models
from odoo.http import request

logger = logging.getLogger(__name__)

# This User-Agent simulate a browser, so that the fetch is not blocked
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; "
    "en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7"
}


class ChildPictures(models.Model):
    _name = "compassion.child.pictures"
    _description = "Child picture"
    _order = "date desc, id desc"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    child_id = fields.Many2one(
        "compassion.child", "Child", required=True, ondelete="cascade"
    )
    fullshot = fields.Image()
    headshot = fields.Image()
    image_url = fields.Char(required=True)
    image_url_compassion = fields.Char(compute="_compute_image_url_compassion")
    date = fields.Date("Date of pictures", default=fields.Date.today)
    fname = fields.Char(compute="_compute_filename")
    hname = fields.Char(compute="_compute_filename")

    funct_new_photo_called = fields.Boolean(default=False)
    _sql_constraints = [
        (
            "unique_picture_per_child",
            "UNIQUE(child_id,image_url)",
            "You cannot set two identical images for the same child.",
        )
    ]

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _compute_filename(self):
        for pictures in self:
            date = fields.Date.to_string(pictures.date)
            code = pictures.child_id.local_id
            pictures.fname = code + " " + date + " fullshot.jpg"
            pictures.hname = code + " " + date + " headshot.jpg"

    def _compute_image_url_compassion(self):
        config = self.env["ir.config_parameter"].sudo()
        if hasattr(request, "website"):
            base_url = request.website.domain
        else:
            base_url = config.get_param(
                "web.external.url", config.get_param("web.base.url")
            )

        endpoint = f"{base_url}/web/image/compassion.child.pictures"

        for image in self:
            image.image_url_compassion = (
                f"{endpoint}/{image.id}/fullshot/{image.date}_{image.child_id.id}.jpg"
            )

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """Fetch new pictures from GMC webservice when creating
        a new Pictures object. Check if picture is the same as the previous
        and attach the pictures to the last case study.
        """
        existing_picture = self._child_picture_already_exists(vals)
        if existing_picture:
            return existing_picture

        picture = super().create(vals)
        # Fetch the image from the webservice
        image_date = picture._fetch_and_attach_pictures()

        # Handle the case where the picture cannot be fetched
        if not image_date:
            picture._handle_picture_issue(
                _("Image cannot be fetched: No image URL available.")
            )
            return self

        # Find if same pictures already exist
        duplicate = picture._find_same_picture()
        if duplicate:
            picture._handle_picture_issue(_("The picture was the same."))
            return duplicate

        picture.write({"date": image_date})
        return picture

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _fetch_and_attach_pictures(self):
        """Fetch the pictures from the webservice and attach them to the record."""
        headshot_fetched = self._get_picture("Headshot", width=180, height=180)
        fullshot_fetched = self._get_picture("Fullshot", width=800, height=1200)
        return headshot_fetched and fullshot_fetched

    def _handle_picture_issue(self, message):
        """Handle issues with the picture, such as fetch failure or duplication."""
        logger.warning(message)
        self.child_id.message_post(body=message, subject=_("Picture update"))
        self.unlink()

    def _find_same_picture(self):
        self.ensure_one()
        reference = self.with_context(bin_size=False)
        pics = reference.search(
            [("child_id", "=", self.child_id.id), ("id", "!=", self.id)], limit=1
        )
        same_pics = pics.filtered(
            lambda record: record.fullshot == reference.fullshot
            and record.headshot == reference.headshot
        )
        return same_pics

    def _child_picture_already_exists(self, vals):
        existing_picture = self.search(
            [
                ("child_id", "=", vals.get("child_id")),
                ("image_url", "=", vals.get("image_url")),
            ],
            limit=1,
        )
        return existing_picture

    def _get_picture(self, pic_type="Headshot", width=300, height=400):
        """Gets a picture from Compassion webservice."""
        self.ensure_one()
        if pic_type.lower() == "headshot":
            cloudinary = (
                "g_face,c_thumb,h_" + str(height) + ",w_" + str(width) + ",z_1.2"
            )
        elif pic_type.lower() == "fullshot":
            cloudinary = "w_" + str(width) + ",h_" + str(height) + ",c_fit"

        _image_date = False
        try:
            image_split = self.image_url.split("/")
            if "upload" in self.image_url:
                ind = image_split.index("upload")
            else:
                ind = image_split.index("media.ci.org")
            image_split[ind + 1] = cloudinary
            url = "/".join(image_split)

            data = urlopen(Request(url, None, HEADERS)).read()
            data = base64.encodebytes(data)
            _image_date = self.child_id.last_photo_date or fields.Date.today()
            if pic_type.lower() == "headshot":
                self.headshot = data
            elif pic_type.lower() == "fullshot":
                self.fullshot = data
        except (AttributeError, ValueError, URLError, HTTPError, TypeError):
            logger.error("Failed to fetch image from %s", self.image_url, exc_info=True)
        return _image_date
