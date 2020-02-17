from openupgradelib import openupgrade

@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Get all support mail.templates
    support_templates = env['mail.template'].search([('model', '=', 'crm.claim')])

    crm_claim_model = env['ir.model'].search([('model', '=', 'crm.claim')]).id

    # Create a communication rule for each of them
    for template in support_templates:
        env['partner.communication.config'].create({
            'name': template['name'],
            'send_mode': 'digital_only',
            'model_id': crm_claim_model,
            'email_template_id': template.id
        })