from odoo import api, models, fields
from odoo.exceptions import ValidationError

class NhatKyCongViec(models.Model):
    _name = 'nhat_ky_cong_viec'
    _description = 'Nhật Ký Công Việc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    user_id = fields.Many2one(
        'res.users',
        string='Nhân viên',
        default=lambda self: self.env.user,
        readonly=True
    )
    cong_viec_id = fields.Many2one('cong_viec', string='Công Việc', ondelete='cascade', tracking=True)
    du_an_id = fields.Many2one('du_an', string='Dự Án', related='cong_viec_id.du_an_id', store=True)

    nhan_vien_ids = fields.Many2many('nhan_vien', string='Người Thực Hiện', ondelete='cascade')

    ngay_thuc_hien = fields.Datetime(string='Ngày Thực Hiện', default=fields.Datetime.now, tracking=True)

    giai_doan_id = fields.Many2one('giai_doan_cong_viec', string="Giai Đoạn", related='cong_viec_id.giai_doan_id', store=True)

    muc_do = fields.Float(
        string='Mức Độ Hoàn Thành (%)', 
        digits=(6, 2), 
        default=0.0,
        tracking=True
    )
    
    trang_thai = fields.Selection([
        ('chua_hoan_thanh', 'Chưa Hoàn Thành'),
        ('hoan_thanh', 'Hoàn Thành'),
        ('hoan_thanh_xuat_sac', 'Hoàn Thành Xuất Sắc'),
    ], string='Trạng Thái', default='chua_hoan_thanh', tracking=True)
    
    @api.onchange('cong_viec_id')
    def _onchange_cong_viec_id(self):
        if self.cong_viec_id:
            self.nhan_vien_ids = [(6, 0, self.cong_viec_id.nhan_vien_ids.ids)]
        else:
            self.nhan_vien_ids = [(6, 0, [])]

    @api.onchange('muc_do')
    def _onchange_muc_do(self):
        """ Tự động cập nhật trạng thái dựa trên mức độ hoàn thành """
        for record in self:
            if record.muc_do < 40:
                record.trang_thai = 'chua_hoan_thanh'
            elif 40 <= record.muc_do < 80:
                record.trang_thai = 'hoan_thanh'
            else:
                record.trang_thai = 'hoan_thanh_xuat_sac'

    @api.constrains('muc_do')
    def _check_muc_do(self):
        """ Kiểm tra mức độ hoàn thành phải từ 0 đến 100 """
        for record in self:
            if not (0 <= record.muc_do <= 100):
                raise ValidationError("Mức Độ Hoàn Thành phải nằm trong khoảng từ 0 đến 100.")

    phan_tram_cong_viec = fields.Float(string="Tiến Độ Công Việc", compute="_compute_phan_tram_cong_viec", store=True)

    @api.depends('cong_viec_id', 'cong_viec_id.phan_tram_cong_viec')
    def _compute_phan_tram_cong_viec(self):
        for record in self:
            record.phan_tram_cong_viec = record.cong_viec_id.phan_tram_cong_viec if record.cong_viec_id else 0.0

    @api.constrains('nhan_vien_ids')
    def _check_nhan_vien_nhat_ky(self):
        for record in self:
            if record.du_an_id:
                nhan_vien_du_an_ids = record.du_an_id.nhan_vien_ids.ids
                for nhan_vien in record.nhan_vien_ids:
                    if nhan_vien.id not in nhan_vien_du_an_ids:
                        raise ValidationError(f"Nhân viên {nhan_vien.display_name} không thuộc dự án này.")

    @api.constrains('cong_viec_id')
    def _check_trang_thai_cong_viec(self):
        for record in self:
            if record.cong_viec_id.trang_thai != 'dang_thuc_hien':
                raise ValidationError(
                    "Bạn chỉ có thể cập nhật nhật ký sau khi xác nhận nhận việc."
                )

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if record.cong_viec_id:
            record.cong_viec_id._compute_phan_tram_cong_viec()
            cv = record.cong_viec_id
            if cv.phan_tram_cong_viec >= 100 and cv.trang_thai == 'dang_thuc_hien':
                cv.trang_thai = 'cho_phe_duyet'
            if cv.du_an_id:
                cv.du_an_id._compute_phan_tram_du_an()
                cv.du_an_id._post_compute_tien_do()
        admin_group = self.env.ref('quan_ly_du_an.group_admin_du_an', raise_if_not_found=False)
        if admin_group:
            admins = self.env['res.users'].search([('groups_id', 'in', admin_group.id)])
            record.message_subscribe(partner_ids=admins.mapped('partner_id').ids)
        return record

    def write(self, vals):
        res = super().write(vals)
        if 'muc_do' in vals:
            for record in self:
                if record.cong_viec_id:
                    record.cong_viec_id._compute_phan_tram_cong_viec()
                    cv = record.cong_viec_id
                    if cv.phan_tram_cong_viec >= 100 and cv.trang_thai == 'dang_thuc_hien':
                        cv.trang_thai = 'cho_phe_duyet'
                    if cv.du_an_id:
                        cv.du_an_id._compute_phan_tram_du_an()
                        cv.du_an_id._post_compute_tien_do()
        if 'trang_thai' in vals and vals['trang_thai'] in ('hoan_thanh', 'hoan_thanh_xuat_sac'):
            for record in self:
                record._cap_nhat_lich_su()
        if 'trang_thai' in vals:
            for record in self:
                record.message_post(
                    body=f"Trạng thái công việc đã thay đổi:<br/>"
                         f"<b>{dict(self._fields['trang_thai'].selection).get(record.trang_thai)}</b><br/>"
                         f"Người cập nhật: <b>{self.env.user.name}</b>",
                    subtype_xmlid='mail.mt_comment'
                )
        return res

    def unlink(self):
        cong_viec_ids = self.mapped('cong_viec_id')
        res = super().unlink()
        for cv in cong_viec_ids:
            cv._compute_phan_tram_cong_viec()
            if cv.du_an_id:
                cv.du_an_id._compute_phan_tram_du_an()
                cv.du_an_id._post_compute_tien_do()
        return res

    def _cap_nhat_lich_su(self):
        """Tạo hoặc cập nhật lịch sử làm việc khi nhật ký hoàn thành."""
        self.ensure_one()
        if not self.cong_viec_id:
            return
        for nv in self.nhan_vien_ids:
            lich_su = self.env['lich_su_lam_viec'].search([
                ('cong_viec_id', '=', self.cong_viec_id.id),
                ('nhan_vien_id', '=', nv.id),
            ], limit=1)
            vals = {
                'du_an_id': self.cong_viec_id.du_an_id.id if self.cong_viec_id.du_an_id else False,
                'ngay_ghi_nhan': fields.Date.today(),
            }
            if lich_su:
                lich_su.write(vals)
            else:
                vals.update({
                    'cong_viec_id': self.cong_viec_id.id,
                    'nhan_vien_id': nv.id,
                    'ma_phong_ban': nv.phong_ban_id.id if nv.phong_ban_id else False,
                })
                self.env['lich_su_lam_viec'].create(vals)
