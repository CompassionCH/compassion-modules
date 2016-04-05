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


def rename_tables(cr):
    """ Rename sponsorship correspondence tables. """
    cr.execute(
        """
        Alter table correspondence RENAME TO correspondence;
        Alter table correspondence_page RENAME TO
        correspondence_page;
        Alter table correspondence_type RENAME TO
        correspondence_type;
        Alter table correspondence_type_relation RENAME TO
        correspondence_type_relation;
        Alter table correspondence_template RENAME TO
        correspondence_template;
        Alter table correspondence_lang_checkbox RENAME TO
        correspondence_lang_checkbox;
        Alter table sponsorship_crosscheck RENAME TO
        correspondence_template_crosscheck;
        Update ir_model_data set model='correspondence.type'
        where model='sponsorship.correspondence.type';
        Update ir_model_data set model='correspondence.template'
        where model='sponsorship.correspondence.template';
        Alter table correspondence_id_seq RENAME TO
        correspondence_id_seq;
        Alter table correspondence_lang_checkbox_id_seq RENAME TO
        correspondence_lang_checkbox_id_seq;
        Alter table correspondence_page_id_seq RENAME TO
        correspondence_page_id_seq;
        Alter table correspondence_template_id_seq RENAME TO
        correspondence_template_id_seq;
        Alter table correspondence_type_id_seq RENAME TO
        correspondence_type_id_seq;
        Alter table sponsorship_crosscheck_id_seq RENAME TO
        correspondence_template_crosscheck_id_seq;
        """
    )


def migrate(cr, version):
    if not version:
        return

    rename_tables(cr)
