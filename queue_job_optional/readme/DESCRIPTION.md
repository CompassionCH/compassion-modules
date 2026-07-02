Abstract the queue_job module from OCA to use it when available and fallback to a
dedicated CRON when the module is not installed. This is helpful for sharing code
between odoo.sh environment and dedicated environment because odoo.sh discourages
the use of the queue_job module.