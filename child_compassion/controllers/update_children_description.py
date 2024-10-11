from odoo import http
from odoo.http import request
from odoo import api


class UpdateChildrenDescription(http.Controller):
    @http.route('/update_children_description/all', type='http', auth='none')
    def update_all(self):
        children = request.env['compassion.child'].sudo().search([])
        html_result = '<html><body><ul>'
        for child in children:
            html_result += "<li> %s </li>" % self.update_child_descriptions(child)
        html_result += '</ul></body></html>'
        return html_result

    @http.route("/update_children_description", type='http', auth='none')
    def update_child(self, child_id):
        child = request.env['compassion.child'].sudo().browse(int(child_id))
        return self.update_child_descriptions(child)

    @api.model
    def update_child_descriptions(self, child):
        descriptions = request.env['compassion.child.description'].sudo().search(
            [('child_id', '=', child.id)], order='write_date desc', limit=1)
        if len(descriptions) > 0:
            description = descriptions[0]
            description._generate_all_translations()
            return "%s (%s) updated" % (child.name, child.id)
        return "Error with %s (%s) : description not found" % (child.name, child.id)
    
