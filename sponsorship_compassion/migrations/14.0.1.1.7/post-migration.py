def migrate(cr, version):
    if version:
        cr.execute(
            "UPDATE recurring_contract SET christmas_invoice = 0,birthday_invoice = 0  where payment_mode_id not in (select id from account_payment_mode where payment_method_code like '%direct_debit')"
        )
