from odoo import models, fields, api
class ChucVu(models.Model):
    _name = 'phong_ban'
    _description = 'Phòng ban của nhân viên'
    _rec_name = 'ten_phong_ban' 

    ma_phong_ban = fields.Char("Mã phòng ban", required=True) 
    ten_phong_ban = fields.Char("Tên phòng ban", required=True)

    nhan_vien_ids = fields.One2many('nhan_vien', 'phong_ban_id', string="Danh sách nhân viên")

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.ma_phong_ban}] {record.ten_phong_ban}" if record.ma_phong_ban else record.ten_phong_ban
            result.append((record.id, name))
        return result