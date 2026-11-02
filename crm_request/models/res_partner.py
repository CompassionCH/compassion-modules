import logging

from psycopg2 import OperationalError

from odoo import models

from ..tools import partner_cleanup as cleanup

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _merge_duplicates(self, duplicate_ids):
        """Job queued by the migration of the duplicated contacts (T3642): merge
        the duplicates in this main contact. The ones that cannot be merged are
        flagged with an activity.
        :param duplicate_ids: ids of the contacts to merge in self
        """
        self.ensure_one()
        wizard = self.env["base.partner.merge.automatic.wizard"]
        failed = self.browse()
        for duplicate in self.browse(duplicate_ids).exists():
            try:
                with self.env.cr.savepoint():
                    cleanup.fix_visitor_tokens(self.env.cr, [self.id, duplicate.id])
                    wizard._merge(
                        [self.id, duplicate.id], dst_partner=self, extra_checks=False
                    )
            except OperationalError:
                # Concurrent update, the job is retried
                raise
            except Exception:
                _logger.exception(
                    "T3642: could not merge %s into %s", duplicate.id, self.id
                )
                failed |= duplicate
        if failed:
            cleanup.schedule_review(
                self.env,
                self,
                "Review possible duplicates of this contact",
                [(p, "possible duplicate, the merge failed") for p in failed],
            )
        return True
