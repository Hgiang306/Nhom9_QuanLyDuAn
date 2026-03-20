from odoo import models, fields


class NhanVienExtend(models.Model):
    _inherit = 'nhan_vien'

    lich_su_lam_viec_ids = fields.One2many(
        'lich_su_lam_viec', 'nhan_vien_id', string='Lịch Sử Làm Việc'
    )
