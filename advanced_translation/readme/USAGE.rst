You can go in the Technical Settings/Translations/Advanced Translations

- Enter all terms you want to use
- Use method get of ir.advanced.translation in order to fetch translations
- Make models inherit the class 'translatable.model' so that they can now use these methods:
    - translate(field_name): Will retrieve the translation of a char/selection field and replaces keywords by
      advanced translations. Keywords should be placed in brackets.
    - get_list: Return comma separated field values (see doc in translatable_model.py)
    - get_date(field_name, date_format='date_full'): Returns a date field directly formatted in
      the format wanted. date_format can be an advanced translation which will return the date format
      wanted (can change depending on the language), or it can directly be a date format used by
      Babel package : http://babel.pocoo.org/en/latest/dates.html
