from odoo import models, fields

class LoaiVanBan(models.Model):
    _name = 'qlvb.loai_van_ban'
    _description = 'Loại văn bản'

    name = fields.Char(string='Tên loại văn bản', required=True)
    ghi_chu = fields.Text(string='Ghi chú')
