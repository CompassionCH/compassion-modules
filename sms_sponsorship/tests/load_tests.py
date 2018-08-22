# coding: utf-8
# pylint: disable=W7936
from locust import HttpLocust, TaskSet, task
from random import randint


class SmsSponsorWorkflow(TaskSet):

    @task(1)
    def send_sms(self):
        url = "/sms/mnc?sender=%2B41789364{}&service=compassion".format(
            randint(100, 999))
        self.client.get(url)


class SmsSponsor(HttpLocust):
    task_set = SmsSponsorWorkflow
