# -*- coding: utf-8 -*-
from odoo import http

# class ResCountryStatistics(http.Controller):
#     @http.route('/res_country_statistics/res_country_statistics/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/res_country_statistics/res_country_statistics/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('res_country_statistics.listing', {
#             'root': '/res_country_statistics/res_country_statistics',
#             'objects': http.request.env['res_country_statistics.res_country_statistics'].search([]),
#         })

#     @http.route('/res_country_statistics/res_country_statistics/objects/<model("res_country_statistics.res_country_statistics"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('res_country_statistics.object', {
#             'object': obj
#         })