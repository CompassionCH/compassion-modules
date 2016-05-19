# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################


from openerp import models, fields


class ChildLifecycleEvent(models.Model):
    """ A child lifecycle event (BLE) """
    _name = 'compassion.child.ble'
    _description = 'Child Lifecycle Event'
    _order = 'date desc'

    child_id = fields.Many2one(
        'compassion.child', 'Child', required=True, ondelete='cascade')
    date = fields.Datetime()
    type = fields.Selection([
        ('Planned Exit', 'Planned Exit'),
        ('Reinstatement/Return', 'Reinstatement'),
        ('Transfer', 'Transfer'),
        ('Unplanned Exit', 'Unplanned Exit'),
    ])

    # All reasons for all request types
    request_reason = fields.Selection([
        # Planned Exit
        ('Reached Maximum Age', 'Reached Maximum Age'),
        ('Reached the end of the relevant programs available at the church '
         'partner ', 'Reached the end of the relevant programs available'),
        # Reinstatement
        ('Beneficiary Exit was a mistake', 'Exit was a mistake'),
        ('Beneficiary Moved Back', 'Beneficiary Moved Back'),
        ('Family Needs Help Again', 'Family Needs Help Again'),
        ('No Longer Sponsored by Another Organization',
         'No Longer Sponsored by Another Organization'),
        ('Other (enter reason below)', 'Other'),
        # Transfer
        ('Relocation: Caregiver\'s Work.', 'Relocation: Caregiver\'s Work.'),
        ('Relocation: Moved To Another Area',
         'Relocation: Moved To Another Area'),
        ('Relocation: Vocational/Technical Or Higher Education.',
         'Relocation: Vocational/Technical Or Higher Education.'),
        ('Programming Availability Is A Better Fit For Beneficiary',
         'Programming Availability Is A Better Fit For Beneficiary'),
        ('Project Closure', 'Project Closure'),
        ('Project Downsizing', 'Project Downsizing'),
        ('Special Needs', 'Special Needs'),
        # Unplanned Exit
        ('Child / Caregiver does not comply with policies',
         'Child / Caregiver does not comply with policies'),
        ('Child in system under two numbers (enter other number in the '
         'Comments box below)', 'Child in system under two numbers'),
        ('Child places others at risk', 'Child places others at risk'),
        ('Child sponsored by another organization',
         'Child sponsored by another organization'),
        ('Death of caregiver creates situation where child cannot continue',
         'Death of caregiver creates situation where child cannot continue'),
        ('Death of child', 'Death of child'),
        ('Family Circumstances Have Changed Positively So That Child No '
         'Longer Needs Compassion’s Assistance',
         'Family Circumstances Have Changed Positively'),
        ('Family moved where a Compassion project with relevant programs is '
         'not available', 'Family moved where a Compassion project with \
            relevant programs is not available'),
        ('Project or program closure', 'Project or program closure'),
        ('Taken out of project by parents, or family no longer interested '
         'in program', 'Taken out of project by parents'),
        ('Unjustified absence from program activities for Greater Than 2 '
         'months', 'Unjustified absence for greater than 2 months'),
    ])

    # Common fields
    ###############
    comments = fields.Char()

    # Planned Exit fields
    #####################
    last_attended_project = fields.Date()
    primary_school_finished = fields.Boolean()
    confesses_jesus_savior = fields.Boolean()
    final_letter_sent = fields.Boolean()
    sponsor_impact = fields.Char()
    new_situation = fields.Char()
    future_hopes = fields.Char()
    family_impact = fields.Char()

    # Reinstatement fields
    ######################
    other_reinstatement_reason = fields.Char()

    # Transfer fields
    #################
    old_project_id = fields.Many2one('compassion.project')
    transfer_arrival_date = fields.Date()
    other_transfer_reason = fields.Char()

    # Transition fields
    ###################
    transition_type = fields.Selection([
        ('Sponsorship-Home to Sponsorship-Center', 'Home to Center'),
        ('Survival to Sponsorship-Home', 'Survival to Home'),
        ('Traditional Survival to Sponsorship-Center',
         'Traditional Survival to Center'),
    ])

    # Unplanned Exit fields
    #######################
    child_death_date = fields.Date()
    child_death_circumstances = fields.Char()
    child_death_category = fields.Selection([
        ('Abuse', 'Abuse'),
        ('Fatal Accident or Suicide', 'Fatal Accident or Suicide'),
        ('Gastro-Intestinal', 'Gastro-Intestinal'),
        ('Infection', 'Infection'),
        ('Maternal', 'Maternal'),
        ('Neonatal Disorders', 'Neonatal Disorders'),
        ('Non-Communicable Diseases', 'Non-Communicable Diseases'),
        ('Respiratory-Related', 'Respiratory-Related'),
        ('Unknown Cause', 'Unknown Cause'),
        ('Vaccine-Preventable Diseases', 'Vaccine-Preventable Diseases'),
        ('Vector-Borne', 'Vector-Borne'),
    ])
    child_death_subcategory = fields.Selection([
        ('Abortion-related', 'Abortion-related'),
        ('Anemia', 'Anemia'),
        ('Asphyxia', 'Asphyxia'),
        ('Birth Asphyxia', 'Birth Asphyxia'),
        ('Bronchitis', 'Bronchitis'),
        ('Burns', 'Burns'),
        ('Cancer', 'Cancer'),
        ('Cardiovascular', 'Cardiovascular'),
        ('Chicken Pox', 'Chicken Pox'),
        ('Chikungunya', 'Chikungunya'),
        ('Cholera', 'Cholera'),
        ('Congenital Abnormalities', 'Congenital Abnormalities'),
        ('Dengue', 'Dengue'),
        ('Diabetes', 'Diabetes'),
        ('Diarrhea', 'Diarrhea'),
        ('Diphtheria', 'Diphtheria'),
        ('Drowning', 'Drowning'),
        ('Electrocution', 'Electrocution'),
        ('Epilepsy/Seizure Disorder', 'Epilepsy/Seizure Disorder'),
        ('Falls', 'Falls'),
        ('HIV/AIDS-related', 'HIV/AIDS-related'),
        ('Hepatitis', 'Hepatitis'),
        ('Influenza', 'Influenza'),
        ('Intra-partum-related Complications',
         'Intra-partum-related Complications'),
        ('Japanese Encephalitis', 'Japanese Encephalitis'),
        ('Leukemia', 'Leukemia'),
        ('Malaria', 'Malaria'),
        ('Measles', 'Measles'),
        ('Meningitis', 'Meningitis'),
        ('Mumps', 'Mumps'),
        ('Natural Disaster', 'Natural Disaster'),
        ('Obstructed Labor', 'Obstructed Labor'),
        ('Other', 'Other'),
        ('Parasites', 'Parasites'),
        ('Pertussis', 'Pertussis'),
        ('Physical', 'Physical'),
        ('Pneumonia', 'Pneumonia'),
        ('Poisoning', 'Poisoning'),
        ('Polio', 'Polio'),
        ('Postpartum Complications (Hemorrhage, infection etc.)',
         'Postpartum Complications (Hemorrhage, infection etc.)'),
        ('Pregnancy Complications (Preeclampsia, eclampsia, etc.)',
         'Pregnancy Complications (Preeclampsia, eclampsia, etc.)'),
        ('Prematurity/ Low Birth Weight', 'Prematurity/ Low Birth Weight'),
        ('Renal Disease', 'Renal Disease'),
        ('Respiratory Tract Infection', 'Respiratory Tract Infection'),
        ('Rotavirus', 'Rotavirus'),
        ('Rubella', 'Rubella'),
        ('Sepsis/Infection', 'Sepsis/Infection'),
        ('Septicemia', 'Septicemia'),
        ('Skin', 'Skin'),
        ('Substance', 'Substance'),
        ('Sudden Infant Death', 'Sudden Infant Death'),
        ('Suicide', 'Suicide'),
        ('Tetanus', 'Tetanus'),
        ('Transportation  Accident', 'Transportation  Accident'),
        ('Tuberculosis', 'Tuberculosis'),
        ('Typhoid', 'Typhoid'),
        ('Typhus', 'Typhus'),
        ('Violence', 'Violence'),
        ('West Nile Virus', 'West Nile Virus'),
        ('Yellow Fever', 'Yellow Fever'),
    ])
