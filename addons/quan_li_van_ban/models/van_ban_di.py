from odoo import models, fields

class VanBanDi(models.Model):
    _name = 'qlvb.van_ban_di'
    _description = 'Văn bản đi'

    so_van_ban = fields.Char(string='Số văn bản', required=True)
    ngay_di = fields.Date(string='Ngày đi')
    trich_yeu = fields.Text(string='Trích yếu')
