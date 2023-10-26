import logging


_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # Force update of Forget Me GMC Action (for changing the success method)
    cr.execute("""UPDATE gmc_action SET success_method='anonymize'
        WHERE name='AnonymizePartner';
    """)
