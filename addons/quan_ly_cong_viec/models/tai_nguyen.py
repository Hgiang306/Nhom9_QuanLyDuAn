from odoo import models, fields, api
from odoo.exceptions import ValidationError


class TaiNguyen(models.Model):
    _name = 'tai_nguyen'
    _description = 'Tài Nguyên Dự Án (Nhân sự)'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one(
        'nhan_vien',
        string='Nhân viên',
        ondelete='restrict'
    )

    du_an_id = fields.Many2one(
        'du_an',
        string='Dự án',
        required=True,
        ondelete='cascade'
    )

    vai_tro = fields.Char(
        string='Vai trò trong dự án',
    )

    ty_le_tham_gia = fields.Float(
        string='Tỷ lệ tham gia (%)',
        default=100.0
    )

    ngay_bat_dau = fields.Date(
        string='Ngày bắt đầu'
    )

    ngay_ket_thuc = fields.Date(
        string='Ngày kết thúc'
    )

    ghi_chu = fields.Text(
        string='Ghi chú'
    )

    # ======================
    # VALIDATION
    # ======================

    @api.constrains('ty_le_tham_gia')
    def _check_ty_le_tham_gia(self):
        for rec in self:
            if rec.ty_le_tham_gia < 0 or rec.ty_le_tham_gia > 100:
                raise ValidationError(
                    "Tỷ lệ tham gia phải nằm trong khoảng 0 – 100%."
                )

    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc')
    def _check_ngay(self):
        for rec in self:
            if rec.ngay_bat_dau and rec.ngay_ket_thuc:
                if rec.ngay_ket_thuc < rec.ngay_bat_dau:
                    raise ValidationError(
                        "Ngày kết thúc không được nhỏ hơn ngày bắt đầu."
                    )

    _sql_constraints = [
        (
            'uniq_employee_du_an',
            'unique(employee_id, du_an_id)',
            'Một nhân viên chỉ được phân công một lần trong cùng dự án.'
        )
    ]
