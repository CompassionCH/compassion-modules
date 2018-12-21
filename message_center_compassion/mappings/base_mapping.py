# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import collections

# Utility method to update nested dictionaries
# http://stackoverflow.com/questions/3232943/
# update-value-of-a-nested-dictionary-of-varying-depth


def nested_update(_dic, _dic_update):
    for key, value in _dic_update.iteritems():
        if isinstance(value, collections.Mapping):
            r = nested_update(_dic.get(key, {}), value)
            _dic[key] = r
        else:
            _dic[key] = _dic_update[key]
    return _dic


class OnrampMapping(object):
    """ Base class for mappings between an Odoo object and the JSON
    representation used by Compassion Connect services.

    It gives one classmethod useful to convert received JSON data from
    Compassion Connect to valid Odoo object values.
    """

    ODOO_MODEL = ''
    MAPPING_NAME = 'default'

    # Dictionary containing the mapping in the following format :
    #   {'ConnectServiceFieldName' : 'odoo_field_name'}
    #
    # Valid 'odoo_field_name' values can be :
    #
    #   - string : any existing field in the Odoo model
    #   - None : indicates we don't use the field value.
    #   - (relational_path, model, optional_action : For relational fields,
    #           a tuple precising the relation model and an optional action.
    #
    #       Caution : it supports only direct relations ! If you traverse
    #       several models for the relation, you should put a related
    #       field in the correspondence model in order to get
    #       the mapping work !
    CONNECT_MAPPING = dict()

    # Dictionary of model field names to send to Compassion Connect.
    #   {'odoo_field_name': convert_options}
    #
    # convert_options can be :
    #   - None : no conversion will be performed
    #   - function : the given function will be called with the field value
    #                as parameter in order to get a converted value.
    FIELDS_TO_SUBMIT = dict()

    # Dictionary of constant values that are sent for all objects
    # to Compassion Connect services
    CONSTANTS = dict()

    def __init__(self, env):
        self.env = env

    def get_vals_from_connect(self, commkit_data, _mapping=None):
        """ Converts Compassion Connect data into a dictionary of
        odoo.model field_connect values.
        """
        if _mapping is None:
            _mapping = self.CONNECT_MAPPING
        odoo_values = dict()
        for field_connect, value_connect in commkit_data.iteritems():
            if isinstance(value_connect, collections.Mapping):
                # Recursively call function to get the mapping of the section
                odoo_values.update(self.get_vals_from_connect(
                    value_connect, _mapping.get(field_connect)))
            else:
                field_odoo = _mapping.get(field_connect)
                is_list_dict = False
                if field_odoo and isinstance(value_connect, list):
                    # Check if we receive a list of dictionnaries and
                    # recursively call function to get the mapping of each
                    for item in value_connect:
                        if isinstance(item, collections.Mapping):
                            is_list_dict = True
                            if len(field_odoo) >= 2:
                                sub_mapping = new_onramp_mapping(
                                    field_odoo[1], self.env)
                            else:
                                sub_mapping = new_onramp_mapping(
                                    field_odoo[1], self.env,
                                    field_odoo[2])
                            list_dict = odoo_values.setdefault(
                                field_odoo[0], list())
                            list_dict.append(
                                sub_mapping.get_vals_from_connect(item))
                if field_odoo and value_connect not in [[], (), {}, None] \
                        and not is_list_dict:
                    odoo_values.update(self._convert_connect_data(
                        field_connect, field_odoo, value_connect))
        if odoo_values:
            self._process_odoo_data(odoo_values)
        return odoo_values

    def get_connect_data(self, odoo_object, fields_to_submit=None):
        """ Convert an Odoo object into valid data for Compassion Connect.
        :param odoo_object: One odoo Record.
        :param fields_to_submit: list of field names to convert.
                                 if not given, will take what is defined
                                 by default in the mapping class.
        """
        connect_data = dict()
        if fields_to_submit is None:
            fields_to_submit = self.FIELDS_TO_SUBMIT.keys()
        for connect_name in fields_to_submit:
            # Constant values are not retrieved from Odoo fields
            if connect_name in self.CONSTANTS:
                constant_res = self._create_dict_from_path(
                    connect_name, self.CONSTANTS[connect_name])
                nested_update(connect_data, constant_res)
                continue

            # Find Odoo field name and convert value
            # using the provided conversion function
            field_path = connect_name.split('.')
            field_mapping = self.CONNECT_MAPPING
            field_name = ''
            for name in field_path:
                field_mapping = field_mapping[name]
                if isinstance(field_mapping, tuple):
                    field_name = field_mapping[0]
                else:
                    field_name = field_mapping

            value = odoo_object
            for field in field_name.split('.'):
                # Field One2Many
                if field_name.endswith('ids'):
                    value = list()
                    if len(field_mapping) == 2:
                        sub_mapping = new_onramp_mapping(
                            field_mapping[1], self.env)
                    else:
                        sub_mapping = new_onramp_mapping(
                            field_mapping[1], self.env, field_mapping[2])
                    for element in getattr(odoo_object, field):
                        value.append(sub_mapping.get_connect_data(element))
                # Other fields
                else:
                    value = value.mapped(field) if len(value) > 1 else \
                        getattr(value, field)

            convert_func = self.FIELDS_TO_SUBMIT[connect_name]
            if convert_func is not None:
                value = convert_func(value)

            nested_update(
                connect_data,
                self._create_dict_from_path(connect_name, value))

        self._process_connect_data(connect_data)
        return connect_data

    def _convert_connect_data(self, connect_name, value_mapping, value,
                              relation_search=None):
        """ Converts a received data from Connect to odoo field:value
            dictionary.

            :param connect_name: Field name of Connect
            :param value_mapping: The value of the mapping for this field
                                  found in CONNECT_MAPPING
            :param value: Connect value for the field.
            :param relation_search: Optional additional search domain to
                                    limit the search results of a relation.

            :returns: a dictionary holding the field:value pair for Odoo"""
        result = dict()
        if isinstance(value_mapping, tuple):
            # Relational field
            relation_obj = self.env[value_mapping[1]].with_context(
                lang='en_US')
            correspondence_field = value_mapping[0].split('.')[0]
            relation_field = value_mapping[0].split('.')[-1]
            operator = 'in' if isinstance(value, list) else '=ilike'
            if relation_search is None:
                relation_search = list()
            relation_search.extend([(relation_field, operator, value)])
            relation_ids = relation_obj.search(relation_search).ids
            if correspondence_field.endswith('ids') and relation_ids:
                # Many2many write
                result[correspondence_field] = [(6, 0, relation_ids)]
            elif relation_ids:
                # Many2one write
                result[correspondence_field] = relation_ids[0]
        else:
            # Regular field
            result[value_mapping] = value

        return result

    def _create_dict_from_path(self, path, value):
        """ Creates nested dictionaries given a path and a value.
        :param path: string with dots separating the keys i.e. 'key1.key2'
        :param value: the final value

        :returns: a nested dictionary like {'key1': {'key2': value}}
        """
        res = dict()
        current_dict = res
        key_list = path.split('.')
        for index in range(0, len(key_list)):
            key = key_list[index]
            if index == len(key_list) - 1:
                current_dict[key] = value
            else:
                current_dict[key] = dict()
                current_dict = current_dict[key]
        return res

    def _process_connect_data(self, connect_data):
        """ Inherit to do some processing before sending connect_data.

        :param connect_data: dictionary that will be returned."""
        pass

    def _process_odoo_data(self, odoo_data):
        """ Inherit to do some processing before sending odoo_data

        :param odoo_data: dictionary that will be returned."""
        pass


