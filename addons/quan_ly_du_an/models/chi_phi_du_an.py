from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class ChiPhiDuAn(models.Model):
    _name = 'chi_phi_du_an'
    _description = 'Chi Phí Dự Án'
    _rec_name = 'ten_chi_phi'
    _order = 'ngay_chi desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ================== FIELDS ==================

    ten_chi_phi = fields.Char(string='Tên Chi Phí', required=True)
    du_an_id = fields.Many2one(
        'du_an', string='Dự Án', required=True, ondelete='cascade'
    )
    ngan_sach_id = fields.Many2one(
        'ngan_sach_du_an', string='Ngân Sách', required=True, ondelete='cascade'
    )

    so_tien = fields.Float(
        string='Số Tiền', required=True, tracking=True
    )

    ngay_chi = fields.Date(
        string='Ngày Chi', required=True, default=fields.Date.today
    )

    loai_chi_phi = fields.Selection([
        ('nhan_luc', 'Nhân Lực'),
        ('thiet_bi', 'Thiết Bị'),
        ('van_phong_pham', 'Văn Phòng Phẩm'),
        ('marketing', 'Marketing'),
        ('di_lai', 'Đi Lại'),
        ('khac', 'Khác')
    ], string='Loại Chi Phí', required=True, default='khac')

    mo_ta = fields.Text(string='Mô Tả')

    nguoi_chi = fields.Many2one(
        'nhan_vien', string='Người Chi',
        default=lambda self: self.env.user
    )
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên")
    hoa_don = fields.Binary(string='Hóa Đơn / Chứng Từ')
    hoa_don_filename = fields.Char(string='Tên File')

    trang_thai = fields.Selection([
        ('cho_duyet', 'Chờ Duyệt'),
        ('da_duyet', 'Đã Duyệt'),
        ('tu_choi', 'Từ Chối')
    ], default='cho_duyet', tracking=True)


    ghi_chu_duyet = fields.Text(string='Ghi Chú Duyệt')

    nguoi_duyet = fields.Many2one(
        'res.users', string='Người Duyệt', readonly=True
    )

    ngay_duyet = fields.Date(
        string='Ngày Duyệt', readonly=True
    )

    is_ngan_sach_am = fields.Boolean(
        string='Ngân sách âm',
        compute='_compute_is_ngan_sach_am',
        store=False
    )

    # ================== CONSTRAINS ==================

    @api.depends('ngan_sach_id.trang_thai')
    def _compute_is_ngan_sach_am(self):
        for record in self:
            record.is_ngan_sach_am = (
                record.ngan_sach_id and 
                record.ngan_sach_id.trang_thai == 'cho_duyet_am'
            )

    @api.constrains('so_tien')
    def _check_so_tien(self):
        for record in self:
            if record.so_tien <= 0:
                raise ValidationError("Số tiền chi phí phải lớn hơn 0")

    # ================== CREATE / WRITE ==================

    @api.model
    def create(self, vals):
        ngan_sach = self.env['ngan_sach_du_an'].browse(vals.get('ngan_sach_id'))
        if ngan_sach and ngan_sach.trang_thai == 'hoan_thanh':
            raise UserError("Ngân sách đã hoàn thành, không thể thêm chi phí mới")
        record = super().create(vals)
        record._kiem_tra_ngan_sach()
        return record

    def write(self, vals):
        res = super().write(vals)
        for record in self:
            record._kiem_tra_ngan_sach()
        return res

    # ================== NGHIỆP VỤ ==================

    def _kiem_tra_ngan_sach(self):
        """
        Kiểm tra tổng chi phí đã duyệt
        Nếu vượt ngân sách → chuyển ngân sách sang chờ duyệt âm
        """
        for record in self:
            if not record.ngan_sach_id:
                continue

            tong_chi_da_duyet = sum(
                record.ngan_sach_id.chi_phi_ids
                .filtered(lambda x: x.trang_thai == 'da_duyet')
                .mapped('so_tien')
            )

            if tong_chi_da_duyet > record.ngan_sach_id.so_tien_du_kien:
                record.ngan_sach_id.trang_thai = 'cho_duyet_am'
                record.message_post(
                    body="Ngân sách dự án đã vượt mức cho phép và đang chờ duyệt âm."
                )

    # ================== PHÂN QUYỀN ==================

    def _check_admin_quyen(self):
        if not self.env.user.has_group('quan_ly_du_an.group_admin_du_an'):
            raise UserError("Bạn không có quyền thực hiện thao tác này")

    # ================== ACTIONS ==================

    def action_duyet(self):
        self._check_admin_quyen()
        for record in self:
            record.write({
                'trang_thai': 'da_duyet',
                'nguoi_duyet': self.env.user.id,
                'ngay_duyet': fields.Date.today()
            })

    def action_tu_choi(self):
        self._check_admin_quyen()
        for record in self:
            record.write({
                'trang_thai': 'tu_choi',
                'nguoi_duyet': self.env.user.id,
                'ngay_duyet': fields.Date.today()
            })

    def action_duyet_am(self):
        """
        Admin duyệt cho phép ngân sách âm
        """
        self._check_admin_quyen()
        for record in self:
            if record.ngan_sach_id:
                record.ngan_sach_id.trang_thai = 'dang_am'

            record.message_post(
                body="Ngân sách dự án đã được admin duyệt cho phép âm."
            )

    def _notify_admin_am(self):
        admins = self.env.ref(
            'quan_ly_du_an.group_admin_du_an'
        ).users

        self.message_post(
            body=f"""
            <b>Ngân sách bị âm</b><br/>
            Ngân sách: {self.ten_ngan_sach}<br/>
            Số tiền còn lại: {self.so_tien_con_lai}
            """
        )

        for admin in admins:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=admin.id,
                summary='Duyệt âm ngân sách',
                note=f'Ngân sách {self.ten_ngan_sach} đang bị âm'
            )
