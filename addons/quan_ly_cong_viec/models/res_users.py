from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    nhan_vien_id = fields.Many2one(
        'nhan_vien',
        string='Nhân viên'
    )