def itersubclasses(cls, _seen=None):
    """
    itersubclasses(cls)

    Generator over all subclasses of a given class, in depth first order.

    >>> list(itersubclasses(int)) == [bool]
    True
    >>> class A(object): pass
    >>> class B(A): pass
    >>> class C(A): pass
    >>> class D(B,C): pass
    >>> class E(D): pass
    >>>
    >>> for cls in itersubclasses(A):
    ...     print(cls.__name__)
    B
    D
    E
    C
    >>> # get ALL (new-style) classes currently defined
    >>> [cls.__name__ for cls in itersubclasses(object)] #doctest: +ELLIPSIS
    ['type', ...'tuple', ...]
    """
    if not isinstance(cls, type):
        raise TypeError('itersubclasses must be called with '
                        'new-style classes, not %.100r' % cls)
    if _seen is None:
        _seen = set()
    try:
        subs = cls.__subclasses__()
    except TypeError:  # fails only when cls is type
        subs = cls.__subclasses__(cls)
    for sub in subs:
        if sub not in _seen:
            _seen.add(sub)
            yield sub
            for sub in itersubclasses(sub, _seen):
                yield sub


def new_onramp_mapping(model, env, mapping_name='default'):
    """Return an instance of the good Mapping class based on the given model.

    :param model: model name of the mapping.
    :param action: action name (not mandatory, specify when a model has many
    actions)
    :return: class instance for given model mapping.
    """
    if not mapping_name:
        mapping_name = 'default'
    for cls in itersubclasses(OnrampMapping):
        if cls.ODOO_MODEL == model and cls.MAPPING_NAME == mapping_name:
            return cls(env)
    raise ValueError
