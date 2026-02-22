from odoo import models, fields

class VanBanDen(models.Model):
    _name = "qlvb.van_ban_den"
    _description = "Văn bản đến"

    so_van_ban = fields.Char(string="Số văn bản", required=True)
    ngay_den = fields.Date(string="Ngày đến")
    trich_yeu = fields.Text(string="Trích yếu")

    nhan_vien_xu_ly_id = fields.Many2one(
        "nhan_vien",
        string="Nhân viên xử lý"
    )

    nhan_vien_ky_id = fields.Many2one(
        "nhan_vien",
        string="Người ký"
    )

    nhan_vien_phoi_hop_ids = fields.Many2many(
        "nhan_vien",
        string="Người phối hợp"
    )
