from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LichSuLamViec(models.Model):
    _name = 'lich_su_lam_viec'
    _description = 'Lịch sử làm việc'
    _rec_name = 'cong_viec_id'

    cong_viec_id = fields.Many2one('cong_viec', string="Công việc", ondelete='cascade')
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True)
    du_an_id = fields.Many2one('du_an', string="Thuộc dự án", related='cong_viec_id.du_an_id', store=True)
    ma_phong_ban = fields.Many2one('phong_ban', string="Phòng ban")
    ngay_ghi_nhan = fields.Date("Ngày ghi nhận", default=fields.Date.context_today)

    @api.constrains('cong_viec_id')
    def _check_cong_viec(self):
        for record in self:
            if not record.cong_viec_id:
                raise ValidationError("Lịch sử làm việc phải gắn với một công việc cụ thể.")
