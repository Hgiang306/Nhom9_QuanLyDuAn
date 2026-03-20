# -*- coding: utf-8 -*-
from odoo import models, fields, api


class GiaiDoanCaNhan(models.Model):
    """Giai đoạn cá nhân của công việc - mỗi user có set riêng (Inbox/Today/This Week...)"""
    _name = 'giai_doan_ca_nhan'
    _description = 'Giai Đoạn Cá Nhân Công Việc'
    _order = 'sequence, id'
    _rec_name = 'ten_giai_doan'

    ten_giai_doan = fields.Char(string='Tên Giai Đoạn', required=True, translate=True)
    sequence = fields.Integer(string='Thứ Tự', default=10)
    user_id = fields.Many2one('res.users', string='Người Dùng', default=lambda self: self.env.uid, index=True)
    fold = fields.Boolean(string='Thu gọn', default=False)

    _sql_constraints = [
        ('unique_user_stage', 'UNIQUE(ten_giai_doan, user_id)',
         'Mỗi người dùng chỉ có một giai đoạn cùng tên.'),
    ]

    @api.model
    def _get_or_create_default_stages(self):
        """Tạo các giai đoạn mặc định cho user hiện tại nếu chưa có."""
        uid = self.env.uid
        defaults = [
            ('Inbox', 1, False),
            ('Today', 2, False),
            ('This Week', 3, False),
            ('This Month', 4, False),
            ('Later', 5, False),
            ('Done', 6, True),
        ]
        for name, seq, fold in defaults:
            existing = self.search([('ten_giai_doan', '=', name), ('user_id', '=', uid)], limit=1)
            if not existing:
                self.create({'ten_giai_doan': name, 'sequence': seq, 'user_id': uid, 'fold': fold})
        return self.search([('user_id', '=', uid)], order='sequence')
