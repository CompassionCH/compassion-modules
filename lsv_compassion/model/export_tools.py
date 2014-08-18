import locale
import collections
from datetime import datetime
from dateutil.relativedelta import relativedelta
import operator
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _

class export_tools():
    @classmethod
    def get_communications(cls, wizard, cr, uid, line, context=None):
        ''' We look for products in invoices to generate an appropriate 
            communication. If we have enough space, add period informations.
        '''
        #######################################################################
        # As communications have to be in partner language and not in user    #
        # language, we update the context with partner lang. This way, the    #
        # right translation is used.                                          #
        # We also backup the context lang to restore it after with the user   #
        # language.                                                           #
        # Beside of this, we also set the locale to the partner language, in  #
        # order to get the month name in the correct language.                #
        #######################################################################
        if not context:
            context = {}
        lang_backup = context.get('lang', '')
        context['lang'] = line.partner_id.lang
        locale.setlocale(locale.LC_ALL, [context.get('lang'), 'utf8'])
        #######################################################################
        # We don't use move_line_id.invoice because it's really slow (the     #
        # invoice field is in fact a function field with some stuff not used  #
        # in this context. Using a search and browse method made the process  #
        # time go from 25ms to 10ms ! We could go down to 7 ms with a low     #
        # level SQL query, but the gain isn't important enough. We prefer     #
        # keep the code clean and lose 3 seconds on 1'000 payment lines.      #
        #######################################################################
        invoice_obj = wizard.pool.get('account.invoice')
        ids = invoice_obj.search(cr, uid, [('move_id', '=', line.move_line_id.move_id.id)])
        if not ids:
            context['lang'] = lang_backup
            return ''
        
        invoice = invoice_obj.browse(cr, uid, ids[0], context)
        products = [(l.product_id.product_tmpl_id.name, l.quantity, l.child_name) \
                        for l in invoice.invoice_line \
                            if l.product_id.name_template \
                            and (l.child_name \
                                and 'sponsorship' in l.product_id.name_template.lower() \
                                    or 'gift' in l.product_id.name_template.lower()) \
                                or not l.child_name]
        if not products:
            context['lang'] = lang_backup
            return ''
        
        #Reduction on keys -> Dict with total per product
        prod_dict = collections.defaultdict(int)
        qties = collections.defaultdict(list)
        names = {}
        for prod_name, qty, child_name in products:
            prod_dict[prod_name] += 1
            qties[prod_name].append(qty)
            names[prod_name] = child_name
        #List of ordered by quantity tuples (product, quantity)
        prod_dict_sort = sorted(prod_dict.iteritems(), key=operator.itemgetter(1), reverse=True)
        
        communication = ''
        #######################################################################
        # If nb products = 1 or 2, we write product name, quantity, child     #
        # name and period                                                     #
        # (as product are sponsorships or funds).                             #
        #                                                                     #
        # If nb products = 3 or 4, we write product name and quantity.        #
        #                                                                     #
        # If nb products > 4, we write the 3 products with most quantity      #
        # (name + quantity) and on the last line "x other engagements".       #
        #######################################################################
        nb_products = len(prod_dict_sort)
        if nb_products in [1, 2]:
            cur_date = datetime.strptime(invoice.date_due, DEFAULT_SERVER_DATE_FORMAT)
            for prod_name, qty in prod_dict_sort:
                communication += wizard._complete_line(_('%d %s') % (qty, prod_name), 35)
                mx = int(max(qties[prod_name]))
                if mx == 1:
                    line2 = ''
                    if _('gift') not in prod_name.lower():
                        line2 += _('period: %s ') % cur_date.strftime("%B").decode('utf-8')
                    if _('sponsorship') in prod_name.lower() or _('gift') in prod_name.lower() \
                        and prod_dict[prod_name] == 1:
                        line2 += str(names[prod_name])
                        
                    communication += wizard._complete_line(line2, 35)
                else:
                    beg_date = cur_date-relativedelta(months=mx-1)
                    communication += wizard._complete_line(_('period: %s to %s') % 
                                        (beg_date.strftime("%B").decode('utf-8'), cur_date.strftime("%B").decode('utf-8')), 35)
        elif nb_products in [3, 4]:
            for prod_name, qty in prod_dict_sort:
                communication += wizard._complete_line(_('%d %s') % (qty, prod_name), 35)
        elif nb_products > 4:
            for prod_name, qty in prod_dict_sort[:3]:
                communication += wizard._complete_line(_('%d %s') % (qty, prod_name), 35)
            communication += wizard._complete_line(_('%d other engagements') % sum([tup[1] for tup in prod_dict_sort[3:]]), 35)
        
        context['lang'] = lang_backup
        return communication