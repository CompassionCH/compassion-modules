def migrate(cr, version):
    cr.execute(
        """
    UPDATE partner_communication_revision_history SET update_user_id = write_uid
    """
    )
