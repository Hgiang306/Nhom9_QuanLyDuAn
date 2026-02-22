from odoo import models, fields


class NhanVien(models.Model):
    _inherit = "nhan_vien"

    van_ban_den_count = fields.Integer(
        compute="_compute_van_ban_den_count"
    )

    def _compute_van_ban_den_count(self):
        for rec in self:
            rec.van_ban_den_count = self.env[
                "qlvb.van_ban_den"
            ].search_count([
                ("nhan_vien_xu_ly_id", "=", rec.id)
            ])

    def action_open_van_ban_den(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Văn bản đến",
            "res_model": "qlvb.van_ban_den",
            "view_mode": "tree,form",
            "domain": [
                ("nhan_vien_xu_ly_id", "=", self.id)
            ],
            "context": {
                "default_nhan_vien_xu_ly_id": self.id
            }
        }
