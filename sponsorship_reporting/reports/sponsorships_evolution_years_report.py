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
    """
    Inherits the Monthly report logic but changes the table name
    and the date grouping format to 'year'.
    """

    _inherit = "sponsorships.evolution_months.report"
    _name = "sponsorships.evolution_years.report"
    _description = "Sponsorships Evolution By Years"
    _table = "sponsorships_evolution_years_report"

    def _date_format(self):
        """
        Overrides the parent method to group by Year instead of Month.
        """
        return "year", "YYYY"
