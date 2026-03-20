# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RuiRo(models.Model):
    _name = 'rui_ro'
    _description = 'Quản Lý Rủi Ro Dự Án'
    _rec_name = 'ten_rui_ro'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'diem_rui_ro desc, id desc'

    # ── Thông tin cơ bản ──────────────────────────────────────────────────────
    ten_rui_ro = fields.Char(string='Tên Rủi Ro', required=True, tracking=True)
    mo_ta = fields.Text(string='Mô Tả Chi Tiết')
    du_an_id = fields.Many2one('du_an', string='Dự Án', required=True,
                               ondelete='cascade', tracking=True)
    loai_rui_ro = fields.Selection([
        ('ky_thuat',   'Kỹ Thuật'),
        ('tien_do',    'Tiến Độ'),
        ('tai_chinh',  'Tài Chính'),
        ('yeu_cau',    'Yêu Cầu / Phạm Vi'),
        ('nhan_su',    'Nhân Sự'),
        ('khac',       'Khác'),
    ], string='Loại Rủi Ro', required=True, default='ky_thuat', tracking=True)

    nguoi_chiu_trach_nhiem_ids = fields.Many2many(
        'nhan_vien', 'rui_ro_nhan_vien_rel', 'rui_ro_id', 'nhan_vien_id',
        string='Người Chịu Trách Nhiệm',
    )
    nguoi_bao_cao_id = fields.Many2one('res.users', string='Người Báo Cáo',
                                       default=lambda self: self.env.uid)
    ngay_phat_hien = fields.Date(string='Ngày Phát Hiện', default=fields.Date.today)
    han_xu_ly = fields.Date(string='Hạn Xử Lý', tracking=True)
    khac_phuc = fields.Text(string='Giải Pháp Khắc Phục')

    # ── Risk Matrix ───────────────────────────────────────────────────────────
    xac_suat = fields.Selection([
        ('1', '1 - Rất thấp'),
        ('2', '2 - Thấp'),
        ('3', '3 - Trung bình'),
        ('4', '4 - Cao'),
        ('5', '5 - Rất cao'),
    ], string='Xác Suất', required=True, default='2', tracking=True)

    tac_dong = fields.Selection([
        ('1', '1 - Không đáng kể'),
        ('2', '2 - Nhỏ'),
        ('3', '3 - Trung bình'),
        ('4', '4 - Lớn'),
        ('5', '5 - Thảm họa'),
    ], string='Tác Động', required=True, default='2', tracking=True)

    diem_rui_ro = fields.Integer(
        string='Điểm Rủi Ro', compute='_compute_diem_rui_ro', store=True)
    muc_do_rui_ro = fields.Selection([
        ('xanh',  'Thấp (1-9)'),
        ('vang',  'Trung Bình (10-16)'),
        ('do',    'Cao (17-25)'),
    ], string='Mức Độ', compute='_compute_diem_rui_ro', store=True, tracking=True)

    # ── Trạng thái workflow ───────────────────────────────────────────────────
    trang_thai = fields.Selection([
        ('du_bao',      'Dự Báo'),
        ('theo_doi',    'Đang Theo Dõi'),
        ('su_co',       'Đã Xảy Ra'),
        ('da_xu_ly',    'Đã Xử Lý'),
    ], string='Trạng Thái', default='du_bao', required=True, tracking=True)

    # ── Liên kết công việc được tạo từ rủi ro ────────────────────────────────
    cong_viec_id = fields.Many2one('cong_viec', string='Công Việc Xử Lý',
                                   readonly=True, copy=False, ondelete='set null')
    so_luong_nguoi_chiu_trach_nhiem = fields.Integer(
        compute='_compute_so_luong_nguoi_chiu_trach_nhiem', store=True)

    # ── Compute ───────────────────────────────────────────────────────────────
    @api.depends('xac_suat', 'tac_dong')
    def _compute_diem_rui_ro(self):
        for r in self:
            xs = int(r.xac_suat or 0)
            td = int(r.tac_dong or 0)
            diem = xs * td
            r.diem_rui_ro = diem
            if diem >= 17:
                r.muc_do_rui_ro = 'do'
            elif diem >= 10:
                r.muc_do_rui_ro = 'vang'
            else:
                r.muc_do_rui_ro = 'xanh'

    @api.depends('nguoi_chiu_trach_nhiem_ids')
    def _compute_so_luong_nguoi_chiu_trach_nhiem(self):
        for r in self:
            r.so_luong_nguoi_chiu_trach_nhiem = len(r.nguoi_chiu_trach_nhiem_ids)

    @api.onchange('du_an_id')
    def _onchange_du_an_id(self):
        """Tự điền người chịu trách nhiệm từ dự án khi chọn dự án."""
        if self.du_an_id and not self.nguoi_chiu_trach_nhiem_ids:
            nv_ids = self.du_an_id.nhan_vien_ids.ids
            if nv_ids:
                # Dùng [(6,0,ids)] để set Many2many - an toàn trong onchange
                self.nguoi_chiu_trach_nhiem_ids = [(6, 0, nv_ids)]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('du_an_id') and not vals.get('nguoi_chiu_trach_nhiem_ids'):
                nv_ids = self.env['du_an'].browse(vals['du_an_id']).nhan_vien_ids.ids
                if nv_ids:
                    vals['nguoi_chiu_trach_nhiem_ids'] = [(6, 0, nv_ids)]
        return super().create(vals_list)

    # ── Workflow actions ──────────────────────────────────────────────────────
    def action_theo_doi(self):
        self.write({'trang_thai': 'theo_doi'})
        self._gui_canh_bao_noi_bo('🔍 Rủi ro đang được theo dõi chặt chẽ.')

    def action_su_co(self):
        self.write({'trang_thai': 'su_co'})
        self._gui_canh_bao_khan_cap()

    def action_da_xu_ly(self):
        self.write({'trang_thai': 'da_xu_ly'})
        for r in self:
            r.message_post(body='✅ Rủi ro đã được xử lý hoàn toàn.')

    def action_reset_du_bao(self):
        self.write({'trang_thai': 'du_bao'})

    def action_chuyen_thanh_cong_viec(self):
        """Tạo công việc khẩn từ rủi ro đã xảy ra."""
        self.ensure_one()
        if not self.du_an_id:
            raise ValidationError('Rủi ro chưa gắn với dự án nào.')
        if self.cong_viec_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'cong_viec',
                'res_id': self.cong_viec_id.id,
                'view_mode': 'form',
            }
        cong_viec = self.env['cong_viec'].create({
            'ten_cong_viec': f'[RỦI RO] {self.ten_rui_ro}',
            'du_an_id': self.du_an_id.id,
            'mo_ta': f'Xử lý rủi ro: {self.ten_rui_ro}\n\nMô tả: {self.mo_ta or ""}\n\nGiải pháp: {self.khac_phuc or ""}',
            'nhan_vien_ids': [(6, 0, self.nguoi_chiu_trach_nhiem_ids.ids)],
            'han_chot': fields.Datetime.now(),
            'priority': 'high',
        })
        self.cong_viec_id = cong_viec
        self.trang_thai = 'su_co'
        self.message_post(
            body=f'🚨 Đã tạo công việc xử lý: <a href="/web#id={cong_viec.id}&model=cong_viec">{cong_viec.ten_cong_viec}</a>'
        )
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cong_viec',
            'res_id': cong_viec.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ── Thông báo nội bộ ──────────────────────────────────────────────────────
    def _gui_canh_bao_noi_bo(self, note=''):
        for r in self:
            partners = r.nguoi_chiu_trach_nhiem_ids.mapped('user_id.partner_id')
            if r.nguoi_bao_cao_id:
                partners |= r.nguoi_bao_cao_id.partner_id
            # Ghi vào chatter
            r.message_post(
                body=f'{note}<br/>Rủi ro: <b>{r.ten_rui_ro}</b> | Điểm: <b>{r.diem_rui_ro}</b>',
                partner_ids=partners.ids,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
            # Tạo activity để hiện trên chuông 🔔
            note_plain = note.replace('<b>', '').replace('</b>', '')
            for nv in r.nguoi_chiu_trach_nhiem_ids:
                if nv.user_id:
                    r.activity_schedule(
                        'mail.mail_activity_data_todo',
                        user_id=nv.user_id.id,
                        summary=f'Cảnh báo rủi ro: {r.ten_rui_ro}',
                        note=note_plain,
                        date_deadline=fields.Date.today(),
                    )

    def _gui_canh_bao_khan_cap(self):
        for r in self:
            partners = r.nguoi_chiu_trach_nhiem_ids.mapped('user_id.partner_id')
            if r.nguoi_bao_cao_id:
                partners |= r.nguoi_bao_cao_id.partner_id
            # Gửi thêm cho nhóm admin
            admin_group = self.env.ref('quan_ly_du_an.group_admin_du_an', raise_if_not_found=False)
            if admin_group:
                partners |= admin_group.users.mapped('partner_id')
            r.message_post(
                body=(
                    f'🚨 <b>SỰ CỐ XẢY RA!</b><br/>'
                    f'Rủi ro <b>{r.ten_rui_ro}</b> đã trở thành sự cố thực tế.<br/>'
                    f'Dự án: <b>{r.du_an_id.ten_du_an}</b><br/>'
                    f'Điểm rủi ro: <b>{r.diem_rui_ro}/25</b><br/>'
                    f'Giải pháp đề xuất: {r.khac_phuc or "Chưa có"}'
                ),
                partner_ids=partners.ids,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
            # Tạo activity cho người chịu trách nhiệm
            for nv in r.nguoi_chiu_trach_nhiem_ids:
                if nv.user_id:
                    r.activity_schedule(
                        'mail.mail_activity_data_todo',
                        user_id=nv.user_id.id,
                        summary=f'Xử lý sự cố: {r.ten_rui_ro}',
                        note=f'Rủi ro đã xảy ra. Cần xử lý ngay!',
                        date_deadline=fields.Date.today(),
                    )

    # ── CRON: Tự động cảnh báo rủi ro cao ────────────────────────────────────
    @api.model
    def _cron_canh_bao_rui_ro(self):
        """Chạy hàng ngày:
        1. Cảnh báo record rủi ro điểm đỏ / quá hạn (nếu có)
        2. Tự quét dữ liệu thực: công việc quá hạn, dự án chậm, CV bị từ chối
        """
        self._canh_bao_rui_ro_da_tao()
        self._canh_bao_tu_dong_tu_du_lieu()

    @api.model
    def _canh_bao_rui_ro_da_tao(self):
        """Cảnh báo các record rủi ro điểm đỏ hoặc quá hạn xử lý."""
        today = fields.Date.today()

        for r in self.search([('muc_do_rui_ro', '=', 'do'), ('trang_thai', 'in', ['du_bao', 'theo_doi'])]):
            r._gui_canh_bao_noi_bo('⚠️ <b>CẢNH BÁO TỰ ĐỘNG:</b> Rủi ro mức ĐỎ chưa được xử lý!')

        for r in self.search([('han_xu_ly', '<', today), ('trang_thai', '!=', 'da_xu_ly'), ('han_xu_ly', '!=', False)]):
            r._gui_canh_bao_noi_bo(f'⏰ <b>QUÁ HẠN XỬ LÝ!</b> Đã vượt hạn xử lý {today}.')

    @api.model
    def _canh_bao_tu_dong_tu_du_lieu(self):
        """Quét dữ liệu thực, tự TẠO record rủi ro nếu chưa có."""
        from odoo.tools import html_escape
        from datetime import timedelta
        now = fields.Datetime.now()
        today = fields.Date.today()

        def _tao_rui_ro_neu_chua_co(ten, du_an, loai, mo_ta, xac_suat='3', tac_dong='3'):
            """Tạo record rủi ro nếu chưa tồn tại record cùng tên + dự án + chưa xử lý."""
            existing = self.search([
                ('ten_rui_ro', '=', ten),
                ('du_an_id', '=', du_an.id),
                ('trang_thai', '!=', 'da_xu_ly'),
            ], limit=1)
            if existing:
                # Đã có rồi, chỉ cập nhật mô tả
                existing.mo_ta = mo_ta
                return existing
            rr = self.create({
                'ten_rui_ro': ten,
                'du_an_id': du_an.id,
                'loai_rui_ro': loai,
                'mo_ta': mo_ta,
                'xac_suat': xac_suat,
                'tac_dong': tac_dong,
                'trang_thai': 'theo_doi',
            })
            # Gửi thông báo ngay sau khi tạo
            rr._gui_canh_bao_noi_bo('🤖 <b>Rủi ro được phát hiện tự động bởi hệ thống.</b>')
            return rr

        # ── 1. Dự án đang thực hiện nhưng tiến độ < 30% ──────────────────────
        du_an_cham = self.env['du_an'].search([
            ('tien_do_du_an', '=', 'dang_thuc_hien'),
            ('phan_tram_du_an', '<', 30),
        ])
        for da in du_an_cham:
            _tao_rui_ro_neu_chua_co(
                ten=f'[Tự động] Dự án chậm tiến độ: {da.ten_du_an}',
                du_an=da,
                loai='tien_do',
                mo_ta=f'Dự án đang thực hiện nhưng tiến độ chỉ đạt {da.phan_tram_du_an:.0f}%. Cần kiểm tra ngay.',
                xac_suat='4',
                tac_dong='3',
            )

        # ── 2. Ngân sách âm (vượt chi) ───────────────────────────────────────
        ns_am = self.env['ngan_sach_du_an'].search([
            ('trang_thai', 'in', ['cho_duyet_am', 'da_duyet_am']),
        ])
        for ns in ns_am:
            if not ns.du_an_id:
                continue
            _tao_rui_ro_neu_chua_co(
                ten=f'[Tự động] Ngân sách vượt mức: {ns.du_an_id.ten_du_an}',
                du_an=ns.du_an_id,
                loai='tai_chinh',
                mo_ta=f'Ngân sách "{ns.ten_ngan_sach}" đã vượt mức cho phép. Trạng thái: {ns.trang_thai}.',
                xac_suat='4',
                tac_dong='4',
            )

        # ── 3. Công việc quá hạn chưa hoàn thành ─────────────────────────────
        cv_qua_han = self.env['cong_viec'].search([
            ('han_chot', '<', now),
            ('trang_thai', 'not in', ['hoan_thanh', 'tu_choi']),
            ('du_an_id', '!=', False),
        ])
        # Nhóm theo dự án để tránh tạo quá nhiều record
        du_an_co_cv_qua_han = {}
        for cv in cv_qua_han:
            du_an_co_cv_qua_han.setdefault(cv.du_an_id, []).append(cv.ten_cong_viec or '?')

        for da, cv_names in du_an_co_cv_qua_han.items():
            danh_sach = ', '.join(cv_names[:5])
            _tao_rui_ro_neu_chua_co(
                ten=f'[Tự động] Công việc quá hạn: {da.ten_du_an}',
                du_an=da,
                loai='tien_do',
                mo_ta=f'Có {len(cv_names)} công việc quá hạn chưa hoàn thành: {danh_sach}.',
                xac_suat='3',
                tac_dong='3',
            )

        # ── 4. Công việc bị từ chối ───────────────────────────────────────────
        cv_tu_choi = self.env['cong_viec'].search([
            ('trang_thai', '=', 'tu_choi'),
            ('du_an_id', '!=', False),
        ])
        du_an_co_cv_tu_choi = {}
        for cv in cv_tu_choi:
            du_an_co_cv_tu_choi.setdefault(cv.du_an_id, []).append(cv.ten_cong_viec or '?')

        for da, cv_names in du_an_co_cv_tu_choi.items():
            danh_sach = ', '.join(cv_names[:5])
            _tao_rui_ro_neu_chua_co(
                ten=f'[Tự động] Công việc bị từ chối: {da.ten_du_an}',
                du_an=da,
                loai='yeu_cau',
                mo_ta=f'Có {len(cv_names)} công việc bị từ chối: {danh_sach}.',
                xac_suat='3',
                tac_dong='2',
            )
