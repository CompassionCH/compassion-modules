##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models


class SponsorshipsEvolutionYearsReport(models.Model):
    _inherit = "sponsorships.evolution_months.report"
    _name = "sponsorships.evolution_years.report"
    _table = "sponsorships_evolution_years_report"
    _description = "Sponsorships Evolution By Years"

    def _date_format(self):
        """
         Used to aggregate data in various formats (in subclasses) "
        :return: (date_trunc value, date format)
        """ ""
        return ("year", "YYYY")
