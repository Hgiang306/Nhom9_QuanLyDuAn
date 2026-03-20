# -*- coding: utf-8 -*-

from . import controllers
from . import models


def post_migrate(cr, version):
    """Tính lại tiến độ toàn bộ dữ liệu cũ sau mỗi lần update module."""
    from odoo import api, SUPERUSER_ID
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        # Tính lại phan_tram_cong_viec cho tất cả công việc
        cong_viecs = env['cong_viec'].search([])
        cong_viecs._compute_phan_tram_cong_viec()
        # Tính lại phan_tram_du_an cho tất cả dự án
        du_ans = env['du_an'].search([])
        du_ans._compute_phan_tram_du_an()


def post_init_hook(cr, registry):
    """Tạo giai đoạn cá nhân mặc định cho tất cả users hiện có."""
    from odoo import api, SUPERUSER_ID
    from odoo.api import Environment
    with Environment.manage():
        env = Environment(cr, SUPERUSER_ID, {})
        users = env['res.users'].search([('share', '=', False), ('active', '=', True)])
        defaults = [
            ('Inbox', 1, False),
            ('Today', 2, False),
            ('This Week', 3, False),
            ('This Month', 4, False),
            ('Later', 5, False),
            ('Done', 6, True),
        ]
        for user in users:
            for name, seq, fold in defaults:
                existing = env['giai_doan_ca_nhan'].search([
                    ('ten_giai_doan', '=', name),
                    ('user_id', '=', user.id),
                ], limit=1)
                if not existing:
                    env['giai_doan_ca_nhan'].create({
                        'ten_giai_doan': name,
                        'sequence': seq,
                        'user_id': user.id,
                        'fold': fold,
                    })