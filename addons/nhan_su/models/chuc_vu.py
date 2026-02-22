from odoo import models, fields, api
class ChucVu(models.Model):
    _name = 'chuc_vu'
    _description = 'Chức vụ của nhân viên'

    ma_chuc_vu = fields.Char("Mã chức vụ")
    # ten_chuc_vu = fields.Char("Tên chức vụ", required=True)
    ten_chuc_vu = fields.Selection(
        selection=[
            ('nhan_vien', 'Nhân viên'),
            ('quan_ly', 'Quản lý'),
        ], 
        string='Chức vụ'
    )
    
    nhan_vien_ids = fields.One2many('nhan_vien', 'chuc_vu_id', string='Danh sách nhân viên')
    def name_get(self):
        result = []
        selection_labels = dict(self.fields_get(allfields=['ten_chuc_vu'])['ten_chuc_vu']['selection'])
        for record in self:
            name = selection_labels.get(record.ten_chuc_vu, record.ten_chuc_vu)
            result.append((record.id, name))
        return result