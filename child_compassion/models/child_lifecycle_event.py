##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>, Philippe Heer
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api


class ChildLifecycleEvent(models.Model):
    """ A child lifecycle event (BLE) """
    _name = 'compassion.child.ble'
    _description = 'Child Lifecycle Event'
    _inherit = 'translatable.model'
    _order = 'date desc, id desc'
    _inherit = ['compassion.mapped.model']

    child_id = fields.Many2one(
        'compassion.child', 'Child', required=True, ondelete='cascade',
        readonly=True)
    global_id = fields.Char(readonly=True, required=True)
    date = fields.Date(readonly=True)
    type = fields.Selection([
        ('Beneficiary Update', 'Beneficiary Update'),
        ('Home Based Caregiver Death', 'Home Based Caregiver Death'),
        ('Planned Exit', 'Planned Exit'),
        ('Registration', 'Registration'),
        ('Reinstatement', 'Reinstatement'),
        ('Transfer', 'Transfer'),
        ('Transition', 'Transition'),
        ('Unplanned Exit', 'Unplanned Exit'),
    ], readonly=True)
    gender = fields.Selection(related='child_id.gender')

    # All reasons for all request types
    request_reason = fields.Selection([
        # Child Registration
        ('registration with compassion', 'Child registration'),
        # Planned Exit
        ('fulfilled completion plan and reached completion date',
         '{he} fulfilled completion plan and reached completion date'),
        ('reached maximum age', '{he} reached maximum age'),
        ('reached max age or completion date but did not fulfill '
         'completion plan',
         '{he} reached maximum age or completion date.'),
        ('reached the end of relevant programs available at icp',
         '{he} reached the end of relevant programs available at the '
         'project'),
        ('reached the end of the relevant programs available at the church '
         'partner',
         '{he} reached the end of relevant programs available at the project'),
        # Reinstatement
        ('beneficiary exit was a mistake', 'the exit was a mistake'),
        ('beneficiary moved back', '{he} moved back'),
        ('reinstate: child moved back', '{he} moved back'),
        ('family needs help again', '{his} family needs help again'),
        ('no longer sponsored by another organization',
         '{he} is no longer sponsored by another organization'),
        ('now interested and agrees to policies',
         '{he} is now interested and agrees to policies'),
        # Transfer
        ('child transfer', 'Child Transfer'),
        ('recently exited and attending new icp',
         '{he} recently exited and attends a new ICP'),
        ("relocation: caregiver's work.",
         "of a relocation of {his} caregiver's work."),
        ("relocation: caregiver's work",
         "of a relocation of {his} caregiver's work."),
        ('relocation: change of caregiver',
         'of a change of caregiver'),
        ('relocation: moved to another area',
         '{he} moved to another area'),
        ('relocation: voc / tech or higher educ',
         'of a relocation for his higher education'),
        ('relocation: vocational / technical or higher education',
         'of a relocation for his higher education'),
        ('programming availability is a better fit for beneficiary',
         'programming availability is a better fit for {him}'),
        ('programming is a better fit', 'programming is a better fit'),
        ('project closure', 'of the project closure'),
        ('project downsizing', 'of the project downsizing'),
        ('project opened closer to home',
         'another project opened closer to {his} home'),
        ('special needs', 'of special needs'),
        ('beneficiary / caregiver moving to another location',
         '{he} moved to another location'),
        ('other (enter reason below)', 'of : {other_transfer_reason}'),
        ('child transfer', 'Child Transfer'),
        # Unplanned Exit
        ('beneficiary / caregiver not comply with policies',
         '{he} does not comply with policies'),
        ('child / caregiver does not comply with policies',
         '{he} does not comply with policies'),
        ('beneficiary in system under two numbers',
         '{he} is in the system under two numbers'),
        ('child in system under two numbers (enter other number in the '
         'comments box below)', '{he} is the in system under two numbers'),
        ('beneficiary pursuing career opportunity',
         '{he} pursues career opportunity'),
        ('child places others at risk', '{he} places others at risk'),
        ('child sponsored by another organization',
         '{he} is sponsored by another organization'),
        ('community safety issues', 'of community safety issues'),
        ('conflicts with school or work schedule',
         'of conflicts with school or work schedule'),
        ('death of caregiver creates situation where child cannot continue',
         '{his} caregiver died'),
        ('death of beneficiary', '{he} passed away'),
        ('death of caregiver', '{his} caregiver died'),
        ('death of child', '{he} passed away'),
        ('family circumstances have changed positively so that child no '
         "longer needs compassion's assistance",
         'family circumstances have changed positively'),
        ('family moved and transfer not available',
         '{his} family moved where a Compassion project '
         'with relevant programs is not available'),
        ('family moved where a compassion project with relevant programs is '
         'not available', '{his} family moved where a Compassion project '
                          'with relevant programs is not available'),
        ('family no longer interested in program',
         '{his} family is no longer interested in the program'),
        ('project closed - no transfer available',
         'of the project closure'),
        ('project or program closure', 'of the project closure'),
        ('taken out of project by parents, or family no longer interested '
         'in program', '{he} was taken out of project by parents'),
        ('unjustified absence from program activities for greater than 2 '
         'months', 'of an unjustified absence for greater than 2 months'),
        ('unjustified absence more than 2 months',
         'of an unjustified absence for greater than 2 months'),
        ('child ran away', '{he} ran away'),
        ('crisis', 'of a crisis'),
        ('deceased', '{he} passed away'),
        ('gone into military service', '{he} went into military service'),
        ('no longer interested in the program',
         '{he} is no longer interested in the Program'),
        ('no longer needs our assistance',
         '{he} no longer needs our assistance'),
        ('project capacity issue', 'of project capacity issue'),
        ('registered / transferred incorrectly',
         '{he} registered incorrectly'),
        ('sponsored by another organization',
         '{he} is sponsored by another organization'),
        ('other', '{he} left the project')
    ], readonly=True)

    # Common fields
    ###############
    # comments = fields.Char(readonly=True)
    status = fields.Char()

    # Planned Exit fields
    #####################
    last_attended_project = fields.Date(readonly=True)
    primary_school_finished = fields.Boolean(readonly=True)
    # confesses_jesus_savior = fields.Boolean(readonly=True)
    final_letter_sent = fields.Boolean(readonly=True)
    sponsor_impact = fields.Char(readonly=True)
    new_situation = fields.Char(readonly=True)
    future_hope_ids = fields.Many2many(
        'child.future.hope', string='Future hopes', readonly=True)
    future_hopes = fields.Char(readonly=True)
    family_impact = fields.Char(readonly=True)

    # Transfer fields
    #################
    old_project_id = fields.Many2one('compassion.project', readonly=True)
    transfer_arrival_date = fields.Date(readonly=True)
    other_transfer_reason = fields.Char(readonly=True)
    current_project = fields.Char(readonly=True)
    new_project = fields.Char(readonly=True)
    new_program = fields.Char(readonly=True)
    previously_active_program = fields.Char(readonly=True)

    # Transition fields
    ###################
    transition_type = fields.Char(readonly=True)

    # Unplanned Exit fields
    #######################
    child_death_date = fields.Date(readonly=True)
    death_intervention_information = fields.Char(readonly=True)

    child_death_category = fields.Selection(
        [
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
        ], readonly=True)
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
    ], readonly=True)

    _sql_constraints = [
        ('global_id', 'unique(global_id)',
         'The lifecycle already exists in database.')
    ]

    @api.model
    def create(self, vals):
        lifecycle = self.search([
            ('global_id', '=', vals['global_id'])
        ])
        if lifecycle:
            lifecycle.write(vals)
        else:
            lifecycle = super().create(vals)
            child = lifecycle.child_id
            # Process lifecycle event
            if 'Exit' in lifecycle.type:
                child.depart()
            elif lifecycle.type == 'Reinstatement':
                child.reinstatement()
            else:
                lifecycle.child_id.with_context(async_mode=False).get_infos()
        return lifecycle

    @api.model
    def process_commkit(self, commkit_data):
        lifecycle_ids = list()

        for single_data in commkit_data.get('BeneficiaryLifecycleEventList',
                                            [commkit_data]):
            vals = self.json_to_data(single_data)
            lifecycle = self.create(vals)
            lifecycle_ids.append(lifecycle.id)

        return lifecycle_ids
