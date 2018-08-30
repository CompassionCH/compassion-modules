# coding: utf-8
# pylint: disable=W7936
from locust import HttpLocust, TaskSet, task
from random import randint


class SmsSponsorWorkflow(TaskSet):

    @task(1)
    def send_sms(self):
        url = "/sms/mnc?sender=%2B4199{}&service=compassion&text=test".format(
            randint(1000000, 9999999))
        self.client.get(url)


class SmsSponsor(HttpLocust):
    task_set = SmsSponsorWorkflow
