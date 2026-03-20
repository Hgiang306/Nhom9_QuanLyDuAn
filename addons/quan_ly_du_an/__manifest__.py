# -*- coding: utf-8 -*-
{
    'name': "quan_ly_du_an",
    'summary': "Quản lý dự án",
    'description': "Module quản lý dự án, tài nguyên, ngân sách, chi phí, rủi ro",
    'author': "FIT DNU",
    'license': 'LGPL-3',
    'website': "http://www.example.com",
    'category': 'Productivity',
    'version': '0.1',
    'depends': ['base', 'nhan_su', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/record_rule.xml',
        'views/du_an_view.xml',
        'views/tai_nguyen.xml',
        'views/ngan_sach_du_an_view.xml',
        'views/chi_phi_du_an_view.xml',
        'views/rui_ro_view.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'quan_ly_du_an/static/src/css/du_an.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
