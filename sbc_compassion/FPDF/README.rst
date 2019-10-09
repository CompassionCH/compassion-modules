==========================================
FPDF - PDF Generator
==========================================
FPDF generate a PDF using PHP, using different template

Installation
============
To install this module, you need to install dependencies:
    * requires the following libraries (names from apt-get):
        - json
        - subprocess
    * requires PHP (tested and working on PHP 7.2 and 7.3)

Structure of the json to generate a PDF
---------------------------------------

5 possible keys:
    * 'images': a list of images to display
    * 'templates': :code:`[background image, [header list], [list of boxes], [list of images]]`, where:
          - the header list is like this: :code:`[filename text, minX, minY, maxX, maxY, cell height]` (empty list if there is no header in this template) the header repeat itself on every page of the template
          - a box is like this: :code:`[minX, minY, maxX, maxY, type, cell height]` (empty list if there is no text box in this template) where the type is 'Original' for original and 'Translation' for translated (for example, it can be anything)
          - an image box is like this. [minX, minY, maxX, maxY]`
    * 'texts': a list of :code:`[text, type]` corresponding to the type defined in the templates with the text content
    * 'original_size': the page number of the original document
    * 'overflow_template': one particular template which will be used when text is overflowing. If not provided, the last template pages will be repeated.
    * 'lang': The lang of generation

The number of pages will be determined by the text length and the number of template if the text (number of pages) is smaller than the number of template

Example of json of a template:

::

    {
        'images': ['b.png', 'c.png', 'd.png'],
        'templates': [[p1.png,
                       [header_filename, '5', '8', '70', '30', '5'],
                       [['0', '70', '100.5', '230', 'Original', '5.32'],
                        ['109', '51.5', '197.5', '215', 'Translation', '5.32']],
                       []
                       ],
                      [p2.png,
                       [],
                       [['0', '21', '101', '255', 'Original', '7.2'],
                        ['109', '13', '197.5', '257', 'Translation', '7.2']],
                       []]
                      ]
        'texts': [[text_original_filename, 'Original'],
                  [text_translated_filename, 'Translation']],
        'original_size': 2,
        'overflow_template': [ov1.png,
                       [header_filename, '5', '8', '70', '30', '5'],
                       [['0', '70', '100.5', '230', 'Original', '5.32'],
                        ['109', '51.5', '197.5', '215', 'Translation', '5.32']],
                       []
                       ],
        'lang': 'fr_CH'
    }

Test
----

To test to generate a PDF go to *url*/generatePDF or *url*/generatePDF/*name_of_pdf*, if the PDF was successfully generated, it will be on sbc_compassion/FPDF/test.pdf
or sbc_compassion/FPDF/*name_of_pdf*.pdf (follow the link on the page).

If nothing happens check sbc_compassion/FPDF/std_err.txt for error that happened on the PHP script.

Going to the link *url*/generatePDF will call the function :code:`generate_pdf_test` on correspondence_template.py which will create the example and call :code:`generate_pdf` on the same file.

:code:`generate_pdf` is close to be generic enough to generate pdf for any template, text and image possible.

Maintainer
----------

This module is maintained by `Compassion Switzerland <https://www.compassion.ch>`.
