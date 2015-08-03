## Migration instructions

### To migrate properly you need to launch the following commands

1. `openerp-server -c 'file.conf' -d 'database_name' -u recurring_contract`
2. `openerp-server -c 'file.conf' -d 'database_name' -i contract_compassion`
3. `openerp-server -c 'file.conf' -d 'database_name' -u all`
4. `openerp-server -c 'file.conf' -d 'database_name' -i account_analytic_attribution,child_sync_typo3,partner_compassion_switzerland,sponsorship_switzerland`
