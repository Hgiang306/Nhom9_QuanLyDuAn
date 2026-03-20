import json
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Dashboard(models.Model):
    _name = 'dashboard'
    _description = 'Thống Kê Tổng Quan'

    name = fields.Char(default='Dashboard', readonly=True)

    so_luong_nhan_vien  = fields.Integer(string="Số lượng nhân viên",   compute="_compute_tong_quan")
    so_luong_du_an      = fields.Integer(string="Số lượng dự án",       compute="_compute_tong_quan")
    so_luong_cong_viec  = fields.Integer(string="Số lượng công việc",   compute="_compute_tong_quan")
    so_luong_danh_gia   = fields.Integer(string="Số lượng đánh giá",    compute="_compute_tong_quan")
    phan_tram_hoan_thanh= fields.Float(  string="Tiến độ TB (%)",       compute="_compute_tong_quan")

    du_an_hoan_thanh    = fields.Integer(string="Dự án hoàn thành",     compute="_compute_tong_quan")
    du_an_dang_thuc_hien= fields.Integer(string="Dự án đang thực hiện", compute="_compute_tong_quan")
    du_an_chua_bat_dau  = fields.Integer(string="Dự án chưa bắt đầu",  compute="_compute_tong_quan")
    du_an_tam_dung      = fields.Integer(string="Dự án tạm dừng",       compute="_compute_tong_quan")

    tong_ngan_sach = fields.Float(string="Tổng Ngân Sách", compute="_compute_tong_quan")
    tong_chi_phi   = fields.Float(string="Tổng Chi Phí",   compute="_compute_tong_quan")

    render_charts    = fields.Html(string="Biểu đồ",         compute="_compute_render_charts")
    danh_sach_nv_ids = fields.Many2many('nhan_vien', string="Nhân viên", compute="_compute_nv")

    du_an_cua_toi  = fields.Html( string="Dự Án Của Tôi",  compute="_compute_du_lieu_ca_nhan")
    rui_ro_cua_toi = fields.Html( string="Rủi Ro Của Tôi", compute="_compute_du_lieu_ca_nhan")
    pie_chart_data = fields.Char( string="Pie Chart Data",  compute="_compute_du_lieu_ca_nhan")

    # ── Nhân viên mới nhất ────────────────────────────────────────────────────
    def _compute_nv(self):
        for record in self:
            record.danh_sach_nv_ids = self.env['nhan_vien'].search([], limit=5)

    # ── Thống kê tổng quan ────────────────────────────────────────────────────
    def _compute_tong_quan(self):
        for record in self:
            try:
                record.so_luong_nhan_vien = self.env['nhan_vien'].search_count([])
            except Exception:
                record.so_luong_nhan_vien = 0
            try:
                record.so_luong_du_an = self.env['du_an'].search_count([])
            except Exception:
                record.so_luong_du_an = 0
            try:
                record.so_luong_cong_viec = self.env['cong_viec'].search_count([])
            except Exception:
                record.so_luong_cong_viec = 0
            try:
                record.so_luong_danh_gia = self.env['danh_gia_nhan_vien'].search_count([])
            except Exception:
                record.so_luong_danh_gia = 0

            try:
                du_an_records = self.env['du_an'].search([])
                record.du_an_hoan_thanh     = sum(1 for d in du_an_records if d.tien_do_du_an == 'hoan_thanh')
                record.du_an_dang_thuc_hien = sum(1 for d in du_an_records if d.tien_do_du_an == 'dang_thuc_hien')
                record.du_an_chua_bat_dau   = sum(1 for d in du_an_records if d.tien_do_du_an == 'chua_bat_dau')
                record.du_an_tam_dung       = sum(1 for d in du_an_records if d.tien_do_du_an == 'tam_dung')
                record.phan_tram_hoan_thanh = (
                    sum(d.phan_tram_du_an for d in du_an_records) / len(du_an_records)
                    if du_an_records else 0.0
                )
            except Exception as e:
                _logger.warning("Dashboard _compute_tong_quan du_an error: %s", e)
                record.du_an_hoan_thanh = record.du_an_dang_thuc_hien = 0
                record.du_an_chua_bat_dau = record.du_an_tam_dung = 0
                record.phan_tram_hoan_thanh = 0.0

            try:
                ns = self.env['ngan_sach_du_an'].search([])
                record.tong_ngan_sach = sum(ns.mapped('so_tien_du_kien'))
                record.tong_chi_phi   = sum(ns.mapped('so_tien_da_chi'))
            except Exception:
                record.tong_ngan_sach = 0.0
                record.tong_chi_phi   = 0.0

    # ── Dữ liệu cá nhân ──────────────────────────────────────────────────────
    def _compute_du_lieu_ca_nhan(self):
        for record in self:
            try:
                user = self.env.user
                nv = self.env['nhan_vien'].search([('user_id', '=', user.id)], limit=1)

                # Dự án của tôi
                du_ans = (
                    self.env['du_an'].search([('nhan_vien_ids', 'in', nv.id)])
                    if nv else self.env['du_an'].search([])
                )
                trang_thai_label = {
                    'chua_bat_dau':   ('Chưa bắt đầu',   '#94a3b8'),
                    'dang_thuc_hien': ('Đang thực hiện',  '#6366f1'),
                    'hoan_thanh':     ('Hoàn thành',      '#22c55e'),
                    'tam_dung':       ('Tạm dừng',        '#f59e0b'),
                }
                rows = ''
                for da in du_ans[:6]:
                    label, color = trang_thai_label.get(da.tien_do_du_an, ('Không rõ', '#94a3b8'))
                    pct = da.phan_tram_du_an or 0
                    rows += (
                        f'<div style="padding:8px 0;border-bottom:1px solid #f1f5f9;">'
                        f'<div style="display:flex;justify-content:space-between;margin-bottom:4px;">'
                        f'<span style="font-weight:600;font-size:13px;color:#1e293b;">{da.ten_du_an}</span>'
                        f'<span style="font-size:11px;padding:2px 8px;border-radius:20px;'
                        f'background:{color}20;color:{color};font-weight:600;">{label}</span></div>'
                        f'<div style="background:#f1f5f9;border-radius:4px;height:6px;">'
                        f'<div style="background:{color};width:{pct:.0f}%;height:6px;border-radius:4px;"></div></div>'
                        f'<div style="font-size:11px;color:#94a3b8;margin-top:2px;">{pct:.0f}% hoàn thành</div></div>'
                    )
                record.du_an_cua_toi = rows or '<div style="color:#94a3b8;text-align:center;padding:20px;">Không có dự án nào</div>'
            except Exception as e:
                _logger.warning("Dashboard du_an_cua_toi error: %s", e)
                record.du_an_cua_toi = '<div style="color:#94a3b8;text-align:center;padding:20px;">Không có dữ liệu</div>'

            try:
                nv = self.env['nhan_vien'].search([('user_id', '=', self.env.user.id)], limit=1)
                rui_ros = (
                    self.env['rui_ro'].search([
                        ('nguoi_chiu_trach_nhiem_ids', 'in', nv.id),
                        ('trang_thai', '!=', 'da_xu_ly'),
                    ], limit=6)
                    if nv else self.env['rui_ro'].search([('trang_thai', '!=', 'da_xu_ly')], limit=6)
                )
                muc_do_cfg = {
                    'do':   ('🔴 Cao',        '#ef4444'),
                    'vang': ('🟡 Trung bình', '#f59e0b'),
                    'xanh': ('🟢 Thấp',       '#22c55e'),
                }
                rr_rows = ''
                for rr in rui_ros:
                    label, color = muc_do_cfg.get(rr.muc_do_rui_ro, ('', '#94a3b8'))
                    rr_rows += (
                        f'<div style="padding:8px 0;border-bottom:1px solid #f1f5f9;">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                        f'<span style="font-weight:600;font-size:13px;color:#1e293b;">{rr.ten_rui_ro}</span>'
                        f'<span style="font-size:11px;font-weight:700;color:{color};">{label}</span></div>'
                        f'<div style="font-size:11px;color:#64748b;margin-top:2px;">'
                        f'📁 {rr.du_an_id.ten_du_an} &nbsp;|&nbsp; Điểm: <b>{rr.diem_rui_ro}/25</b></div></div>'
                    )
                record.rui_ro_cua_toi = rr_rows or '<div style="color:#22c55e;text-align:center;padding:20px;">✅ Không có rủi ro nào!</div>'
            except Exception as e:
                _logger.warning("Dashboard rui_ro_cua_toi error: %s", e)
                record.rui_ro_cua_toi = '<div style="color:#94a3b8;text-align:center;padding:20px;">Không có dữ liệu</div>'

            try:
                nv = self.env['nhan_vien'].search([('user_id', '=', self.env.user.id)], limit=1)
                CV = self.env['cong_viec']
                base = [('nhan_vien_ids', 'in', nv.id)] if nv else []
                pie_data = {
                    'labels': ['Chờ xác nhận', 'Đang thực hiện', 'Chờ phê duyệt', 'Hoàn thành', 'Từ chối'],
                    'data': [
                        CV.search_count(base + [('trang_thai', '=', 'cho_xac_nhan')]),
                        CV.search_count(base + [('trang_thai', '=', 'dang_thuc_hien')]),
                        CV.search_count(base + [('trang_thai', '=', 'cho_phe_duyet')]),
                        CV.search_count(base + [('trang_thai', '=', 'hoan_thanh')]),
                        CV.search_count(base + [('trang_thai', '=', 'tu_choi')]),
                    ],
                    'colors': ['#94a3b8', '#6366f1', '#f59e0b', '#22c55e', '#ef4444'],
                }
                record.pie_chart_data = json.dumps(pie_data)
            except Exception as e:
                _logger.warning("Dashboard pie_chart_data error: %s", e)
                record.pie_chart_data = '{}'

    # ── Render chart template ─────────────────────────────────────────────────
    def _compute_render_charts(self):
        for record in self:
            try:
                record.render_charts = self.env['ir.qweb']._render(
                    'quan_ly_cong_viec.dashboard_du_an_template'
                )
            except Exception:
                record.render_charts = ''

    # ── Khởi tạo record mặc định ──────────────────────────────────────────────
    def init(self):
        super().init()
        if not self.search([], limit=1):
            self.with_context(no_recompute=True).create({'name': 'Dashboard'})

    # ── RPC methods ───────────────────────────────────────────────────────────
    @api.model
    def get_project_progress_stats(self):
        try:
            du_ans = self.env['du_an'].search([])
            return {
                'labels':   [p.ten_du_an for p in du_ans],
                'progress': [p.phan_tram_du_an for p in du_ans],
                'colors':   ['#5b9bd5'] * len(du_ans),
            }
        except Exception as e:
            _logger.warning("get_project_progress_stats error: %s", e)
            return {'labels': [], 'progress': [], 'colors': []}

    @api.model
    def get_dashboard_data(self):
        dashboard = self.search([], limit=1)
        if not dashboard:
            dashboard = self.create({'name': 'Dashboard'})
        return dashboard.id

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        return res

    @api.model
    def action_open_dashboard(self):
        """Trả về action với đúng res_id."""
        dashboard = self.search([], limit=1)
        if not dashboard:
            dashboard = self.create({'name': 'Dashboard'})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dashboard',
            'res_model': 'dashboard',
            'view_mode': 'form',
            'res_id': dashboard.id,
            'target': 'current',
            'context': {'form_view_initial_mode': 'readonly'},
        }

    # ── Button actions ────────────────────────────────────────────────────────
    def action_open_nhan_vien(self):
        return self.env['ir.actions.act_window']._for_xml_id('nhan_su.action_nhan_vien')

    def action_open_du_an(self):
        return self.env['ir.actions.act_window']._for_xml_id('quan_ly_du_an.action_du_an')

    def action_open_cong_viec(self):
        return self.env['ir.actions.act_window']._for_xml_id('quan_ly_cong_viec.action_cong_viec')

    def action_open_danh_gia(self):
        return self.env['ir.actions.act_window']._for_xml_id('quan_ly_cong_viec.action_danh_gia_nhan_vien')
