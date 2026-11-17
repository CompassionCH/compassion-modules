# partner_id, child_id and project_id were non-stored related fields on
# sponsorship.gift: values set on gifts without sponsorship were lost and
# gifts with a sponsorship have empty columns. Fill them from the sponsorship.


def migrate(cr, version):
    cr.execute(
        """
        UPDATE sponsorship_gift g
        SET partner_id = c.correspondent_id,
            child_id = c.child_id,
            project_id = ch.project_id
        FROM recurring_contract c
        LEFT JOIN compassion_child ch ON ch.id = c.child_id
        WHERE c.id = g.sponsorship_id
          AND (
            g.partner_id IS DISTINCT FROM c.correspondent_id
            OR g.child_id IS DISTINCT FROM c.child_id
            OR g.project_id IS DISTINCT FROM ch.project_id
          )
        """
    )
