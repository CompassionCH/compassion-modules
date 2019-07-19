import re
import threading
import locale
import logging
from contextlib import contextmanager
from collections import OrderedDict


from odoo import models, fields, api, _


LOCALE_LOCK = threading.Lock()
logger = logging.getLogger(__name__)


@contextmanager
def setlocale(name):
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, (name, 'UTF-8'))
        except:
            logger.error("unable to set locale.")
            yield
        finally:
            locale.setlocale(locale.LC_ALL, saved)


class AdvancedTranslatable(models.AbstractModel):
    """ Inherit this class in order to let your model fetch keywords
    based on the source recordset and a gender field in the model.
    """
    _name = 'translatable.model'

    gender = fields.Selection([
        ('M', 'Male'),
        ('F', 'Female'),
    ], default='M')

    @api.multi
    def get(self, keyword):
        """
        Gets the translation for one keyword, depending on the recordset
        (will determine gender and singular/plural automatically.
        :param keyword: keyword for fetching a translation
        :return: the translation
        """
        plural = len(self) > 1
        male = self.filtered(lambda c: c.gender == 'M')
        female = self.filtered(lambda c: c.gender == 'F')
        advanced_translation = self.env['ir.advanced.translation']
        if plural and female and not male:
            return advanced_translation.get(keyword, True, True)
        elif plural:
            return advanced_translation.get(keyword, plural=True)
        elif female and not male:
            return advanced_translation.get(keyword, female=True)
        else:
            return advanced_translation.get(keyword)

    @api.multi
    def translate(self, field):
        """ helps getting the translated value of a
        char/selection field by adding a translate function.
        """
        if not self.exists():
            return ''
        pattern_keyword = re.compile("(\\{)(.*?)(\\})")

        def _replace_keyword(match):
            return self.translate(match.group(2))

        res = list()
        field_path = field.split('.')
        obj = self
        if len(field_path) > 1:
            field_traversal = '.'.join(field_path[:-1])
            obj = obj.mapped(field_traversal)
        definition = obj.fields_get([field_path[-1]]).get(
            field_path[-1])
        if definition:
            for record in self:
                for raw_value in record.mapped(field):
                    if not raw_value:
                        continue
                    val = False
                    if definition['type'] in ('char', 'text') or isinstance(
                            raw_value, str) and definition['type'] !=\
                            'selection':
                        val = _(raw_value)
                    elif definition['type'] == 'selection':
                        val = _(dict(definition['selection'])[raw_value])
                    if val:
                        val = pattern_keyword.sub(_replace_keyword, val)
                        res.append(val)
        if len(res) == 1:
            res = res[0]
        return res or ''

    @api.multi
    def get_list(self, field, limit=float("inf"), substitution=None,
                 translate=True):
        """
        Get a list of values, separated with commas. (last separator 'and')
        :param field: the field values to retrieve from the recordset
        :param limit: optional max number of values to be displayed
        :param substitution: optional substitution text, if number of values is
                             greater than max number provided
        :param translate: set to false to avoid translating values in list
        :return: string of comma separated values
        """
        if translate:
            values = self.translate(field)
        else:
            values = self.mapped(field)
        if isinstance(values, list):
            seen = set()
            values = [x for x in values if not (x in seen or seen.add(x))]
            if len(values) > limit:
                if substitution:
                    return substitution
                values = values[:limit]
            if len(values) > 1:
                res_string = ', '.join(values[:-1])
                res_string += ' ' + _('and') + ' ' + values[-1]
            else:
                res_string = values and values[0] or ""
            values = res_string
        return values

    @api.multi
    def get_date(self, field, date_type='date_short'):
        """
        Useful to format a date field in a given language
        :param field: the date field inside the model
        :param date_type: a valid src of a ir.advanced.translation date format
        :return: the formatted dates
        """
        _format = self.env['ir.advanced.translation'].get(date_type).encode(
            'utf-8')
        dates = map(fields.Datetime.from_string,
                    self.filtered(field).sorted(
                        key=lambda r: getattr(r, field)).mapped(field))
        with setlocale(self.env.lang):
            ordered_dates = OrderedDict.fromkeys(dates)
            for d in dates:
                ordered_dates[d] = d.strftime(_format).decode('utf-8')
        # Filter unique dates
        unique = set()
        unique_add = unique.add
        dates_string = [d for d in ordered_dates.values() if not (
            d in unique or unique_add(d))]
        if len(dates_string) > 1:
            res_string = ', '.join(dates_string[:-1])
            res_string += ' ' + _('and') + ' ' + dates_string[-1]
        else:
            res_string = dates_string and dates_string[0] or ''
        return res_string
