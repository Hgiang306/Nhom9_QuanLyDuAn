# -*- coding: utf-8 -*-
{
    'name': 'Chatbot Quản Lý Dự Án',
    'summary': 'AI Chatbot hỗ trợ quản lý dự án và công việc',
    'version': '0.1',
    'author': 'FIT DNU',
    'license': 'LGPL-3',
    'category': 'Productivity',
    'depends': ['base', 'mail', 'web', 'quan_ly_du_an', 'quan_ly_cong_viec'],
    'data': [
        'security/ir.model.access.csv',
        'data/chatbot_data.xml',
        'views/chatbot_view.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/quan_ly_chatbot/static/src/chatbot.css',
            '/quan_ly_chatbot/static/src/chatbot.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
