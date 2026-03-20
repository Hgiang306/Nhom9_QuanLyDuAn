from odoo import models, fields, api


class DuAnExtend(models.Model):
    _inherit = 'du_an'

    cong_viec_ids = fields.One2many('cong_viec', 'du_an_id', string='Công Việc')
    nhat_ky_cong_viec_ids = fields.One2many('nhat_ky_cong_viec', 'du_an_id', string='Nhật Ký Công Việc')
    danh_gia_nhan_vien_ids = fields.One2many('danh_gia_nhan_vien', 'du_an_id', string='Đánh Giá Nhân Viên')
    dashboard_id = fields.Many2one('dashboard', string="Dashboard")

    @api.depends('cong_viec_ids.phan_tram_cong_viec', 'cong_viec_ids.trang_thai')
    def _compute_phan_tram_du_an(self):
        for record in self:
            cong_viec = record.cong_viec_ids
            if cong_viec:
                total_progress = sum(cong_viec.mapped('phan_tram_cong_viec'))
                record.phan_tram_du_an = total_progress / len(cong_viec)
            else:
                record.phan_tram_du_an = 0.0

    def _post_compute_tien_do(self):
        """Gọi sau khi compute để cập nhật trạng thái — tránh side effect trong compute."""
        for record in self:
            avg = record.phan_tram_du_an
            if avg >= 100 and record.tien_do_du_an != 'hoan_thanh':
                record.tien_do_du_an = 'hoan_thanh'
                record.message_post(
                    body="🎉 <b>Chúc mừng!</b> Dự án đã hoàn thành 100% khối lượng công việc.",
                    subtype_xmlid="mail.mt_note"
                )
            elif avg > 0 and record.tien_do_du_an == 'chua_bat_dau':
                record.tien_do_du_an = 'dang_thuc_hien'

    def action_view_task_chart(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Biểu Đồ Công Việc',
            'res_model': 'cong_viec',
            'view_mode': 'graph',
            'domain': [('du_an_id', '=', self.id)],
            'context': {'search_default_group_by_du_an_id': self.id},
            'target': 'current',
        }

    def action_ai_assistant(self):
        for record in self:
            cv_chua_xong = record.cong_viec_ids.filtered(lambda x: x.trang_thai != 'hoan_thanh')
            if cv_chua_xong:
                ds_chi_tiet = []
                for cv in cv_chua_xong:
                    ten_nv = ", ".join(cv.nhan_vien_ids.mapped('name')) or "Chưa giao ai"
                    trang_thai_tv = dict(cv._fields['trang_thai'].selection).get(cv.trang_thai)
                    ds_chi_tiet.append(f"• '{cv.ten_cong_viec}' của {ten_nv} ({trang_thai_tv})")
                noi_dung_cv = "<br/>".join(ds_chi_tiet)
                tra_loi = (f"🤖 <b>AI Trợ Lý Báo Cáo:</b><br/>"
                           f"Dự án <b>{record.ten_du_an}</b> hiện đạt <b>{record.phan_tram_du_an}%</b>.<br/>"
                           f"Các hạng mục chưa xong bao gồm:<br/>{noi_dung_cv}")
            else:
                tra_loi = f"🤖 <b>AI Trợ Lý:</b> Tuyệt vời! Tất cả hạng mục trong dự án <b>{record.ten_du_an}</b> đã hoàn thành 100%."
            record.message_post(body=tra_loi)
