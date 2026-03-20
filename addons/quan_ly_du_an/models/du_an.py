from odoo import models, fields, api
from datetime import datetime

class DuAn(models.Model):
    _name = 'du_an'
    _description = 'Dự Án'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ten_du_an'

    ten_du_an = fields.Char(string='Tên Dự Án', required=True)
    mo_ta = fields.Text(string='Mô Tả') 
    
    nguoi_phu_trach_id = fields.Many2one('nhan_vien', string='Người Phụ Trách', ondelete='set null')
    
    nhan_vien_ids = fields.Many2many('nhan_vien', 'du_an_nhan_vien_rel', 'du_an_id', 'nhan_vien_id', string='Nhân Viên Tham Gia')

    tai_nguyen_ids = fields.One2many('tai_nguyen', 'du_an_id', string='Danh Sách Tài Nguyên')
    rui_ro_ids = fields.One2many('rui_ro', 'du_an_id', string='Rủi Ro')

    tien_do_du_an = fields.Selection([
        ('chua_bat_dau', 'Chưa Bắt Đầu'),
        ('dang_thuc_hien', 'Đang Thực Hiện'),
        ('hoan_thanh', 'Hoàn Thành'),
        ('tam_dung', 'Tạm Dừng')
    ], string="Trạng Thái Dự Án", default='chua_bat_dau')
    
    phan_tram_du_an = fields.Float(
        string="Tiến Độ Dự Án (%)",
        compute="_compute_phan_tram_du_an",
        store=True,
        default=0.0
    )

    @api.model
    def create(self, vals):
        npt_id = vals.get('nguoi_phu_trach_id')
        if npt_id:
            current_nv_commands = vals.get('nhan_vien_ids', [])
            nv_ids = []
            if current_nv_commands and current_nv_commands[0][0] == 6:
                nv_ids = list(current_nv_commands[0][2])
            if npt_id not in nv_ids:
                nv_ids.append(npt_id)
                vals['nhan_vien_ids'] = [(6, 0, nv_ids)]
        return super(DuAn, self).create(vals)

    def write(self, vals):
        res = super(DuAn, self).write(vals)
        if 'nguoi_phu_trach_id' in vals or 'nhan_vien_ids' in vals:
            for record in self:
                npt = record.nguoi_phu_trach_id
                if npt and npt not in record.nhan_vien_ids:
                    super(DuAn, record).write({'nhan_vien_ids': [(4, npt.id)]})
        return res
            
            
    