from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    existing_param = env['ir.config_parameter'].search([
        ('key', '=', 'web.external.url')])
    if existing_param:
        openupgrade.add_xmlid(
            env.cr, 'cms_form_compassion', 'external_url', 'ir.config_parameter',
            existing_param.id, True)
