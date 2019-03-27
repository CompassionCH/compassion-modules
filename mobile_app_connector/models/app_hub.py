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

from ..mappings.compassion_child_mapping import MobileChildMapping
from ..mappings.wp_post_mapping import WPPostMapping
from ..mappings.mobile_app_tile_mapping import TileMapping
from odoo import api, models, _

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
        children = sponsorships.mapped('child_id')
        # Start with child selector tile or sponsor a child (when no child)
        first_tile = {
            "SortOrder": 1001,
        }
        if children:
            first_tile.update({
                "ActionDestination": "Child selector",
                "Type": "Child",
                "SubType": "CH1",
                "Title": _("Thank you!"),
                "Body": _("You're changing {} lives").format(len(children)),
            })
        else:
            first_tile.update({
                # TODO Replace with child_sponsor destination when implemented
                "ActionDestination": "Feedback overlay",
                "Type": "Miscellaneous",
                "SubType": "MI2",
                "Title": _("Sponsor a child"),
                "Body": _("Release one child from extreme poverty today"),
            })
        messages = [
            first_tile,
        ]
        child_mapping = MobileChildMapping(self.env)
        children_data = []
        for child in children:
            children_data.append(child_mapping.get_connect_data(child))
        messages.extend(children.get_mobile_app_tiles())
        messages.extend(self._fetch_wordpress_tiles(**pagination))
        res = self._construct_hub_message(
            partner_id, messages, children_data, **pagination)
        return res

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    @api.model
    def _public_hub(self, **pagination):
        """
                Gets the cached wordpress posts
                :return: List of JSON messages for use in the hub.
                """
        available_tiles = self.env['mobile.app.tile'].search([
            ('enabled', '=', 'Active')
        ])
        tiles = []
        if available_tiles:
            start = int(pagination.get('start', 0))
            number_mess = int(pagination.get('limit', 1000))
            offset = (start % number_mess) * self.LIMIT_PUBLIC_TILES
            tile_mapping = TileMapping(self.env)
            for post in available_tiles[offset:self.LIMIT_PUBLIC_TILES]\
                    .sorted(key=lambda r: r.type_id.view_order + r.view_order):
                tiles.append(tile_mapping.get_connect_data(post))

        """
        In Public mode, we return an invite to login and a feedback tile.
        The news and agenda feeds are fetched from the website.
        TODO Display a tile for inviting to sponsor a child
        (this can be done when we add the relevant action on the app)
        TODO See if we send a link for a video (could be from website)
        TODO Add tiles for fund donations (define how to order them or enable
        dynamic configuration from Odoo user interface).
        :return: list of tiles displayed in mobile app.
        """
        # messages = [
        #     # Login
        #     {
        #         "ActionDestination": "Login overlay",
        #         "ActionText": _("Login"),
        #         "Body": _("We've noticed you're not currently logged in"),
        #         "SortOrder": 1007,
        #         "SubType": "MI1",
        #         "Title": "Log in",
        #         "Type": "Miscellaneous"
        #     },
        #     # Feedback TODO move in mobile.app.tile object (see AP-37)
        #     {
        #         "ActionDestination": "Feedback overlay",
        #         "ActionText": _("Feedback"),
        #         "Body": _("We'd love to hear what you think about our App"),
        #         "SortOrder": 1007,
        #         "SubType": "MI2",
        #         "Title": "Your comments",
        #         "Type": "Miscellaneous"
        #     },
        #     # Child survival donation TODO move in mobile.app.tile (AP-37)
        #     {
        #         "ActionDestination": "Give overlay",
        #         "ActionText": _("Give a Donation"),
        #         "Appeal": {
        #             "FundType": "Child Survival Programme"
        #         },
        #         "Body": _("Child survival"),
        #         "SortOrder": 1006,
        #         "SubType": "GI1",
        #         "Title": _("Help a mother and her baby today"),
        #         "Type": "Giving"
        #     },
        # ]
        # tiles.extend(self._fetch_wordpress_tiles(**pagination))
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

    def _construct_hub_message(self, partner_id, messages, children=False,
                               start=0, limit=100, **kwargs):
        """
        Wrapper for constructing the JSON message for the mobile app, for
        the main hub display.
        :param partner_id: Connected partner
        :param messages: List of messages to send (will display tiles in
                         app)
        :param children: List of children of the sponsor (JSON data)
        :param start: optional start for loading subset of messages
        :param limit: optional limit for loading subset of messages
        :param kwargs: other request parameters (ignored)
        :return: JSON compatible data for mobile app
        """
        base_url = self.env['ir.config_parameter'].get_param(
            'web.base.url') + '/mobile-app-api'
        hub_endpoint = '/hub/{}?start={}&limit={}'
        self._assign_order(messages)
        return {
            "Children": children or [],
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
        }

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
