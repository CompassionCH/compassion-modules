##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import html
import logging

from odoo import api, models, fields, _
from ..tools import wp_requests

_logger = logging.getLogger(__name__)


class WordpressPost(models.Model):
    """
    This serves as a local cache of all Published articles on the WP website,
    in order to answer fast to mobile app queries for rendering the main
    hub of the users.
    """

    _name = "wp.post"
    _description = "Wordpress post"
    _inherit = "compassion.mapped.model"
    _order = "date desc"

    name = fields.Char("Title", required=True)
    date = fields.Datetime(required=True)
    wp_id = fields.Integer("Wordpress Post ID", required=True, index=True)
    url = fields.Char("URL")
    image_url = fields.Char()
    post_type = fields.Selection(
        [("posts", "News"), ("agendas", "Agenda"), ("download", "Download")]
    )
    category_ids = fields.Many2many(
        "wp.post.category", string="Categories", readonly=False
    )

    lang = fields.Selection("select_lang", "Language", required=True)
    display_on_hub = fields.Boolean(
        default=True, help="Deactivate in order to hide tiles in App."
    )
    view_order = fields.Integer("View order", required=True, default=6000)
    is_automatic_ordering = fields.Boolean("Automatic ordering", default=True)
    tile_type = fields.Selection(
        [("Prayer", "Prayer"), ("Story", "Story")],
        compute="_compute_tile_type",
        inverse="_inverse_tile_type",
        store=True,
    )
    tile_subtype = fields.Selection(
        [("PR2", "PR2"), ("ST_T1", "ST_T1"), ], compute="_compute_tile_subtype"
    )

    _sql_constraints = [("wp_unique", "unique(wp_id)", "This post already exists")]

    @api.multi
    @api.depends("category_ids", "category_ids.default_tile_type")
    def _compute_tile_type(self):
        for post in self:
            default_types = post.category_ids.mapped("default_tile_type")
            if default_types and not post.tile_type:
                post.tile_type = default_types[0]

    @api.multi
    def _compute_tile_subtype(self):
        for post in self:
            post.tile_subtype = "PR2" if post.tile_type == "Prayer" else "ST_T1"

    @api.multi
    def _inverse_tile_type(self):
        # Simply allows to write in field
        return True

    @api.model
    def select_lang(self):
        langs = self.env["res.lang"].search([])
        return [(lang.code, lang.name) for lang in langs]

    @api.onchange("display_on_hub")
    def onchange_display_on_hub(self):
        """
        If the user activate the display on hub, notify that the wordpress
        post should have some content.
        :return: warning to user
        """
        if self.display_on_hub:
            return {
                "warning": {
                    "title": _("Warning"),
                    "message": _(
                        "This post was disabled probably because it doesn't "
                        "have a content. Please make sure the post has a "
                        "body to avoid any display issues in the mobile app."
                    ),
                },
            }

    @api.model
    def fetch_posts(self, post_type):
        """
        This is called by a CRON job in order to refresh the cache
        of published posts in the website.
        https://developer.wordpress.org/rest-api/reference/posts/
        :param post_type: the post type to fetch
        :return: True
        """
        _logger.info("Fetch Wordpress %s started!", post_type)
        wp_config = self.env["wordpress.configuration"].get_config()
        # This is standard Wordpress REST API URL
        wp_api_url = "https://" + wp_config.host + "/wp-json/wp/v2/" + post_type
        # This is for avoid loading all post content
        params = {"context": "embed", "per_page": 100}
        found_ids = []
        try:
            with wp_requests.Session(wp_config) as requests:
                for lang in self._supported_langs():
                    params["lang"] = lang.code[:2]
                    wp_posts = requests.get(wp_api_url, params=params).json()

                    _logger.debug("Processing posts in %s", lang.name)
                    for i, post_data in enumerate(wp_posts):
                        _logger.debug(
                            "...processing post " f"{str(i + 1)}/{str(len(wp_posts))}"
                        )
                        post_id = post_data["id"]
                        found_ids.append(post_id)
                        # TODO AP-377 FIX this code erases all categories of our news
                        # cached_post = self.search([("wp_id", "=", post_id)])
                        # if cached_post:
                        #     cached_post.update_post_categories(post_data, requests)
                            # Skip post already fetched
                            # continue

                        content_empty = True
                        self_url = post_data["_links"]["self"][0]["href"]
                        http_response = requests.get(self_url)
                        if http_response.ok:
                            content = http_response.json()
                            if content["content"]["rendered"]:
                                content_empty = False
                        try:
                            # Fetch image for thumbnail
                            image_json_url = post_data["_links"]["wp:featuredmedia"][0][
                                "href"
                            ]
                            image_json = requests.get(image_json_url).json()
                            if (
                                    ".jpg"
                                    in image_json["media_details"]["sizes"]["medium"][
                                        "source_url"
                                    ]
                            ):
                                image_url = image_json["media_details"]["sizes"][
                                    "medium"
                                ]["source_url"]
                            else:
                                image_url = image_json["source_url"]
                        except KeyError:
                            # Some post images may not be accessible
                            image_url = False
                            _logger.warning("WP Post ID %s has no image", str(post_id))
                        # Fetch post category
                        categories_id = self._fetch_categories_ids(post_data, requests)

                        # Cache new post in database
                        self.create(
                            {
                                "name": html.unescape(post_data["title"]["rendered"]),
                                "date": post_data["date"],
                                "wp_id": post_id,
                                "url": post_data["link"],
                                "image_url": image_url,
                                "post_type": post_type,
                                "category_ids": [(6, 0, categories_id)],
                                "lang": lang.code,
                                "display_on_hub": not content_empty,
                            }
                        )
            # Delete unpublished posts
            self.search(
                [("wp_id", "not in", found_ids), ("post_type", "=", post_type)]
            ).unlink()
            _logger.info("Fetch Wordpress Posts finished!")
        except ValueError:
            _logger.warning("Error fetching wordpress posts", exc_info=True)
        return True

    def update_post_categories(self, post_data, requests):
        """
        Update the categories from a post, given the JSON data received.
        :param post_data: JSON data from the Wordpress API
        :param requests: The Wordpress API session
        :return: None
        """
        self.ensure_one()
        categories_id = self._fetch_categories_ids(post_data, requests)
        # If there is a difference between categories
        if sorted(self.category_ids.ids) != sorted(categories_id):
            self.write(
                {"category_ids": [(6, 0, categories_id)], }
            )
        self.update_display_on_hub()

    def _fetch_categories_ids(self, post_data, requests):
        """
        Get the wordpress category ids associated to the JSON post data.
        :param post_data: JSON post data retrieved from Wordpress API
        :param requests: The Wordpress API session
        :return: list of wp.post.category record ids
        """
        categories_id = []
        category_obj = self.env["wp.post.category"]
        try:
            category_data = [
                d for d in post_data["_links"]["wp:term"] if d["taxonomy"] == "category"
            ][0]
            category_json_url = category_data["href"]

            categories_request = requests.get(category_json_url).json()
            if not isinstance(categories_request, list):
                categories_request = [categories_request]
            for c in categories_request:
                if not isinstance(c, dict):
                    continue
                category = category_obj.search([("name", "=", c["name"])])
                if not category:
                    category = category_obj.create({"name": c["name"]})
                categories_id.append(category.id)
        except (IndexError, KeyError):
            _logger.warning("WP Post ID %s has no category.", str(post_data["id"]))
        return categories_id

    def update_display_on_hub(self):
        """ Compute visibility of post based on the visibility of its
        categories. It will be visible if at least one category is visible. """
        for post in self:
            post.display_on_hub = post.category_ids.filtered("display_on_hub")

    @api.model
    def _supported_langs(self):
        """
        Will fetch all wordpress posts in the given langs
        :return: res.lang recordset
        """
        return self.env["res.lang"].search([("code", "!=", "en_US")])

    @api.multi
    def data_to_json(self, mapping_name=None):
        res = super().data_to_json(mapping_name)
        if not res:
            res = {}
        for key, value in list(res.items()):
            if not value:
                res[key] = None
        return res
