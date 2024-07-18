# -*- coding: utf-8 -*-
{
    'name': 'SOS Accounting',
    'version': '16.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Tableau prévisionnel de trésorerie',
    'description': """
        Module pour générer un tableau prévisionnel de trésorerie.
    """,
    'author': 'Henintsoa Moria',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/sos_accounting_view.xml',
        'views/menu.xml',
        'wizard/sos_accounting_wizard_view.xml',
        'wizard/sos_accounting_update_wizard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
