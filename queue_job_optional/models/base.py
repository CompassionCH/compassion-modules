from datetime import timedelta

from odoo import fields, models


class Base(models.AbstractModel):
    """The base model, which is implicitly inherited by all models.

    A new :meth:`~with_delay` method is added on all Odoo Models, allowing to
    postpone the execution of a job method in an asynchronous process.
    """

    _inherit = "base"

    def with_delay_sh(self, job_function, *job_args, **delay_args):
        """Returns a proxy object that will enqueue the method call instead of
        executing it immediately.

        :param job_function: The name of the method to be executed asynchronously.
        :param job_args: Positional arguments to be passed to the `job_function`.
                         These arguments will be serialized and passed to the
                         asynchronous job.
        :param delay_args: Keyword arguments to control the job's execution.
            Possible arguments include:
            *   **eta** (datetime or int/float): The earliest time at which the job
                should be executed. If an int or float, it represents seconds from now.
                Defaults to `fields.Datetime.now()` if not specified.
            *   **priority** (int): The priority of the job. Lower numbers indicate
                higher priority (e.g., 0 is higher priority than 10).
            *   **channel** (str): The channel to which the job should be sent.
                Jobs within the same channel are typically executed sequentially.
            *   **split** (int): If greater than 0, the current recordset (`self`)
                will be split into chunks of this size, and a separate job will be
                created for each chunk. Each job will then operate on its respective
                chunk of records.
            *   **chain** (bool): If `split` is used and `chain` is True, the
                generated jobs will be chained, meaning each job will only start
                after the previous one in the chain has completed successfully.
            *   **parent_job_id** (queue.job record): An existing delayable object
                (only applicable when the `queue_job` module is installed) to which
                the new job will be linked as a child.
                When queue_job is not installed, this should be the id of the parent
                queue.job.replacement record.
                The child job will be executed when the parent job is done.
            * **wait_for_children** (boolean): Don't run the job to add children jobs
                to the queue, but wait for all children jobs to be created.
        """
        queue_job_installed = "queue.job" in self.env
        split = delay_args.pop("split", 0)
        chain = delay_args.pop("chain", False)
        no_delay = self.env.context.get("queue_job__no_delay")
        if queue_job_installed:
            parent_job = delay_args.pop("parent_job_id", None)
            wait_for_children = delay_args.pop("wait_for_children", False)
            if not no_delay and (split or parent_job is not None or wait_for_children):
                job = getattr(self.delayable(), job_function)(*job_args).set(
                    **delay_args
                )
                if split:
                    job = job.split(split, chain=chain)
                if parent_job is not None:
                    parent_job.on_done(job)
                if not wait_for_children:
                    job.delay()
                return job
            else:
                return getattr(self.with_delay(**delay_args), job_function)(*job_args)
        else:
            if no_delay:
                return getattr(self, job_function)(*job_args)
            eta = delay_args.pop("eta", None)
            if isinstance(eta, (int | float)):
                eta = fields.Datetime.now() + timedelta(seconds=eta)
            elif eta is None:
                eta = fields.Datetime.now()
            create_vals = [
                {
                    "res_model": self._name,
                    "res_ids": str(self[i : i + max(split, 1)].ids),
                    "job_function": job_function,
                    "job_args": str(job_args),
                    "user_id": self.env.user.id,
                    "company_id": self.env.company.id,
                    "context": str(self.env.context),
                    "eta": eta,
                    **delay_args,
                }
                for i in range(0, max(len(self), 1), max(split, 1))
            ]
            if chain:
                job = self.env["queue.job.replacement"].sudo()
                for vals in create_vals:
                    vals["parent_job_id"] = job.id
                    job = job.create(vals)
            else:
                job = self.env["queue.job.replacement"].sudo().create(create_vals)
            if delay_args.get("priority", 100) < 100:
                # Immediate trigger for jobs with high priority
                self.env.ref(
                    "queue_job_optional.ir_cron_queue_job_replacement_process"
                ).sudo()._trigger()
            return job
