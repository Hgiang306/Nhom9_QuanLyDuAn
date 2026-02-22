# -*- coding: utf-8 -*-
{
    'name': "quan_ly_cong_viec",
    'summary': "Quản lý công việc và dự án",
    'description': "Module quản lý công việc và dự án với biểu đồ",
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'license': 'LGPL-3',
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'nhan_su', 'mail', 'board'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/record_rule.xml',
        'views/du_an_view.xml',
        'views/giai_doan_cong_viec_view.xml',
        'views/cong_viec_view.xml',
        'views/nhat_ky_cong_viec_view.xml',
        'views/tai_nguyen.xml',
        'views/danh_gia_nhan_vien_view.xml',
        'views/ngan_sach_du_an_view.xml',
        'views/chi_phi_du_an_view.xml',
        'views/dashboard_view.xml',
        'views/action_my_cong_viec.xml',
        'views/bieu_do_cong_viec_view.xml', 
        'views/menu.xml',  # Load sau cùng
    ],
    'icon': '/quan_ly_cong_viec/static/description/image.png',
    'assets': {
        'web.assets_backend': [
            'https://cdn.jsdelivr.net/npm/chart.js',
            '/quan_ly_cong_viec/static/css/dashboard.css',
            '/quan_ly_cong_viec/static/css/modern_dashboard.css',
            '/quan_ly_cong_viec/static/js/bieu_do_cong_viec.js',
            '/quan_ly_cong_viec/static/js/progress_chart.js',
            
        ],
    },
}