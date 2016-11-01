# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>, Philippe Heer
#
#    The licence is in the file __openerp__.py
#
##############################################################################


from openerp import models, fields, api, _
from openerp.addons.message_center_compassion.mappings \
    import base_mapping as mapping


class ChildLifecycleEvent(models.Model):
    """ A child lifecycle event (BLE) """
    _name = 'compassion.child.ble'
    _description = 'Child Lifecycle Event'
    _inherit = 'translatable.model'
    _order = 'date desc, id desc'

    child_id = fields.Many2one(
        'compassion.child', 'Child', required=True, ondelete='cascade',
        readonly=True)
    global_id = fields.Char(readonly=True, required=True)
    date = fields.Datetime(readonly=True)
    type = fields.Selection([
        ('Planned Exit', 'Planned Exit'),
        ('Registration', 'Registration'),
        ('Reinstatement', 'Reinstatement'),
        ('Transfer', 'Transfer'),
        ('Transition', 'Transition'),
        ('Unplanned Exit', 'Unplanned Exit'),
    ], readonly=True)

    # All reasons for all request types
    request_reason = fields.Selection([
        # Child Registration
        ('Registration with Compassion', _('Child registration')),
        # Planned Exit
        ('Fulfilled Completion Plan And Reached Completion Date',
         _('{he} fulfilled completion plan and reached completion date')),
        ('Reached Maximum Age', _('{he} reached maximum age')),
        ('Reached Max Age Or Completion Date But Did Not Fulfill '
         'Completion Plan',
         _('{he} reached maximum age or completion date.')),
        ('Reached The End Of Relevant Programs Available At ICP',
         _('{he} reached the end of relevant programs available at the '
           'project')),
        ('Reached The End Of The Relevant Programs Available At The Church '
         'Partner',
         _('{he} reached the end of relevant programs available at the '
           'project')),
        # Reinstatement
        ('Beneficiary Exit Was A Mistake', _('the exit was a mistake')),
        ('Beneficiary Moved Back', _('{he} moved back')),
        ('Family Needs Help Again', _('{his} family needs help again')),
        ('No Longer Sponsored By Another Organization',
         _('{he} is no longer sponsored by another organization')),
        ('Now Interested And Agrees To Policies',
         _('{he} is now interested and agrees to policies')),
        # Transfer
        ('Recently Exited And Attending New ICP',
         _('{he} recently exited and attends a new ICP')),
        ('Relocation: Caregiver\'s Work.',
         _('of a relocation of {his} caregiver\'s work.')),
        ('Relocation: Change Of Caregiver',
         _('of a change of caregiver')),
        ('Relocation: Moved To Another Area',
         _('{he} moved to another area')),
        ('Relocation: Voc / Tech Or Higher Educ',
         _('of a relocation for his higher education')),
        ('Relocation: Vocational/Technical Or Higher Education.',
         _('of a relocation for his higher education')),
        ('Programming Availability Is A Better Fit For Beneficiary',
         _('programming availability is a better fit for {him}')),
        ('Programming Is A Better Fit', _('programming is a better fit')),
        ('Project Closure', _('of the project closure')),
        ('Project Downsizing', _('of the project downsizing')),
        ('Project Opened Closer To Home',
         _('another project opened closer to {his} home')),
        ('Special Needs', _('of special needs')),
        ('Beneficiary / Caregiver Moving To Another Location',
         _('{he} moved to another location')),
        # Unplanned Exit
        ('Beneficiary / Caregiver Not Comply With Policies',
         _('{he} does not comply with policies')),
        ('Child / Caregiver Does Not Comply With Policies',
         _('{he} does not comply with policies')),
        ('Beneficiary In System Under Two Numbers',
         _('{he} is in the system under two numbers')),
        ('Child In System Under Two Numbers (Enter Other Number In The '
         'Comments Box Below)', _('{he} is the in system under two numbers')),
        ('Beneficiary Pursuing Career Opportunity',
         _('{he} pursues career opportunity')),
        ('Child Places Others At Risk', _('{he} places others at risk')),
        ('Child Sponsored By Another Organization',
         _('{he} is sponsored by another organization')),
        ('Community Safety Issues', _('of community safety issues')),
        ('Conflicts With School Or Work Schedule',
         _('of conflicts with school or work schedule')),
        ('Death Of Caregiver Creates Situation Where Child Cannot Continue',
         _('{his} caregiver died')),
        ('Death Of Beneficiary', _('{he} passed away')),
        ('Death Of Caregiver', _('{his} caregiver died')),
        ('Death Of Child', _('{he} passed away')),
        ('Family Circumstances Have Changed Positively So That Child No '
         'Longer Needs Compassion\'s Assistance',
         _('family circumstances have changed positively')),
        ('Family Moved And Transfer Not Available',
         _('{his} family moved where a Compassion project '
           'with relevant programs is not available')),
        ('Family Moved Where A Compassion Project With Relevant Programs Is '
         'Not Available', _('{his} family moved where a Compassion project '
                            'with relevant programs is not available')),
        ('Family No Longer Interested in Program',
         _('{his} family is no longer interested in the program')),
        ('Project Closed - No Transfer Available',
         _('of the project closure')),
        ('Project Or Program Closure', _('of the project closure')),
        ('Taken Out Of Project By Parents, Or Family No Longer Interested '
         'In Program', _('{he} was taken out of project by parents')),
        ('Unjustified Absence From Program Activities For Greater Than 2 '
         'Months', _('of an unjustified absence for greater than 2 months')),
        ('Unjustified Absence More Than 2 Months',
         _('of an unjustified absence for greater than 2 months')),
        ('Child Ran Away', _('{he} ran away')),
        ('Crisis', _('of a crisis')),
        ('Deceased', _('{he} passed away')),
        ('Gone Into Military Service', _('{he} went into military service')),
        ('No Longer Interested In The Program',
         _('{he} is no longer interested in the Program')),
        ('No Longer Needs Our Assistance',
         _('{he} no longer needs our assistance')),
        ('Project Capacity Issue', _('of project capacity issue')),
        ('Registered / Transferred Incorrectly',
         _('{he} registered incorrectly')),
        ('Sponsored By Another Organization',
         _('{he} is sponsored by another organization'))
    ], readonly=True)

    # Common fields
    ###############
    # comments = fields.Char(readonly=True)
    status = fields.Selection([
        ('Cancelled', 'Cancelled'),
        ('Closed', 'Closed'),
        ('In Progress', 'In Progress'),
        ('Open', 'Open'),
    ])

    # Planned Exit fields
    #####################
    last_attended_project = fields.Date(readonly=True)
    primary_school_finished = fields.Boolean(readonly=True)
    # confesses_jesus_savior = fields.Boolean(readonly=True)
    final_letter_sent = fields.Boolean(readonly=True)
    sponsor_impact = fields.Char(readonly=True)
    new_situation = fields.Char(readonly=True)
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
    transition_type = fields.Selection([
        ('Sponsorship-Home to Sponsorship-Center', 'Home to Center'),
        ('Survival to Sponsorship-Home', 'Survival to Home'),
        ('Traditional Survival to Sponsorship-Center',
         'Traditional Survival to Center'),
    ], readonly=True)

    # Unplanned Exit fields
    #######################
    child_death_date = fields.Date(readonly=True)
    death_intervention_information = fields.Char(readonly=True)

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
            lifecycle = super(ChildLifecycleEvent, self).create(vals)
            # Process lifecycle event
            if 'Exit' in lifecycle.type:
                lifecycle.child_id.depart()
            elif lifecycle.type == 'Reinstatement':
                lifecycle.child_id.reinstatement()
        return lifecycle

    @api.model
    def process_commkit(self, commkit_data):
        lifecycle_mapping = mapping.new_onramp_mapping(
            self._name,
            self.env,
            'new_child_lifecyle')
        lifecycle_ids = list()

        for single_data in commkit_data.get('BeneficiaryLifecycleEventList',
                                            [commkit_data]):
            vals = lifecycle_mapping.get_vals_from_connect(single_data)
            lifecycle = self.create(vals)
            lifecycle_ids.append(lifecycle.id)

        return lifecycle_ids
