{
    'name': 'Report to printer - Paper bin selection',
    'version': '10.0.1.0.0',
    'category': 'Printer',
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'license': 'AGPL-3',
    'depends': [
        'base_report_to_printer'
    ],
    'data': [
        'views/printing_printer.xml'
    ],
    'external_dependencies': {
        'python': ['cups'],
    },
    'installable': True,
    'application': False,
}
