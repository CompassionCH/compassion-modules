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

from ..mappings.wp_post_mapping import WPPostMapping
from odoo import api, models

_logger = logging.getLogger(__name__)


class AppHub(models.AbstractModel):
    """
    This Class holds the logic to construct the Mobile App Hub.
    It generates and orders the list of tiles that will be displayed at the
    user.
    """
    _name = 'mobile.app.hub'

    # This will limit the number of tiles displayed in one screen
    # This can be later put in some settings if this needs to be changed
    LIMIT_WORDPRESS_TILES = 10
    LIMIT_PUBLIC_TILES = 10

    @api.model
    def mobile_get_message(self, partner_id, **pagination):
        """
        This is the main message sent from the Mobile App in order to construct
        the HUB of the sponsor. It returns a list of messages that will
        correspond to the tiles displayed in the app. Each message has
        an type, a destination action, a priority for order and some data.
        https://confluence.compassion.ch/display/AM/GET+Message
        :param partner_id: the connected partner (0 for public use)
        :param pagination: can contain start and limit numbers,
                           used for loading a subset of messages.
        :return: list of messages to display in app
        """
        if not partner_id:
            # Public mode is handled differently.
            return self._public_hub(**pagination)

        partner = self.env['res.partner'].browse(partner_id)
        sponsorships = partner.sponsorship_ids.filtered('is_active')
        # sponsorships = self.env['recurring.contract'].sudo().search([
        #     ('partner_id', '=', partner_id),
        #     ('is_active', '=', 'active')
        # ])
        children = sponsorships.mapped('child_id')

        available_tiles = self.env['mobile.app.tile'].search([
            ('is_active', '=', True),
            ('visibility', '!=', 'public')
        ])
        # TODO this is for testing purpose
        #   Implement a way for defining donation products that will show in
        #   tiles (AP-45)
        fund = self.env.ref('contract_compassion.product_category_fund').sudo()
        product = self.env['product.product'].sudo().search([
            ('categ_id', '=', fund.id)
        ], limit=1)
        tile_data = {
            'res.partner': partner,
            'recurring.contract': sponsorships,
            'compassion.child': children,
            'product.product': product,

        }
        # TODO handle pagination properly
        limit = int(pagination.get('limit', 1000))
        messages = available_tiles[:limit].render_tile(tile_data)
        messages.extend(self._fetch_wordpress_tiles(**pagination))
        res = self._construct_hub_message(
            partner_id, messages, children, **pagination)
        return res

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.model
    def _public_hub(self, **pagination):
        """
        In Public mode, we return tiles defined in mobile.app.tile object
        The news and agenda feeds are fetched from the website.
        TODO Display a tile for inviting to sponsor a child
        (this can be done when we add the relevant action on the app)
        TODO See if we send a link for a video (could be a wordpress post)
        TODO Add tiles for fund donations
            (see how to configure with mobile.app.tile).
        :return: list of tiles displayed in mobile app.
        """
        available_tiles = self.env['mobile.app.tile'].search([
            ('is_active', '=', True),
            ('visibility', '!=', 'private')
        ]).sorted(key=lambda t: t.view_order + t.subtype_id.view_order)
        tiles = []
        if available_tiles:
            start = int(pagination.get('start', 0))
            number_mess = int(pagination.get('limit', 1000))
            offset = (start % number_mess) * self.LIMIT_PUBLIC_TILES
            tiles.extend(
                available_tiles[offset:self.LIMIT_PUBLIC_TILES].render_tile()
            )

        # Fetch tiles from Wordpress
        tiles.extend(self._fetch_wordpress_tiles(**pagination))
        return self._construct_hub_message(0, tiles, **pagination)

    def _fetch_wordpress_tiles(self, **pagination):
        """
        Gets the cached wordpress posts
        :return: List of JSON messages for use in the hub.
        """
        available_posts = self.env['wp.post'].search([
            ('lang', '=', self.env.lang)])
        messages = []
        if available_posts:
            start = int(pagination.get('start', 0))
            number_mess = int(pagination.get('limit', 1000))
            offset = (start % number_mess) * self.LIMIT_WORDPRESS_TILES
            wp_mapping = WPPostMapping(self.env)
            for post in available_posts[offset:self.LIMIT_WORDPRESS_TILES]:
                messages.append(wp_mapping.get_connect_data(post))
        return messages

    def _construct_hub_message(self, partner_id, messages, children=None,
                               start=0, limit=100, **kwargs):
        """
        Wrapper for constructing the JSON message for the mobile app, for
        the main hub display.
        :param partner_id: Connected partner
        :param messages: List of messages to send (will display tiles in
                         app)
        :param children: recordset of compassion.child
        :param start: optional start for loading subset of messages
        :param limit: optional limit for loading subset of messages
        :param kwargs: other request parameters (ignored)
        :return: JSON compatible data for mobile app
        """
        base_url = self.env['ir.config_parameter'].get_param(
            'web.base.url') + '/mobile-app-api'
        hub_endpoint = '/hub/{}?start={}&limit={}'
        self._assign_order(messages)
        if children is None:
            children = self.env['compassion.child']
        result = children.get_app_json(multi=True)

        result.update({
            "Size": len(messages),  # Total size of available messages
            "Start": start,  # Starting point of message subset returned
            "Limit": limit,  # Limit number of messages returned
            "_Links": {  # This is used for lazy load of messages in App.
                "Base": base_url,
                "Next": hub_endpoint.format(
                    partner_id, int(start) + int(limit), limit),
                "Self": base_url + hub_endpoint.format(partner_id, start,
                                                       limit),
            },
            "Messages": messages[int(start):min(len(messages), int(limit))],
        })
        return result

    def _assign_order(self, messages):
        """
        This will update the list of messages and assign the SortOrder
        value for each message, in order to control the order of the displayed
        tiles inside the mobile app. The algorithm for determining this
        order can be tweaked here.
        TODO Implement a robust algorithm that can easily be tweaked by user
        (with settings in user interface for instance)
        :param messages: List of JSON messages that will be sent to app
        :return: None
        """
        base_score_mapping = {
            "Miscellaneous": 1000,
            "Child": 1000,
            "Letter": 2000,
            "Story": 3000,
            "Community": 4000,
            "Giving": 5000,
            "Prayer": 6000,
        }
        for i, message in enumerate(messages):
            base_score = base_score_mapping.get(message.get("Type"), 10000)
            message["SortOrder"] = str(base_score + i)
        messages.sort(key=lambda m: int(m["SortOrder"]))
