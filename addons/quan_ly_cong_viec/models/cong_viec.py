from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError


class CongViec(models.Model):
    _name = 'cong_viec'
    _description = 'Công Việc Dự Án'
    _rec_name = 'ten_cong_viec'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    ten_cong_viec = fields.Char(string='Tên Công Việc')
    mo_ta = fields.Text(string='Mô Tả')
    du_an_id = fields.Many2one('du_an', string='Dự Án', required=True, ondelete='cascade')
    nhan_vien_ids = fields.Many2many(
        'nhan_vien', 'cong_viec_nhan_vien_rel', 'cong_viec_id', 'nhan_vien_id',
        string='Nhân Viên Tham Gia'
    )
    start_date = fields.Date(string='Ngày Bắt Đầu', default=fields.Date.today)
    han_chot = fields.Datetime(string='Hạn Chót')
    giai_doan_id = fields.Many2one('giai_doan_cong_viec', string='Giai Đoạn')
    priority = fields.Selection([
        ('low', 'Thấp'),
        ('medium', 'Trung bình'),
        ('high', 'Cao'),
    ], string='Mức độ ưu tiên', default='medium')
    nhat_ky_cong_viec_ids = fields.One2many('nhat_ky_cong_viec', 'cong_viec_id', string='Nhật Ký Công Việc')
    thoi_gian_con_lai = fields.Char(string="Thời Gian Còn Lại", compute="_compute_thoi_gian_con_lai", store=True)
    danh_gia_nhan_vien_ids = fields.One2many('danh_gia_nhan_vien', 'cong_viec_id', string='Đánh Giá Nhân Viên')
    nhan_vien_display = fields.Char(string="Danh sách nhân viên", compute="_compute_nhan_vien_display")

    # Google Calendar / Lịch Odoo
    sync_to_google_calendar = fields.Boolean(string="Đồng bộ với Google Calendar", default=False)
    google_calendar_event_id = fields.Char(string="Google Calendar Event ID", readonly=True, copy=False)
    last_sync_date = fields.Datetime(string="Lần đồng bộ cuối", readonly=True)
    calendar_event_id = fields.Many2one('calendar.event', string='Sự kiện lịch', readonly=True, copy=False)

    phan_tram_cong_viec = fields.Float(
        string="Phần Trăm Hoàn Thành",
        compute="_compute_phan_tram_cong_viec",
        store=True
    )
    trang_thai = fields.Selection([
        ('cho_xac_nhan', 'Chờ nhân viên xác nhận'),
        ('dang_thuc_hien', 'Đang thực hiện'),
        ('tri_hoan', 'Trì hoãn'),
        ('cho_phe_duyet', 'Chờ phê duyệt'),
        ('hoan_thanh', 'Hoàn thành'),
        ('tu_choi', 'Từ chối'),
    ], string='Trạng thái', default='cho_xac_nhan', tracking=True)
    ly_do = fields.Text(string="Lý do từ chối")
    color = fields.Integer(string='Màu', default=0)
    giai_doan_ca_nhan_id = fields.Many2one(
        'giai_doan_ca_nhan', string='Giai Đoạn Cá Nhân',
        domain="[('user_id', '=', uid)]",
        index=True,
        group_expand='_group_expand_giai_doan_ca_nhan',
        default=lambda self: self.env['giai_doan_ca_nhan']._get_or_create_default_stages()[:1],
    )

    # -------------------------------------------------------------------------
    # Compute
    # -------------------------------------------------------------------------
    @api.depends('nhat_ky_cong_viec_ids.muc_do')
    def _compute_phan_tram_cong_viec(self):
        for record in self:
            if record.nhat_ky_cong_viec_ids:
                total = sum(record.nhat_ky_cong_viec_ids.mapped('muc_do'))
                record.phan_tram_cong_viec = total / len(record.nhat_ky_cong_viec_ids)
            else:
                record.phan_tram_cong_viec = 0.0

    @api.depends('nhan_vien_ids')
    def _compute_nhan_vien_display(self):
        for record in self:
            record.nhan_vien_display = ', '.join(record.nhan_vien_ids.mapped('display_name'))

    @api.depends('han_chot')
    def _compute_thoi_gian_con_lai(self):
        for record in self:
            if record.han_chot:
                delta = record.han_chot - datetime.now()
                if delta.total_seconds() > 0:
                    record.thoi_gian_con_lai = f"{delta.days} ngày, {delta.seconds // 3600} giờ"
                else:
                    record.thoi_gian_con_lai = "Hết hạn"
            else:
                record.thoi_gian_con_lai = "Chưa có hạn chót"

    # -------------------------------------------------------------------------
    # Onchange / Constrains
    # -------------------------------------------------------------------------
    # Không dùng @api.onchange với Many2many - gây lỗi _unknown trong Odoo 15

    @api.constrains('du_an_id')
    def _check_du_an_tien_do(self):
        for record in self:
            if record.du_an_id and record.du_an_id.tien_do_du_an == 'hoan_thanh':
                raise ValidationError("Không thể thêm công việc vào dự án đã hoàn thành.")

    @api.constrains('nhan_vien_ids')
    def _check_nhan_vien_trong_du_an(self):
        for record in self:
            if record.du_an_id:
                nhan_vien_du_an_ids = record.du_an_id.nhan_vien_ids.ids
                for nv in record.nhan_vien_ids:
                    if nv.id not in nhan_vien_du_an_ids:
                        raise ValidationError(f"Nhân viên {nv.display_name} không thuộc dự án này.")

    @api.model
    def domain_my_cong_viec(self):
        nhan_vien = self.env['nhan_vien'].search([('user_id', '=', self.env.uid)], limit=1)
        return [('nhan_vien_ids', 'in', nhan_vien.id)]

    @api.model
    def _group_expand_giai_doan_ca_nhan(self, stages, domain, order):
        """Luôn hiện đủ các cột giai đoạn cá nhân của user trong kanban."""
        return self.env['giai_doan_ca_nhan']._get_or_create_default_stages()

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """Tự tạo giai đoạn cá nhân khi user mở kanban group by giai_doan_ca_nhan_id."""
        if groupby and groupby[0] == 'giai_doan_ca_nhan_id':
            stages = self.env['giai_doan_ca_nhan']._get_or_create_default_stages()
            # Gán Inbox cho các công việc chưa có giai đoạn
            inbox = stages.filtered(lambda s: s.ten_giai_doan == 'Inbox')[:1]
            if inbox:
                no_stage = self.search(domain + [('giai_doan_ca_nhan_id', '=', False)])
                if no_stage:
                    no_stage.write({'giai_doan_ca_nhan_id': inbox.id})
        return super().read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        # Đảm bảo user hiện tại có các giai đoạn cá nhân mặc định
        self.env['giai_doan_ca_nhan']._get_or_create_default_stages()
        records = super().create(vals_list)
        for record in records:
            for nv in record.nhan_vien_ids:
                if nv.user_id:
                    record.activity_schedule(
                        'mail.mail_activity_data_todo',
                        user_id=nv.user_id.id,
                        summary='Công việc mới: ' + (record.ten_cong_viec or ''),
                        note=f'Bạn được giao việc: {record.ten_cong_viec}. Vui lòng xác nhận.',
                        date_deadline=record.han_chot.date() if record.han_chot else fields.Date.today(),
                    )
                    record.message_post(
                        body=f"Hệ thống đã giao việc cho <b>{nv.display_name}</b>.",
                        partner_ids=[nv.user_id.partner_id.id],
                    )
        return records

    def write(self, vals):
        # Ghi nhận trạng thái toggle trước khi write
        sync_toggled_on = vals.get('sync_to_google_calendar') is True
        prev_sync = {r.id: r.sync_to_google_calendar for r in self} if sync_toggled_on else {}

        result = super().write(vals)

        # Nếu toggle vừa bật (False -> True): tạo/cập nhật calendar.event ngay
        if sync_toggled_on:
            for record in self:
                if not prev_sync.get(record.id):  # trước đó đang tắt
                    record.action_sync_calendar()

        # Nếu đang bật sync và có thay đổi dữ liệu liên quan: cập nhật event
        elif sync_fields := {'ten_cong_viec', 'mo_ta', 'han_chot', 'start_date', 'nhan_vien_ids'} & set(vals):
            for record in self:
                if record.sync_to_google_calendar and record.calendar_event_id:
                    record._update_calendar_event()

        return result

    # -------------------------------------------------------------------------
    # Sync lịch
    # -------------------------------------------------------------------------
    def _update_calendar_event(self):
        """Cập nhật calendar.event hiện có theo dữ liệu công việc."""
        self.ensure_one()
        if not self.han_chot or not self.calendar_event_id:
            return
        partner_ids = self.nhan_vien_ids.mapped('user_id.partner_id').ids
        self.calendar_event_id.write({
            'name': self.ten_cong_viec or 'Công việc',
            'start': self.han_chot,
            'stop': self.han_chot,
            'description': self.mo_ta or '',
            'partner_ids': [(6, 0, partner_ids)],
        })
        self.last_sync_date = fields.Datetime.now()

    def action_sync_calendar(self):
        """Tạo hoặc cập nhật calendar.event. Odoo tự sync lên Google Calendar."""
        for record in self:
            if not record.han_chot:
                record.message_post(body="⚠️ Công việc chưa có hạn chót, không thể tạo sự kiện lịch.")
                continue
            partner_ids = record.nhan_vien_ids.mapped('user_id.partner_id').ids
            if record.calendar_event_id:
                record._update_calendar_event()
                record.message_post(body="📅 Đã cập nhật sự kiện lịch.")
            else:
                event = self.env['calendar.event'].create({
                    'name': record.ten_cong_viec or 'Công việc',
                    'start': record.han_chot,
                    'stop': record.han_chot,
                    'description': record.mo_ta or '',
                    'partner_ids': [(6, 0, partner_ids)],
                })
                record.calendar_event_id = event
                record.last_sync_date = fields.Datetime.now()
                record.message_post(body="📅 Đã tạo sự kiện lịch. Odoo sẽ tự đồng bộ lên Google Calendar.")

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------
    def action_xac_nhan_nhan_viec(self):
        self.ensure_one()
        nhan_vien = self.env['nhan_vien'].search([('user_id', '=', self.env.uid)], limit=1)
        if nhan_vien not in self.nhan_vien_ids:
            raise ValidationError("Bạn không được giao công việc này.")
        self.trang_thai = 'dang_thuc_hien'
        self.activity_feedback(['mail.mail_activity_data_todo'])
        self.message_post(body=f"Nhân viên <b>{nhan_vien.display_name}</b> đã xác nhận nhận việc.")
        for nv in self.nhan_vien_ids:
            existing = self.env['lich_su_lam_viec'].search([
                ('cong_viec_id', '=', self.id),
                ('nhan_vien_id', '=', nv.id),
            ], limit=1)
            if not existing:
                self.env['lich_su_lam_viec'].create({
                    'cong_viec_id': self.id,
                    'nhan_vien_id': nv.id,
                    'ma_phong_ban': nv.phong_ban_id.id if nv.phong_ban_id else False,
                    'ngay_ghi_nhan': fields.Date.today(),
                })

    def action_tu_choi_nhan_viec(self):
        self.ensure_one()
        return {
            'name': 'Lý do từ chối công việc',
            'type': 'ir.actions.act_window',
            'res_model': 'cong_viec.tu_choi.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_cong_viec_id': self.id},
        }

    def action_gui_duyet(self):
        """Nhân viên gửi yêu cầu phê duyệt hoàn thành."""
        self.ensure_one()
        nhan_vien = self.env['nhan_vien'].search([('user_id', '=', self.env.uid)], limit=1)
        if nhan_vien not in self.nhan_vien_ids:
            raise ValidationError("Bạn không được giao công việc này.")
        if self.trang_thai != 'dang_thuc_hien':
            raise ValidationError("Chỉ có thể gửi duyệt khi công việc đang thực hiện.")
        self.trang_thai = 'cho_phe_duyet'
        # Gửi activity cho admin/manager
        managers = self.env.ref('quan_ly_du_an.group_admin_du_an').users
        for manager in managers:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=manager.id,
                summary=f'Cần phê duyệt: {self.ten_cong_viec}',
                note=f'Nhân viên <b>{nhan_vien.display_name}</b> đã hoàn thành và gửi yêu cầu phê duyệt.',
                date_deadline=fields.Date.today(),
            )
        self.message_post(body=f"📤 <b>{nhan_vien.display_name}</b> đã gửi yêu cầu phê duyệt hoàn thành.")

    def action_phe_duyet(self):
        """Manager phê duyệt - chuyển sang Hoàn thành."""
        self.ensure_one()
        if not self.env.user.has_group('quan_ly_du_an.group_admin_du_an'):
            raise ValidationError("Chỉ Manager mới có quyền phê duyệt.")
        if self.trang_thai != 'cho_phe_duyet':
            raise ValidationError("Công việc chưa được gửi duyệt.")
        self.trang_thai = 'hoan_thanh'
        self.activity_feedback(['mail.mail_activity_data_todo'])
        self.message_post(body=f"✅ Công việc đã được <b>{self.env.user.name}</b> phê duyệt hoàn thành.")


class CongViecTuChoiWizard(models.TransientModel):
    _name = 'cong_viec.tu_choi.wizard'
    _description = 'Wizard từ chối công việc'

    cong_viec_id = fields.Many2one('cong_viec', string="Công việc")
    ly_do = fields.Text(string="Lý do từ chối", required=True)

    def confirm_tu_choi(self):
        if self.cong_viec_id:
            self.cong_viec_id.write({
                'trang_thai': 'tu_choi',
                'ly_do': self.ly_do,
            })
            self.cong_viec_id.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=self.cong_viec_id.create_uid.id,
                summary='Công việc bị từ chối!',
                note=f'Nhân viên từ chối việc: {self.cong_viec_id.ten_cong_viec}. Lý do: {self.ly_do}',
                date_deadline=fields.Date.today(),
            )
            self.cong_viec_id.message_post(
                subject="Từ chối công việc: " + self.cong_viec_id.ten_cong_viec,
                body=f"Nhân viên đã từ chối. Lý do: {self.ly_do}",
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
