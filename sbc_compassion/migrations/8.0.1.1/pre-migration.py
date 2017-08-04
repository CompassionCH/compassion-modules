# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################


def rename_tables(cr):
    """ Rename sponsorship correspondence tables. """
    cr.execute(
        """
        Alter table sponsorship_correspondence RENAME TO correspondence;
        Alter table sponsorship_correspondence_page RENAME TO
        correspondence_page;
        Alter table sponsorship_correspondence_type RENAME TO
        correspondence_type;
        Alter table sponsorship_correspondence_type_relation RENAME TO
        correspondence_type_relation;
        Alter table sponsorship_correspondence_template RENAME TO
        correspondence_template;
        Alter table sponsorship_correspondence_lang_checkbox RENAME TO
        correspondence_lang_checkbox;
        Alter table sponsorship_crosscheck RENAME TO
        correspondence_template_crosscheck;
        Update ir_model_data set model='correspondence.type'
        where model='sponsorship.correspondence.type';
        Update ir_model_data set model='correspondence.template'
        where model='sponsorship.correspondence.template';
        Alter table sponsorship_correspondence_id_seq RENAME TO
        correspondence_id_seq;
        Alter table sponsorship_correspondence_lang_checkbox_id_seq RENAME TO
        correspondence_lang_checkbox_id_seq;
        Alter table sponsorship_correspondence_page_id_seq RENAME TO
        correspondence_page_id_seq;
        Alter table sponsorship_correspondence_template_id_seq RENAME TO
        correspondence_template_id_seq;
        Alter table sponsorship_correspondence_type_id_seq RENAME TO
        correspondence_type_id_seq;
        Alter table sponsorship_crosscheck_id_seq RENAME TO
        correspondence_template_crosscheck_id_seq;
        """
    )
    # Rename layout 6
    cr.execute(
        """
        Update correspondence_template set layout='CH-A-6S11-1'
        Where layout='CH-A-6S01-1';
        """
    )


def migrate(cr, version):
    if not version:
        return

    rename_tables(cr)
