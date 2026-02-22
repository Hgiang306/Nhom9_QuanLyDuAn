from odoo import models, fields, api


class NhanVien(models.Model):
    _name = 'nhan_vien'
    _description = 'Nhân viên'

    name = fields.Char(string='Tên', required=True)
    ma_dinh_danh = fields.Char(string='Mã định danh')
    user_id = fields.Many2one('res.users', string='Tài khoản')


    ngay_sinh = fields.Date(string='Ngày sinh')

    gioi_tinh = fields.Selection(
        [('nam', 'Nam'), ('nu', 'Nữ'), ('khac', 'Khác')],
        string='Giới tính'
    )

    que_quan = fields.Char(string='Quê quán')
    email = fields.Char(string='Email')
    so_dien_thoai = fields.Char(string='Số điện thoại')
    lich_su_lam_viec_ids = fields.One2many('lich_su_lam_viec', inverse_name='nhan_vien_id', string='Danh sách LSLV')
    
    # chuc_vu_ids = fields.One2many('chuc_vu', inverse_name='nhan_vien_id', string='Danh sách CV')
    chuc_vu_id = fields.Many2one('chuc_vu', string='Chức vụ')
    phong_ban_id = fields.Many2one('phong_ban', string='Phòng ban')

    image_1920 = fields.Binary(string='Ảnh nhân viên')
    
    def name_get(self):
        return [
            (r.id, f"{r.ma_dinh_danh} - {r.name}")
            for r in self
        ]