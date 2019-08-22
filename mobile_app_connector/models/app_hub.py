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
    LIMIT_WORDPRESS_TILES = 20
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
        # TODO For now we only display the contracts for which the sponsor
        #  is correspondent (to avoid viewing letters when he doesn't write)
        sponsorships = (partner.contracts_correspondant +
                        partner.contracts_fully_managed).filtered('is_active')
        unpaid = partner.contracts_fully_managed.filtered(
            lambda c: not c.is_active and not c.parent_id and
            (c.state in ['waiting', 'draft']))
        children = sponsorships.mapped('child_id')
        sponsorship_amounts = sponsorships.mapped('total_amount')
        unpaid_children = unpaid.mapped('child_id')
        unpaid_amounts = unpaid.mapped('total_amount')

        letters = self.env['correspondence'].search([
            ('partner_id', '=', partner_id),
            ('sponsorship_id', 'in', sponsorships.ids)
        ])

        available_tiles = self.env['mobile.app.tile'].search([
            ('visibility', '!=', 'public')
        ])
        products = self.env['product.product'].sudo().search([
            ('mobile_app', '=', True)
        ])
        tile_data = {
            'res.partner': partner,
            'recurring.contract': sponsorships,
            'compassion.child': children,
            'product.product': products,
            'correspondence': letters,
        }
        unpaid_data = {
            'recurring.contract': unpaid
        }
        # TODO handle pagination properly
        limit = int(pagination.get('limit', 1000))
        messages = available_tiles[:limit].render_tile(tile_data)

        # GI7 is treated separately because it needs unpaid sponsorships
        msg_tmp = self.env['mobile.app.tile'].search([
            ('subtype_id', '=',
             self.env.ref('mobile_app_connector.tile_subtype_gi7').id)
        ]).render_tile(unpaid_data)
        messages.extend(msg_tmp)
        messages.extend(self._fetch_wordpress_tiles(**pagination))
        res = self._construct_hub_message(
            partner_id, messages, children, **pagination)

        # Amount for monthly sponsorship
        res.update({'SponsorshipAmounts': sponsorship_amounts})

        # Handle children with awaiting payment
        if unpaid_children:
            unpaid_dict = unpaid_children.get_app_json(
                multi=True, wrapper='UnpaidChildren')
            res.update(unpaid_dict)
            res.update({'UnpaidAmounts': unpaid_amounts})

        # To allow donation for users that are not sponsor
        res.update({
            'SupporterGroupId': partner_id,
            'SupporterId': partner_id,
        })

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
        :return: list of tiles displayed in mobile app.
        """
        available_tiles = self.env['mobile.app.tile'].search([
            ('visibility', '!=', 'private')
        ]).sorted(key=lambda t: t.view_order + t.subtype_id.view_order)
        tiles = []
        # Fetch products for fund donations
        products = self.env['product.product'].sudo().search([
            ('mobile_app', '=', True)
        ])
        if available_tiles:
            start = int(pagination.get('start', 0))
            number_mess = int(pagination.get('limit', 1000))
            offset = (start % number_mess) * self.LIMIT_PUBLIC_TILES
            tiles.extend(
                available_tiles[offset:self.LIMIT_PUBLIC_TILES].render_tile({
                    'product.product': products})
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
            ('lang', '=', self.env.lang),
            ('display_on_hub', '=', True),
            ('category_ids.name', '=', 'Afficher dans le hub')
        ])
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

        We divide the tiles in three group: promoted, fixed and the rest.

        The promoted group will appear first and is constitued of new letters
        and a few other tiles. This can be tweaked in the recent_content dict.

        The fixed group has all the children tiles that we always what to be
        displayed not too far down. We take all the tiles of a type listed in
        fixed group tiles.

        The rest group has all the tile remaining.

        We favor content which is marked as unread and otherwise sort on the
        OrderDate attribute. This attribute is set in the mapping file of each
        tile type with a fallback on the creation date of the tile.


        ViewOrder values assigned:

        0    Login tile
        1000 Unread + recently read letters

        2000 Other promoted content

        3000 Fixed content (children, ...)

        4000 Rest of tiles

        :param messages: List of JSON messages that will be sent to app
        :return: None
        """

        category_length = 500
        gap = 500
        login_order = 0
        unread_letter_order = login_order + category_length + gap
        promoted_content_order = unread_letter_order + category_length + gap
        fixed_content_order = promoted_content_order + category_length + gap
        rest_of_tiles_order = fixed_content_order + category_length + gap

        to_order = [m for m in messages if m['IsAutomaticOrdering']]
        to_order.sort(key=lambda m: m["OrderDate"], reverse=True)

        letters = {'tiles': [], 'max_number_tile': 1}
        prayers = {'tiles': [], 'max_number_tile': 1}
        community = {'tiles': [], 'max_number_tile': 0}
        stories = {'tiles': [], 'max_number_tile': 0}
        giving = {'tiles': [], 'max_number_tile': 1}
        pictures = {'tiles': [], 'max_number_tile': 1}
        child_fact = {'tiles': [], 'max_number_tile': 0}
        # tiles that will be in first group of displayed tiles
        recent_content = {
            "CH1": {'tiles': [], 'max_number_tile': 0},
            "CH2": pictures,
            "CH3": child_fact,
            "CH-T1": {'tiles': [], 'max_number_tile': 1},
            "CH_T2": child_fact,
            "CO1": community,
            "CO2": community,
            "CO3": community,
            "CO4": community,
            "GI1": giving,
            "GI3": giving,
            "GI5": giving,
            "GI7": giving,
            "GI_T1": giving,
            "LE1": letters,
            "LE_T1": {'tiles': [], 'max_number_tile': 2},
            "LE_T2": {'tiles': [], 'max_number_tile': 0},
            'LE_T3': letters,
            "PR1": prayers,
            "PR_T1": prayers,
            "PR-T2": prayers,
            "PR2": prayers,
            "ST_T1": stories,
            "ST_T2": stories,
            "ST1": stories,
            "MI1": {'tiles': [], 'max_number_tile': 1},
            "MI2": {'tiles': [], 'max_number_tile': 0},
        }
        fixed_group = []
        fixed_group_tiles = ["CH1", "CO1", "CO2", "CO3", "CO4"]
        rest_group = []

        for tile in to_order:
            recent_group = recent_content[tile['SubType']]
            if recent_group['max_number_tile'] > len(recent_group['tiles']) \
                    and (tile['SubType'] != 'LE_T1' or
                         tile.get('UnReadRecently')):
                recent_group['tiles'].append(tile)
            elif tile['SubType'] in fixed_group_tiles:
                fixed_group.append(tile)
            else:
                rest_group.append(tile)

        for subtype, tiles in recent_content.iteritems():
            if subtype == 'LE_T1':
                for tile in tiles['tiles']:
                    tile['SortOrder'] = unread_letter_order
                    unread_letter_order += \
                        category_length // len(tiles['tiles'])
                tiles['tiles'] = []
            else:
                for tile in tiles['tiles']:
                    tile['SortOrder'] = promoted_content_order
                    promoted_content_order += 10
                tiles['tiles'] = []

        for tile in fixed_group:
            tile['SortOrder'] = fixed_content_order
            fixed_content_order += category_length // len(fixed_group)

        rest_group.sort(key=lambda x: (x.get('UnReadRecently', False),
                                       x['OrderDate']), reverse=True)
        for tile in rest_group:
            tile['SortOrder'] = rest_of_tiles_order
            rest_of_tiles_order += category_length // len(rest_group)

        for tile in to_order:
            # login tile should be first
            if tile['SubType'] == "MI1":
                tile['SortOrder'] = login_order

        messages.sort(key=lambda m: int(m["SortOrder"]))
