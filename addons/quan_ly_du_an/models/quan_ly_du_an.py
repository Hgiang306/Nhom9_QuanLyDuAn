from odoo import models, fields, api

class QuanLyDuAn(models.Model):
    _name = 'quan_ly_du_an.cong_viec'
    _description = 'Quản Lý Công Việc '

    name = fields.Char(string='Tên', required=True)

    cong_viec_ids = fields.Many2many(
        'cong_viec',
        string='Tất cả công việc',
        compute='_compute_cong_viec_ids',
        store=False
    )

    so_luong_cong_viec = fields.Integer(string='Số lượng công việc', compute='_compute_so_luong_cong_viec', store=False)

    @api.depends()
    def _compute_cong_viec_ids(self):
        CongViec = self.env['cong_viec'].sudo()
        all_tasks = CongViec.search([])
        for rec in self:
            rec.cong_viec_ids = all_tasks

    @api.depends('cong_viec_ids')
    def _compute_so_luong_cong_viec(self):
        for rec in self:
            rec.so_luong_cong_viec = len(rec.cong_viec_ids)
