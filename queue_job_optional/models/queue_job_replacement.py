import logging
from contextlib import closing, contextmanager

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class QueueJobReplacement(models.Model):
    _name = "queue.job.replacement"
    _description = "Queued Job for later execution"

    res_model = fields.Char(required=True)
    res_ids = fields.Char(required=True)
    job_function = fields.Char(required=True)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    context = fields.Char()
    job_args = fields.Char()
    eta = fields.Datetime(default=fields.Datetime.now, required=True, index=True)
    start_date = fields.Datetime()
    description = fields.Char()
    priority = fields.Integer(default=10, required=True, index=True)
    channel = fields.Char()
    identity_key = fields.Char()
    job_result = fields.Text()
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("done", "Done"),
            ("failed", "Failed"),
        ],
        default="pending",
        index=True,
        required=True,
    )
    parent_job_id = fields.Many2one("queue.job.replacement")
    is_predecessor_complete = fields.Boolean(
        compute="_compute_is_predecessor_complete",
        search="_search_is_predecessor_complete",
    )

    def _compute_is_predecessor_complete(self):
        for job in self:
            job.is_predecessor_complete = (
                not job.parent_job_id or job.parent_job_id.state == "done"
            )

    @staticmethod
    def _parse_payload(value, default):
        if not value:
            return default
        return safe_eval(value)

    def _search_is_predecessor_complete(self, operator, value):
        if operator not in ["=", "!="]:
            raise UserError(
                _("Unsupported operator for is_predecessor_complete search.")
            )
        if value:
            domain = [
                "|",
                ("parent_job_id", "=", False),
                ("parent_job_id.state", "=", "done"),
            ]
        else:
            domain = [
                ("parent_job_id", "!=", False),
                ("parent_job_id.state", "!=", "done"),
            ]
        return domain

    @api.model_create_multi
    def create(self, vals_list):
        field_names = self._fields.keys()
        res = self.browse()
        to_create = []
        for vals in vals_list:
            for key in list(vals.keys()):
                if key not in field_names:
                    vals.pop(key)
                if key == "parent_job_id" and not isinstance(vals[key], int):
                    vals[key] = vals[key].id
            if identity_key := vals.get("identity_key"):
                processing_job = self.search_count(
                    [("identity_key", "=", identity_key), ("state", "=", "processing")]
                )
                if processing_job:
                    # Prevent running the duplicate job
                    vals.update(
                        {
                            "state": "failed",
                            "job_result": _(
                                "Another job(s) with same identity key "
                                "is already running."
                            ),
                        }
                    )
                pending_job = self.search(
                    [
                        ("identity_key", "=", identity_key),
                        ("state", "=", "pending"),
                    ]
                )
                if len(pending_job) > 1:
                    raise ValidationError(
                        _("Another job with same identity key is already scheduled.")
                    )
                if pending_job:
                    if self._parse_payload(
                        pending_job.job_args, default=()
                    ) != self._parse_payload(vals["job_args"], default=()):
                        raise ValidationError(
                            _(
                                "Another job with same identity key is already "
                                "scheduled with different arguments."
                            )
                        )
                    pending_res_ids = self._parse_payload(
                        pending_job.res_ids, default=[]
                    )
                    current_res_ids = self._parse_payload(vals["res_ids"], default=[])
                    pending_job.res_ids = str(
                        list(set(pending_res_ids + current_res_ids))
                    )
                    res |= pending_job
                    continue
            to_create.append(vals)
        res |= super().create(to_create)
        return res

    def cron_run_jobs(self):
        search_domain = [
            ("state", "=", "pending"),
            ("eta", "<=", fields.Datetime.now()),
        ]
        total_jobs = self.search_count(search_domain)
        jobs = self.search(
            search_domain + [("is_predecessor_complete", "=", True)],
            order="priority,eta",
            limit=100,
        )
        for job in jobs:
            try:
                with self._do_in_new_env(new_cr=True) as new_env:
                    job_new_env = new_env[self._name].browse(job.id)
                    job_new_env.write(
                        {"state": "processing", "start_date": fields.Datetime.now()}
                    )
                    # Safe to commit at this point to ensure the state is set
                    # pylint: disable=invalid-commit
                    job_new_env.env.cr.commit()
                    records = (
                        new_env[job_new_env.res_model]
                        .with_user(job_new_env.user_id)
                        .with_company(job_new_env.company_id)
                        .with_context(
                            **self._parse_payload(job_new_env.context, default={})
                        )
                        .browse(self._parse_payload(job_new_env.res_ids, default=[]))
                    )
                    job_function = getattr(records, job_new_env.job_function)
                    job_result = job_function(
                        *self._parse_payload(job_new_env.job_args, default=())
                    )
                    job_new_env.write(
                        {
                            "state": "done",
                            "job_result": str(job_result),
                        }
                    )
            except Exception as e:
                _logger.error("Error processing job", exc_info=True)
                job.write({"state": "failed", "job_result": str(e)})
        if jobs and total_jobs > len(jobs):
            self.env.ref(
                "queue_job_optional.ir_cron_queue_job_replacement_process"
            ).sudo()._trigger()

    def requeue(self):
        self.write({"state": "pending"})

    def set_done(self):
        self.write({"state": "done"})

    def drop_job(self, identity_key):
        if "queue.job" in self.env:
            job = (
                self.env["queue.job"]
                .sudo()
                .search(
                    [
                        ("identity_key", "=", identity_key),
                        ("state", "not in", ["done", "cancelled"]),
                    ]
                )
            )
            job.button_done()
            job.unlink()
        else:
            job = self.search(
                [("identity_key", "=", identity_key), ("state", "!=", "done")]
            )
            job.set_done()
            job.unlink()
        return True

    def open_related(self):
        self.ensure_one()
        parsed_ids = self._parse_payload(self.res_ids, default=[])
        if isinstance(parsed_ids, int):
            record_ids = [parsed_ids]
        elif isinstance(parsed_ids, (list | tuple | set)):
            record_ids = [int(rec_id) for rec_id in parsed_ids]
        else:
            raise UserError(_("Related record ids are invalid."))

        if not record_ids:
            raise UserError(_("No related record ids are defined for this job."))

        action = {
            "name": _("Related records"),
            "type": "ir.actions.act_window",
            "res_model": self.res_model,
            "target": "current",
        }
        if len(record_ids) == 1:
            action.update(
                {
                    "res_id": record_ids[0],
                    "view_mode": "form",
                }
            )
        else:
            action.update(
                {
                    "view_mode": "list,form",
                    "domain": [("id", "in", record_ids)],
                }
            )
        return action

    @contextmanager
    def _do_in_new_env(self, new_cr=False):
        """Context manager that yields a new environment
        Copied from OCA storage/fs_attachment module
        Using a new Odoo Environment thus a new PG transaction.
        """
        if new_cr:
            with closing(self.env.registry.cursor()) as cr:
                try:
                    yield self.env(cr=cr)
                except Exception:
                    cr.rollback()
                    raise
                else:
                    # disable pylint error because this is a valid commit,
                    # we are in a new env
                    cr.commit()  # pylint: disable=invalid-commit
        else:
            # make a copy
            yield self.env()
