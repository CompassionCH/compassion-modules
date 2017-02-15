# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Roman Zoller
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.tests import common

import base64
import os
import re

IMPORT_DIR = os.path.join(os.path.dirname(__file__), "testdata/import")


def get_file_content(path):
    """ Reads a file and returns a base64 encoding of its contents. """
    with open(path, "rb") as f:
        file_content = f.read()
        return base64.b64encode(file_content)


def import_letters(env, filename, csv_file):
    """ Reads and imports letters/csv into the database. """
    test_letters_obj = env["test.import.letters.history"]
    letters_obj = env["import.letters.history"]
    path = os.path.join(IMPORT_DIR, filename)
    file_content = get_file_content(path)
    path_csv = os.path.join(IMPORT_DIR, csv_file)
    csv_content = get_file_content(path_csv)
    attachment = {
        "name": filename,
        "datas": file_content,
    }
    csv_file = {
        "name": csv_file,
        "datas": csv_content,
    }
    test_letters = test_letters_obj.create({
        "data": [(0, 0, attachment)],
        'csv_file_ids': [(0, 0, csv_file)],
    })
    letters = letters_obj.create({
        "data": [(0, 0, attachment)],
    })
    test_letters.with_context(async_mode=False).button_import()
    letters.with_context(async_mode=False).button_import()
    return test_letters, letters


def get_template_list(data_obj):
    """
    Returns a dict of all templates with externals ids as keys and ids as
    corresponding values.
    """
    data = data_obj.search(
        [("model", "=", "correspondence.template")])
    template_list = {}
    for d in data:
        template_list[d.name] = d.res_id
    return template_list


def generate_test(filename, csv_file):
    """ Generates a test for the import of one letter. """
    def test_import(self):
        test_imports, imports = import_letters(self.env, filename, csv_file)
        self.assertEqual(test_imports.nber_letters, 0)
        self.assertEqual(imports.nber_letters, 1)
        test_line = test_imports.test_import_line_ids
        # check if a line does not correspond to the csv
        self.assertEqual(len(test_line), 0)
        letters = imports.import_line_ids
        self.assertEqual(len(letters), 1)
        self.assertEqual(test_imports.state, "open")
        if (letters.sponsorship_id and letters.template_id and
                letters.letter_language_id):
            self.assertEqual(imports.state, "ready")
        else:
            self.assertEqual(imports.state, "open")
    return test_import


class TestLetterImportGenerator(type):
    """
    Generates a test function for each entry of a list of files.
    """
    def __new__(mcs, name, bases, dict_value):
        file_index = os.path.join(IMPORT_DIR, "travis_files.csv")
        for f in os.listdir(IMPORT_DIR):
            if os.path.splitext(f)[1] in ['.tif', '.zip']:
                sanitized_filename = re.sub(r"[^a-zA-Z0-9]", "_", f)
                test_name = "test_import_{}".format(sanitized_filename)
                dict_value[test_name] = generate_test(f, file_index)
        return type.__new__(mcs, name, bases, dict_value)


class TestLetterImport(common.TransactionCase):
    """
    Tests import of letters and verifies correct parsing. Letters are given as
    .tif files; a list of these files is read from a .csv file, along with
    expected parsing results.
    """
    __metaclass__ = TestLetterImportGenerator
