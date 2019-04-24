# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from ..tools import wp_requests


from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import config

_logger = logging.getLogger(__name__)


class WordpressPost(models.Model):
    """
    This serves as a local cache of all Published articles on the WP website,
    in order to answer fast to mobile app queries for rendering the main
    hub of the users.
    """
    _name = 'wp.post'
    _description = 'Wordpress post'
    _order = 'date desc'

    name = fields.Char('Title', required=True)
    date = fields.Datetime(required=True)
    wp_id = fields.Integer('Wordpress Post ID', required=True, index=True)
    url = fields.Char('URL')
    image_url = fields.Char()
    post_type = fields.Selection([
        ('posts', 'News'),
        ('agendas', 'Agenda'),
        ('download', 'Download')
    ])
    category_id = fields.Many2one('wp.post.category', 'Category')
    lang = fields.Selection('select_lang', 'Language', required=True)
    display_on_hub = fields.Boolean(
        default=True, help='Deactivate in order to hide tiles in App.')

    _sql_constraints = [
        ('wp_unique', 'unique(wp_id)', 'This post already exists')
    ]

    @api.model
    def select_lang(self):
        langs = self.env['res.lang'].search([])
        return [(lang.code, lang.name) for lang in langs]

    @api.onchange('display_on_hub')
    def onchange_display_on_hub(self):
        """
        If the user activate the display on hub, notify that the wordpress
        post should have some content.
        :return: warning to user
        """
        if self.display_on_hub:
            return {
                'warning': {
                    'title': _("Warning"),
                    'message': _(
                        "This post was disabled probably because it doesn't "
                        "have a content. Please make sure the post has a "
                        "body to avoid any display issues in the mobile app.")
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
        wp_host = config.get('wordpress_host')
        if not wp_host:
            raise UserError(_("Please add wp_host in your configuration"))
        # This is standard Wordpress REST API URL
        wp_api_url = 'https://' + wp_host + '/wp-json/wp/v2/' + post_type
        # This is for avoid loading all post content
        params = {'context': 'embed'}
        category_obj = self.env['wp.post.category']
        found_ids = []
        try:
            with wp_requests.Session() as requests:
                for lang in self._supported_langs():
                    params['lang'] = lang.code[:2]
                    wp_posts = requests.get(wp_api_url, params=params).json()
                    _logger.info('Processing posts in %s', lang.name)
                    for i, post_data in enumerate(wp_posts):
                        _logger.info("...processing post %s/%s",
                                     str(i+1), str(len(wp_posts)))
                        post_id = post_data['id']
                        found_ids.append(post_id)
                        if self.search([('wp_id', '=', post_id)]):
                            # Skip post already fetched
                            continue

                        content_empty = False
                        self_url = post_data['_links']['self'][0]['href']
                        content = requests.get(self_url).json()
                        if not content['content']['rendered']:
                            # We won't display the post in hub when content
                            # is empty
                            content_empty = True
                        try:
                            # Fetch image for thumbnail
                            image_json_url = post_data['_links'][
                                'wp:featuredmedia'][0]['href']
                            image_json = requests.get(image_json_url).json()
                            if '.jpg' in image_json['media_details']['sizes'][
                                    'medium']['source_url']:
                                image_url = \
                                    image_json['media_details']['sizes'][
                                        'medium']['source_url']
                            else:
                                image_url = image_json['source_url']
                        except KeyError:
                            # Some post images may not be accessible
                            image_url = False
                            _logger.warning('WP Post ID %s has no image',
                                            str(post_id))
                        # Fetch post category
                        try:
                            category_data = [
                                d for d in post_data['_links']['wp:term']
                                if d['taxonomy'] == 'category'
                            ][0]
                            category_json_url = category_data['href']
                            category_name = requests.get(
                                category_json_url).json()[0]['name']
                            category = category_obj.search([
                                ('name', '=', category_name)])
                            if not category:
                                category = category_obj.create({
                                    'name': category_name
                                })
                        except (IndexError, KeyError):
                            _logger.info('WP Post ID %s has no category.',
                                         str(post_id))
                            category = category_obj
                        # Cache new post in database
                        self.create({
                            'name': post_data['title']['rendered'],
                            'date': post_data['date'],
                            'wp_id': post_id,
                            'url': post_data['link'],
                            'image_url': image_url,
                            'post_type': post_type,
                            'category_id': category.id,
                            'lang': lang.code,
                            'display_on_hub': not content_empty
                        })
            # Delete unpublished posts
            self.search([('wp_id', 'not in', found_ids),
                         ('post_type', '=', post_type)]).unlink()
            _logger.info("Fetch Wordpress Posts finished!")
        except ValueError:
            _logger.warning("Error fetching wordpress posts", exc_info=True)
        return True

    @api.model
    def _supported_langs(self):
        """
        Will fetch all wordpress posts in the given langs
        :return: res.lang recordset
        """
        return self.env['res.lang'].search([('code', '!=', 'en_US')])
