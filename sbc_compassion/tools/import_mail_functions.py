"""
Defines a few functions useful in ../models/import_mail.py
"""
import os


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
    if ext.lower() == '.pdf':
        return True
    else:
        return False


def isTIFF(name):
    """
    Check the extension of the name

    :param string name: File name to check
    :returns: True if TIFF, False otherwise
    :rtype: bool
    """
    ext = os.path.splitext(name)[1]
    if (ext.lower() == '.tif' or ext.lower() == '.tiff'):
        return True
    else:
        return False

def isPNG(name):
    """
    Check the extension of the name

    :param string name: File name to check
    :returns: True if PNG, False otherwise
    :rtype: bool
    """
    ext = os.path.splitext(name)[1]
    if ext.lower() == '.png':
        return True
    else:
        return False


def isZIP(name):
    """
    Check the extension of the name

    :param string name: File name to check
    :returns: True if ZIP, False otherwise
    :rtype: bool
    """
    ext = os.path.splitext(name)[1]
    if (ext.lower() == '.zip'):
        return True
    else:
        return False


def list2string(list_):
    """
    Transform a list to a string by separating the string in the list by ;

    :param [string] list_: List to transform
    :returns: Input list as a string and separated by ';'
    :rtype: String
    """
    tmp = ''
    for i in list_:
        tmp += i + ';'
    return tmp


def addname(string, name):
    """
    Add name to string by separating them with ;
    The name is put at the end of the string

    :param string string: String where to add the name
    :param string name: Name to add at the end of string (in unicode)
    """
    return string + name + ';'


def removename(string, name):
    """
    Find and remove name in string where string is a string separated with ;

    :param string string: String list separated by ';'
    :param string name: Name to find in string
    :returns: string without name or False
    :rtype: string or bool
    """
    tmp = string.replace(';' + name + ';', ';')
    if tmp == string:
        tmp = string.replace(name + ';', ';')
        if tmp == string:
            return -1
        else:
            return tmp
    else:
        return tmp

