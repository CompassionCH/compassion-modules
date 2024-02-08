To use this module, you need to:

- Inherit the module
- Use *self.env\["res.partner.match"\].match_values_to_partner(vals)*
  method in order to match partner given some partner data dictionary.
- Inherit *\_process_create_infos* method if you want to customize
  partner creation (in case of match fail)
- Inherit *\_process_update_vals* method if you want to customize
  partner update (in case of match success)
- Inherit *\_match_get_rules_order* in order to alter match rules order,
  or to add remove any rule
- Add a method *\_match\_\<rule_name\>* in order to add a new match rule
- Inherit *\_get_valid_create_fields* to restrict/extend fields allowed
  for partner creation.
- Inherit *\_get_valid_update_fields* to restrict/extend fields allowed
  for partner update.
