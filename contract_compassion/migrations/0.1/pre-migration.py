# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Coninckx David <david@coninckx.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import sys
from operator import itemgetter
import pdb



def migrate(cr, version):
    reload(sys)
    sys.setdefaultencoding('UTF8')
    pdb.set_trace()
    if not version:
        return
    
    # Remove new ir_model_data for contract_compassion product
    cr.execute(
    """
    DELETE FROM ir_model_data
    WHERE module='contract_compassion' AND
    model='product.product'
    """
    )
    # Modify old ir_model_data to change module name
    cr.execute(
    """
    UPDATE ir_model_data
    SET module='contract_compassion'
    WHERE module='sponsorship_compassion' AND
    model='product.product'
    """
    )
    
    # Remove new ir_model_data for contract_compassion workflow activities
    cr.execute(
    """
    DELETE FROM ir_model_data
    WHERE module='contract_compassion' AND
    model IN ('workflow.activity','workflow.transition')
    """
    )
    # Modify old ir_model_data to change module name
    cr.execute(
    """
    UPDATE ir_model_data
    SET module='contract_compassion'
    WHERE module='sponsorship_compassion' AND
    model IN ('workflow.activity','workflow.transition')
    """
    )
    pdb.set_trace()