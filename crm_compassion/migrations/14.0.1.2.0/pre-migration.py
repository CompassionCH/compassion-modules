def migrate(cr, version):
    cr.execute(
        """
        DELETE FROM ir_model_fields_selection WHERE field_id = ANY (
            SELECT id FROM ir_model_fields
            WHERE name='direction' AND model IN (
                'partner.log.interaction.wizard',
                'partner.log.other.interaction'
            )
        )
    """
    )
