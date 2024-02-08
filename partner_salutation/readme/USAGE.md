The module adds a salutation that is computed in English only. You can
inherit it and add other languages by defining new methods on the
*res.partner* model: *def \_\_get_salutation\_\<lang_Code\>*. The method
should return the full salutation string.
