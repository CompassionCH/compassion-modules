# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Loïc Hausammann
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import os
import copy


def open_and_edit_data(filename):
    f = open(filename, 'r')
    data = f.read()
    f.close()
    lines = edit_data(data)
    f = open(filename, 'w')
    for l in lines:
        f.write(l+'\n')
    f.close()


def edit_data(data):
    lines = data.splitlines()
    lines_copy = copy.deepcopy(lines)
    add_private = False
    for l in lines_copy[::-1]:
        if ':show-inheritance:' in l:
            lines.remove(l)
        if '.. automodule::' in l:
            add_private = True
    if add_private:
        lines.append('    :private-members:')
    return lines

if __name__ == '__main__':
    dirname = os.path.dirname(__file__)
    for d in os.listdir(os.path.abspath(dirname + 'source/')):
        if os.path.splitext(d)[1] == '.rst':
            open_and_edit_data('source/' + d)
