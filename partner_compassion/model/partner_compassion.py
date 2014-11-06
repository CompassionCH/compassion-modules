# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
from openerp.osv import fields, orm
from openerp.tools.translate import _
from . import gp_connector

# fields that are synced if 'use_parent_address' is checked
ADDRESS_FIELDS = (
    'street', 'street2', 'street3', 'zip', 'city', 'state_id', 'country_id')


class ResPartner(orm.Model):
    """ This class upgrade the partners to match Compassion needs.
        It also synchronize all changes with the MySQL server of GP.
    """

    _inherit = 'res.partner'

    def _is_church(self, cr, uid, ids, field_name, arg, context=None):
        """ Tell if the given Partners are Church Partners
            (by looking at their categories). """
        # Set the default return value to False
        res = dict.fromkeys(ids, False)

        # Retrieve all the categories and check if one is Church
        for record in self.browse(cr, uid, ids, context):
            for category in record.category_id:
                if category.name.upper() in ('CHURCH', 'EGLISE', 'KIRCHE'):
                    res[record.id] = True

        return res

    def _get_church_partner(self, cr, uid, ids, context=None):
        """ Used to recompute the 'is_church' field when a partner's
            categories are modified. """
        return ids

    def _get_receipt_types(self, cursor, uid, context=None):
        """ Display values for the receipt selection fields. """
        lang = self.pool.get('res.users').browse(cursor, uid, uid).lang
        if (lang == 'fr_FR') or (lang == 'fr_CH'):
            res = (
                ('no', 'Pas de reçu'),
                ('default', 'Par défaut'),
                ('email', 'Par e-mail'),
                ('paper', 'Version papier')
            )
        else:
            res = (
                ('no', 'No receipt'),
                ('default', 'Default'),
                ('email', 'By e-mail'),
                ('paper', 'On paper')
            )
        return res

    def create(self, cr, uid, vals, context=None):
        """ We override the create method so that each partner creation will
            also propagate in the MySQL table used by GP. This method is also
            called by GP with XMLRPC, so that the Odoo holds all the logic
            to sync the two databases.
        """

        gp = gp_connector.GPConnect(cr, uid)
        fieldsUpdate = vals.keys()

        # If the reference is not defined, we automatically set it.
        if 'ref' not in fieldsUpdate:
            # If the contact has a parent and uses his address, plus the parent
            # has a reference, we use the same reference.
            if 'parent_id' in fieldsUpdate and vals['parent_id'] and \
               'use_parent_address' in fieldsUpdate and \
               vals['use_parent_address']:
                vals['ref'] = self.browse(
                    cr, uid, vals['parent_id'], context=context).ref
            # Otherwise we attribute a new reference number
            else:
                vals['ref'] = gp.nextRef()

        # Create the partner in Odoo, with original values, before exporting
        # to MySQL.
        new_id = super(ResPartner, self).create(cr, uid, vals,
                                                context=context)
        partner = self.browse(cr, uid, new_id, context=context)

        # Set some special fields that need a conversion before sending to
        # MySQL
        title = ""
        if partner.title.id:
            title = self.pool.get('res.partner.title').browse(
                cr, uid, partner.title.id, {'lang': 'en_US'}).name
        churchRef = partner.church_id.ref
        countryCode = partner.country_id.code
        categories = self._get_category_names(partner, cr, uid)

        # Id of the ERP partner referenced in the MySQL table (should be a
        # child partner (contact)).
        linkId = new_id

        # If the partner has children with the same address, we need to
        # perform some verifications
        for child_record in partner.child_ids:
            if child_record.use_parent_address:
                # Set the correct reference id
                linkId = child_record.id
                # Don't update some values that are defined by the child
                # partner.
                del vals['abroad']
                del vals['opt_out']
                del vals['thankyou_letter']
                del vals['tax_certificate']
                del vals['title']

        # Don't unset the "Mailing complet" category, the parent wants to
        # receive it.
        if partner.use_parent_address and not partner.parent_id.opt_out and \
           'opt_out' in fieldsUpdate:
            del vals['opt_out']

        gp.createPartner(
            uid, vals, partner, linkId, title, churchRef, categories,
            countryCode)
        # Release connection
        del(gp)
        return new_id

    def create_from_gp(self, cr, uid, vals, context=None):
        """ Simple create method that skips MySQL insertion, since it is
            called from GP in order to export the addresses. """
        return super(ResPartner, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        """ We override the write method so that each update will also update
            the partner in the MySQL table used by GP. This method is also
            called by GP with XMLRPC, so that the update syncs the two
            databases. """
        # We first call the original write method and update the records.
        result = super(ResPartner, self).write(
            cr, uid, ids, vals, context=context)

        # Some fields that need some conversion before sending to MySQL
        categories = []
        churchRef = ""
        countryCode = ""
        title = ""

        records = self.browse(cr, uid, ids, context)
        records = [records] if not isinstance(records, list) else records
        create = False
        gp = gp_connector.GPConnect(cr, uid)

        for record in records:
            if record.ref:
                # Handle the change of parent_id and use_parent_address
                if 'use_parent_address' in vals.keys() and record.parent_id:
                    if vals['use_parent_address']:
                        # Change the MySQL partner so that it is linked to the
                        # contact
                        gp.linkContact(uid, record.parent_id.ref, record.id)
                        # Merge contact with parent
                        vals['ref'] = record.parent_id.ref
                    else:
                        # Change the MySQL company partner so that it is no
                        # more linked to the contact of the company
                        gp.unlinkContact(
                            uid, record.parent_id,
                            self._get_category_names(record.parent_id, cr,
                                                     uid))
                        # Link with contact in GP and sync or create new
                        # contact if it doesn't exist.
                        ref = gp.getRefContact(record.id)
                        if ref < 0:
                            ref = str(gp.nextRef())
                            create = True
                        vals['ref'] = ref
                    # Write the new reference in OpenERP
                    super(ResPartner, self).write(
                        cr, uid, record.id, vals, context=context)
                    record.ref = vals['ref']
                    # We need to copy all partner fields in the new referenced
                    # partner in MySQL
                    self._fill_fields(record, vals)

                # Handle the change of the company status (weird update, but
                # could happen!)
                if 'is_company' in vals.keys():
                    if vals['is_company']:
                        gp.changeToCompany(uid, record.ref, record.name)
                    else:
                        # Unlink the contact, if any exists.
                        gp.unlinkContact(
                            uid, record,
                            self._get_category_names(record, cr, uid))
                        gp.changeToPrivate(uid, record.ref)
            else:
                # The partner has no relation to MySQL ! Fix it.
                self._fill_fields(record, vals)
                ref = gp.getRefContact(record.id)
                if ref < 0:
                    ref = str(gp.nextRef())
                    create = True
                vals['ref'] = ref
                # Write the new reference in OpenERP
                record.ref = ref
                super(ResPartner, self).write(
                    cr, uid, record.id, vals, context=context)

            # Get the special fields values
            title = ""
            if record.title.id:
                title = self.pool.get('res.partner.title').browse(
                    cr, uid, record.title.id, {'lang': 'en_US'}).name
            churchRef = record.church_id.ref
            categories = self._get_category_names(record, cr, uid)
            countryCode = record.country_id.code

            # Update the MySQL table with the retrieved values.
            if create:
                gp.createPartner(
                    uid, vals, record, record.id, title, churchRef,
                    categories, countryCode)
            else:
                gp.updatePartner(
                    uid, vals, record, title, churchRef, categories,
                    countryCode)

        # Release connection
        del(gp)
        return result

    def _get_category_names(self, record, cr, uid, context={'lang': 'en_US'}):
        """ Get a list of the category names of all linked partners.

        Args:
            record (res.partner) : The current partner for which we search
                                   the categories

        Returns:
            A list of strings containing the category names of the current
            partner, his parent and children.
        """
        categories = []
        ids = map(lambda category: category.id, record.category_id)
        category_obj = self.pool.get('res.partner.category')
        for category in category_obj.browse(cr, uid, ids, context):
            categories.append(category.name)
        if record.use_parent_address and record.parent_id:
            for category in category_obj.browse(cr, uid,
                                                record.parent_id.category_id,
                                                context):
                categories.append(category.id.name)
        for child_record in record.child_ids:
            if child_record.use_parent_address:
                for category in category_obj.browse(cr, uid,
                                                    child_record.category_id,
                                                    context):
                    categories.append(category.id.name)
        return categories

    def write_from_gp(self, cr, uid, ids, vals, context=None):
        """ Simple write method that skips MySQL insertion, since it is
        called from GP in order to export the addresses. """
        return super(ResPartner, self).write(cr, uid, ids, vals,
                                             context=context)

    ##########################################################################
    #                        NEW PARTNER FIELDS                              #
    ##########################################################################
    _columns = {
        'street3': fields.char("Street3", size=128),
        'member_ids': fields.one2many(
            'res.partner', 'church_id', 'Members',
            domain=[('active', '=', True)]),
        'is_church': fields.function(
            _is_church, type='boolean', method=True, string="Is a Church",
            store={'res.partner': (_get_church_partner, ['category_id'], 10)}
        ),
        'church_id': fields.many2one(
            'res.partner', 'Church', domain=[('is_church', '=', True)]),
        'church_unlinked': fields.char(
            _("Church (N/A)"),
            help=_("Use this field if the church of the partner"
                   " can not correctly be determined and linked.")),
        'deathdate': fields.date(_('Death date')),
        'birthdate': fields.date(_('Birthdate')),
        'nbmag': fields.integer(_('Number of Magazines'), size=2,
                                required=True),
        'tax_certificate': fields.selection(
            _get_receipt_types, _('Tax certificate'), required=True),
        'thankyou_letter': fields.selection(
            _get_receipt_types, _('Thank you letter'), required=True),
        'calendar': fields.boolean(
            _('Calendar'),
            help=_("Indicates if the partner wants to receive the Compassion "
                   "calendar.")),
        'christmas_card': fields.boolean(
            _('Christmas Card'),
            help=_("Indicates if the partner wants to receive the "
                   "christmas card.")),
        'birthday_reminder': fields.boolean(
            _('Birthday Reminder'),
            help=_("Indicates if the partner wants to receive a birthday "
                   "reminder of his child.")),
        'abroad': fields.boolean(
            _('Abroad/Only e-mail'),
            help=_("Indicates if the partner is abroad and should only be "
                   "updated by e-mail")),
    }

    _defaults = {
        'nbmag': 0,
        'tax_certificate': 'default',
        'thankyou_letter': 'default',
        'calendar': True,
        'christmas_card': True,
        'birthday_reminder': True,
        'opt_out': True,
    }

    def _fill_fields(self, record, vals):
        """ Fills all needed vals for the MySQL table. """
        vals['title'] = record.title.id
        vals['lang'] = record.lang
        vals['firstname'] = record.firstname
        vals['lastname'] = record.lastname
        vals['function'] = record.function
        vals['nbmag'] = record.nbmag
        vals['calendar'] = record.calendar
        vals['tax_certificate'] = record.tax_certificate
        vals['thankyou_letter'] = record.thankyou_letter
        vals['abroad'] = record.abroad
        vals['opt_out'] = record.opt_out
        vals['mobile'] = record.mobile
        vals['category_id'] = record.category_id
        if not record.use_parent_address:
            # Creation of new partner, add all possible fields.
            vals['street'] = record.street
            vals['street2'] = record.street2
            vals['street3'] = record.street3
            vals['city'] = record.city
            vals['zip'] = record.zip
            vals['country_id'] = record.country_id.id
            vals['birthdate'] = record.birthdate
            vals['deathdate'] = record.deathdate
            vals['phone'] = record.phone
            vals['email'] = record.email
            vals['church_id'] = record.church_id  # TODO Bug !
            vals['church_unlinked'] = record.church_unlinked
            vals['date'] = record.date

    def _address_fields(self, cr, uid, context=None):
        """ Returns the list of address fields that are synced from the parent
        when the `use_parent_address` flag is set. """
        return list(ADDRESS_FIELDS)

    def _display_address(self, cr, uid, address, without_company=False,
                         context=None):
        """ Build and return an address formatted accordingly to
        Compassion standards.

        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its country
                  habits (or the default ones if not country is specified)
        :rtype: string
        """

        # get the information that will be injected into the display format
        # get the address format
        address_format = "%(street)s\n%(street2)s\n%(street3)s\n%(city)s " \
                         "%(state_code)s %(zip)s\n%(country_name)s"
        args = {
            'state_code': address.state_id and address.state_id.code or '',
            'state_name': address.state_id and address.state_id.name or '',
            'country_code':
                address.country_id and address.country_id.code or '',
            'country_name':
                address.country_id and address.country_id.name or '',
            'company_name':
                address.parent_id and address.parent_id.name or '',
        }

        for field in self._address_fields(cr, uid, context=context):
            args[field] = getattr(address, field) or ''

        if without_company:
            args['company_name'] = ''
        elif address.parent_id:
            address_format = '%(company_name)s\n' + address_format
        return address_format % args

    def unlink(self, cr, uid, ids, context=None):
        """ We want to perform some checks before deleting a partner ! """
        records = self.browse(cr, uid, ids, context)
        records = [records] if not isinstance(records, list) else records
        gp = gp_connector.GPConnect(cr, uid)
        for record in records:
            # If it is a company, unlink contact in MySQL if there is any.
            if record.is_company:
                for child in record.child_ids:
                    if child.use_parent_address:
                        gp.unlinkContact(
                            uid, record, self._get_category_names(record, cr,
                                                                  uid))

            # If it is a contact, unlink from company.
            if record.use_parent_address and record.parent_id:
                gp.unlinkContact(
                    uid, record.parent_id, self._get_category_names(
                        record.parent_id, cr, uid))

            # Unlink from MySQL
            gp.unlink(uid, record.id)

        del(gp)
        return super(ResPartner, self).unlink(cr, uid, ids, context)
