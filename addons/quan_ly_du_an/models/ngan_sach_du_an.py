from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class NganSachDuAn(models.Model):
    _name = 'ngan_sach_du_an'
    _description = 'Ngân Sách Dự Án'
    _rec_name = 'ten_ngan_sach'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ================= FIELDS =================

    ten_ngan_sach = fields.Char(required=True)
    du_an_id = fields.Many2one('du_an', required=True, ondelete='cascade')

    so_tien_du_kien = fields.Float(required=True, tracking=True)
    so_tien_da_chi = fields.Float(
        compute='_compute_so_tien_da_chi',
        store=True
    )
    so_tien_con_lai = fields.Float(
        compute='_compute_so_tien_con_lai',
        store=True
    )
    phan_tram_su_dung = fields.Float(
        compute='_compute_phan_tram_su_dung',
        store=True
    )

    loai_ngan_sach = fields.Selection([
        ('nhan_luc', 'Nhân Lực'),
        ('thiet_bi', 'Thiết Bị'),
        ('van_phong_pham', 'Văn Phòng Phẩm'),
        ('marketing', 'Marketing'),
        ('khac', 'Khác')
    ], default='khac', required=True)

    mo_ta = fields.Text()
    ngay_tao = fields.Date(default=fields.Date.today)

    trang_thai = fields.Selection([
        ('du_kien', 'Dự Kiến'),
        ('dang_su_dung', 'Đang Sử Dụng'),
        ('cho_duyet_am', 'Chờ Duyệt Âm'),
        ('da_duyet_am', 'Đã Duyệt Âm'),
        ('hoan_thanh', 'Hoàn Thành')
    ], default='dang_su_dung', tracking=True)

    chi_phi_ids = fields.One2many(
        'chi_phi_du_an',
        'ngan_sach_id'
    )

    ly_do_am = fields.Text()
    nguoi_duyet_id = fields.Many2one(
        'res.users',
        readonly=True
    )
    ngay_duyet = fields.Datetime(readonly=True)

    # ================= COMPUTE =================

    @api.depends('chi_phi_ids.so_tien', 'chi_phi_ids.trang_thai')
    def _compute_so_tien_da_chi(self):
        for r in self:
            r.so_tien_da_chi = sum(
                r.chi_phi_ids.filtered(
                    lambda x: x.trang_thai == 'da_duyet'
                ).mapped('so_tien')
            )

    @api.depends('so_tien_du_kien', 'so_tien_da_chi')
    def _compute_so_tien_con_lai(self):
        for r in self:
            r.so_tien_con_lai = r.so_tien_du_kien - r.so_tien_da_chi

    @api.depends('so_tien_du_kien', 'so_tien_da_chi')
    def _compute_phan_tram_su_dung(self):
        for r in self:
            r.phan_tram_su_dung = (
                (r.so_tien_da_chi / r.so_tien_du_kien) * 100
                if r.so_tien_du_kien else 0
            )

    # ================= CONSTRAINS =================

    @api.constrains('so_tien_du_kien')
    def _check_so_tien(self):
        for r in self:
            if r.so_tien_du_kien <= 0:
                raise ValidationError("Ngân sách phải > 0")

    # ================= ACTIONS =================

    def action_hoan_thanh(self):
        for r in self:
            if r.so_tien_con_lai < 0:
                if r.trang_thai != 'cho_duyet_am':
                    r.trang_thai = 'cho_duyet_am'
                    r._notify_admin_am()
            else:
                r.trang_thai = 'hoan_thanh'
            
    def action_duyet_am_ngan_sach(self):
        self.ensure_one()
        if not self.env.user.has_group(
            'quan_ly_du_an.group_admin_du_an'
        ):
            raise UserError("Bạn không có quyền duyệt âm ngân sách")

        self.write({
            'trang_thai': 'da_duyet_am',
            'nguoi_duyet_id': self.env.user.id,
            'ngay_duyet': fields.Datetime.now()
        })
    # ================= NOTIFY =================

    def _notify_admin_am(self):
        template = self.env.ref(
            'quan_ly_du_an.mail_template_am_ngan_sach',
            raise_if_not_found=False
        )

        # In-app notification + activity
        admins = self.env.ref(
            'quan_ly_du_an.group_admin_du_an'
        ).users

        self.message_post(
            body=f"""
            <b>Ngân sách bị âm</b><br/>
            Ngân sách: {self.ten_ngan_sach}<br/>
            Số tiền còn lại: {self.so_tien_con_lai}
            """,
            subtype_xmlid="mail.mt_comment"
        )

        for admin in admins:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=admin.id,
                summary='Duyệt âm ngân sách',
                note=f'Ngân sách {self.ten_ngan_sach} đang bị âm'
            )

        # GỬI EMAIL
        if template:
            template.send_mail(self.id, force_send=True)
