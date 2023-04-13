# -*- coding: utf-8 -*-
# from odoo import http


# class MisBuilderSpnInfo(http.Controller):
#     @http.route('/mis_builder_spn_info/mis_builder_spn_info/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mis_builder_spn_info/mis_builder_spn_info/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mis_builder_spn_info.listing', {
#             'root': '/mis_builder_spn_info/mis_builder_spn_info',
#             'objects': http.request.env['mis_builder_spn_info.mis_builder_spn_info'].search([]),
#         })

#     @http.route('/mis_builder_spn_info/mis_builder_spn_info/objects/<model("mis_builder_spn_info.mis_builder_spn_info"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mis_builder_spn_info.object', {
#             'object': obj
#         })
