# -*- coding: utf-8 -*-
{
    'name': "quan_ly_du_an",
    'summary': "Tổng hợp công việc (chỉ đọc)",
    'description': "Hiển thị toàn bộ công việc đã giao từ module quan_ly_cong_viec ở dạng chỉ đọc",
    'author': "FIT DNU",
    'license': 'LGPL-3',
    'website': "http://www.example.com",
    'category': 'Productivity',
    'version': '0.1',
    'depends': ['base', 'quan_ly_cong_viec'],
    'data': [
        'security/ir.model.access.csv',
        'security/record_rule.xml',
        'views/quan_ly_du_an_view.xml',
        'data/quan_ly_du_an_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}