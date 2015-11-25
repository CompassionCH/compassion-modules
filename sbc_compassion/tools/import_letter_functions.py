# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Loic Hausammann <loic_hausammann@hotmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
"""
Defines a few functions useful in ../models/import_mail.py
"""
import os


##########################################################################
#                           GENERAL METHODS                              #
##########################################################################
def check_file(name):
    """
    Check the name of a file.
    return 1 if it is a tiff or a pdf and 0 otherwise.

    This function can be upgraded in order to include other
    format (1 for file, 2 for archive, 0 for not supported).
    In order to have a nice code, one should add the function
    is... when adding a new format

    :param str name: Name of the file to check
    :return: 1 if pdf or tiff, 2 if zip, 0 otherwise
    :rtype: int
    """
    if isPDF(name) or isTIFF(name):
        return 1
    elif isZIP(name):
        return 2
    else:
        return 0


def isPDF(name):
    """
    Check the extension of the name

    :param string name: File name to check
    :returns: True if PDF, False otherwise
    :rtype: bool
    """
    ext = os.path.splitext(name)[1]
    return (ext.lower() == '.pdf')


def isTIFF(name):
    """
    Check the extension of the name

    :param string name: File name to check
    :returns: True if TIFF, False otherwise
    :rtype: bool
    """
    ext = os.path.splitext(name)[1]
    return (ext.lower() == '.tif' or ext.lower() == '.tiff')


def isPNG(name):
    """
    Check the extension of the name

    :param string name: File name to check
    :returns: True if PNG, False otherwise
    :rtype: bool
    """
    ext = os.path.splitext(name)[1]
    return (ext.lower() == '.png')


def isZIP(name):
    """
    Check the extension of the name

    :param string name: File name to check
    :returns: True if ZIP, False otherwise
    :rtype: bool
    """
    ext = os.path.splitext(name)[1]
    return (ext.lower() == '.zip')
