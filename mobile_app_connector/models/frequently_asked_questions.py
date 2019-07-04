# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging
from odoo import api, models, _

_logger = logging.getLogger(__name__)

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    _logger.log('Please install bs4 and requests')


class PrivacyStatementAgreement(models.Model):
    """
    This class contains everything that is related to the Frequently Asked
    Questions for the application.
    """
    _name = 'frequently.asked.questions'

    @api.multi
    def mobile_get_faq_json(self):
        """
        Method that takes care of retrieving the FAQ from the website and
        returns it in a JSON format. The method should be called directly
        from a route from the mobile application, but can be used directly,
        if needed. The FAQ is returned in the language of the user (if
        existing), but default is German, because there is no existing
        English version.

        :return: a JSON formatted dictionary containing all the questions and
        answers of the FAQ.
        """
        faq_link = _('https://compassion.ch/de/haeufig-gestellte-fragen/')
        html = requests.get(faq_link).text
        soup = BeautifulSoup(html, 'html.parser')
        questions_list = soup.find_all(class_='accordion-title')
        questions = [question.text for question in questions_list]
        answers_list = soup.find_all(class_='accordion-content')
        answers = [answer.text for answer in answers_list]

        faq = []
        for (question, answer) in zip(questions, answers):
            faq.append({'Question': question, 'Answer': answer})

        return faq
