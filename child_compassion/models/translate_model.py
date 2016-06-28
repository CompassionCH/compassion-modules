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


from openerp import api, models, _


class TranslateModel(models.AbstractModel):
    """ This model helps getting the translated value of a
        char/selection field by adding a translate function. """
    _name = 'translatable.model'
    _description = 'Translatable Model'

    @api.multi
    def translate(self, field):
        res = list()
        definition = self.fields_get([field]).get(field)
        if definition:
            for record in self:
                raw_value = getattr(record, field, False)
                if raw_value:
                    if definition['type'] in ('char', 'text'):
                        val = _(raw_value)
                    elif definition['type'] == 'selection':
                        val = _(dict(definition['selection'])[raw_value])
                    if val:
                        res.append(val)
        if len(res) == 1:
            res = res[0]
        return res or ''
