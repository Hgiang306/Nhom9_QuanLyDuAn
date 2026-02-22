{
    'name': 'Quản lý văn bản',
    'version': '1.0',
    'summary': 'Quản lý văn bản đến và đi',
    'description': 'Simple document management for inbound and outbound documents.',
    'category': 'Custom',
    'author': 'Local',
    'depends': [
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',

        'views/loai_van_ban.xml',

        'views/van_ban_den_search.xml',
        'views/van_ban_den.xml',

        'views/van_ban_di_search.xml',
        'views/van_ban_di.xml',

        'views/menu.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
