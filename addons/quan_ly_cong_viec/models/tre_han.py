# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date


class TreHan(models.Model):
    _name = 'tre_han'
    _description = 'Công việc trễ hạn'
    _rec_name = 'cong_viec_id'
    _order = 'so_ngay_tre desc'

    cong_viec_id = fields.Many2one('cong_viec', string='Công Việc', ondelete='cascade', required=True)
    du_an_id     = fields.Many2one('du_an', string='Dự Án', related='cong_viec_id.du_an_id', store=True)
    han_chot     = fields.Datetime(string='Hạn Chót', related='cong_viec_id.han_chot', store=True)
    trang_thai   = fields.Selection(related='cong_viec_id.trang_thai', string='Trạng Thái', store=True)
    nhan_vien_ids= fields.Many2many(related='cong_viec_id.nhan_vien_ids', string='Nhân Viên')

    ngay_phat_hien = fields.Date(string='Ngày Phát Hiện', default=fields.Date.today, readonly=True)
    so_ngay_tre    = fields.Integer(string='Số Ngày Trễ', compute='_compute_so_ngay_tre', store=True)
    muc_do         = fields.Selection([
        ('nhe',   '🟡 Nhẹ (1-3 ngày)'),
        ('trung', '🟠 Trung bình (4-7 ngày)'),
        ('nang',  '🔴 Nặng (>7 ngày)'),
    ], string='Mức Độ', compute='_compute_so_ngay_tre', store=True)
    da_xu_ly = fields.Boolean(string='Đã Xử Lý', default=False)
    ghi_chu  = fields.Text(string='Ghi Chú')

    _sql_constraints = [
        ('unique_cong_viec', 'UNIQUE(cong_viec_id)', 'Công việc này đã có trong danh sách trễ hạn!'),
    ]

    @api.depends('han_chot')
    def _compute_so_ngay_tre(self):
        today = date.today()
        for r in self:
            if r.han_chot:
                delta = (today - r.han_chot.date()).days
                r.so_ngay_tre = max(delta, 0)
            else:
                r.so_ngay_tre = 0
            # Phân loại mức độ
            if r.so_ngay_tre <= 0:
                r.muc_do = False
            elif r.so_ngay_tre <= 3:
                r.muc_do = 'nhe'
            elif r.so_ngay_tre <= 7:
                r.muc_do = 'trung'
            else:
                r.muc_do = 'nang'

    @api.model
    def cap_nhat_tre_han(self):
        """Cron job: quét công việc quá hạn chưa hoàn thành, thêm vào danh sách."""
        now = fields.Datetime.now()
        trang_thai_chua_xong = ['cho_xac_nhan', 'dang_thuc_hien', 'tri_hoan', 'cho_phe_duyet']

        cv_tre = self.env['cong_viec'].search([
            ('han_chot', '<', now),
            ('trang_thai', 'in', trang_thai_chua_xong),
        ])

        existing_ids = self.search([]).mapped('cong_viec_id').ids

        for cv in cv_tre:
            if cv.id not in existing_ids:
                self.create({'cong_viec_id': cv.id})

        # Cập nhật so_ngay_tre cho các record hiện có chưa xử lý
        self.search([('da_xu_ly', '=', False)])._compute_so_ngay_tre()

        # Tự đánh dấu đã xử lý nếu công việc đã hoàn thành
        done = self.search([
            ('da_xu_ly', '=', False),
            ('trang_thai', 'in', ['hoan_thanh', 'tu_choi']),
        ])
        done.write({'da_xu_ly': True})
