from odoo import models, fields, api
import json
from datetime import date

class BieuDoCongViec(models.Model):
    _name = 'bieu_do_cong_viec'
    _description = 'Biểu Đồ Công Việc'

    name = fields.Char(string="Tên báo cáo", default="Báo cáo tiến độ")
    cong_viec_id = fields.Many2one('cong_viec', string='Tiến độ công việc')