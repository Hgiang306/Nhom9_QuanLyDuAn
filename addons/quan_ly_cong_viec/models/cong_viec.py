from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

class CongViec(models.Model):
    _name = 'cong_viec'
    _description = 'Công Việc Dự Án'
    _rec_name = 'ten_cong_viec'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    ten_cong_viec = fields.Char(string='Tên Công Việc' )
    mo_ta = fields.Text(string='Mô Tả')
    du_an_id = fields.Many2one('du_an', string='Dự Án', required=True, ondelete='cascade')

    nhan_vien_ids = fields.Many2many('nhan_vien', 'cong_viec_nhan_vien_rel', 'cong_viec_id', 'nhan_vien_id', string='Nhân Viên Tham Gia')
    start_date = fields.Date(string='Ngày Bắt Đầu', default=fields.Date.today)
    han_chot = fields.Datetime(string='Hạn Chót')
    giai_doan_id = fields.Many2one('giai_doan_cong_viec', string='Giai Đoạn')
    
    priority = fields.Selection([
        ('low', 'Thấp'),
        ('medium', 'Trung bình'),
        ('high', 'Cao'),
    ], string='Mức độ ưu tiên', default='medium')

    nhat_ky_cong_viec_ids = fields.One2many('nhat_ky_cong_viec', 'cong_viec_id', string='Nhật Ký Công Việc')

    thoi_gian_con_lai = fields.Char(string="Thời Gian Còn Lại", compute="_compute_thoi_gian_con_lai", store=True)
    
    danh_gia_nhan_vien_ids = fields.One2many('danh_gia_nhan_vien', 'cong_viec_id', string='Đánh Giá Nhân Viên')
    
    nhan_vien_display = fields.Char(string="Nhân Viên Tham Gia (Tên + Mã Định Danh)", compute="_compute_nhan_vien_display")

    phan_tram_cong_viec = fields.Float(
        string="Phần Trăm Hoàn Thành", 
        compute="_compute_phan_tram_cong_viec", 
        store=True
    )

    trang_thai = fields.Selection([
        ('cho_xac_nhan', 'Chờ nhân viên xác nhận'),
        ('dang_thuc_hien', 'Đang thực hiện'),
        ('tri_hoan', 'Trì hoãn'),
        ('hoan_thanh', 'Hoàn thành'),
        ('tu_choi', 'Từ chối')
    ], string='Trạng thái', default='cho_xac_nhan', tracking=True)
    
    ly_do = fields.Text(string="Lý do từ chối", help="Lý do từ chối công việc")
    
    @api.depends('nhat_ky_cong_viec_ids.muc_do')
    def _compute_phan_tram_cong_viec(self):
        for record in self:
            if record.nhat_ky_cong_viec_ids:
                total_progress = sum(record.nhat_ky_cong_viec_ids.mapped('muc_do'))
                record.phan_tram_cong_viec = total_progress / len(record.nhat_ky_cong_viec_ids)
            else:
                record.phan_tram_cong_viec = 0.0

            if record.phan_tram_cong_viec >= 100:
                record.trang_thai = 'hoan_thanh'
    
    @api.depends('nhan_vien_ids')
    def _compute_nhan_vien_display(self):
        for record in self:
            record.nhan_vien_display = ', '.join(record.nhan_vien_ids.mapped('display_name'))

    @api.depends('han_chot')
    def _compute_thoi_gian_con_lai(self):
        for record in self:
            if record.han_chot:
                now = datetime.now()
                delta = record.han_chot - now
                if delta.total_seconds() > 0:
                    days = delta.days
                    hours = delta.seconds // 3600
                    record.thoi_gian_con_lai = f"{days} ngày, {hours} giờ"
                else:
                    record.thoi_gian_con_lai = "Hết hạn"
            else:
                record.thoi_gian_con_lai = "Chưa có hạn chót"

    
    @api.onchange('du_an_id')
    def _onchange_du_an_id(self):
        if self.du_an_id:
            self.nhan_vien_ids = [(6, 0, self.du_an_id.nhan_vien_ids.ids)]

            
    @api.constrains('du_an_id')
    def _check_du_an_tien_do(self):
        for record in self:
            if record.du_an_id and record.du_an_id.tien_do_du_an == 'hoan_thanh':
                raise ValidationError("Không thể thêm công việc vào dự án đã hoàn thành.")
    
    

    @api.constrains('nhan_vien_ids')
    def _check_nhan_vien_trong_du_an(self):
        for record in self:
            if record.du_an_id:
                nhan_vien_du_an_ids = record.du_an_id.nhan_vien_ids.ids
                for nhan_vien in record.nhan_vien_ids:
                    if nhan_vien.id not in nhan_vien_du_an_ids:
                        raise ValidationError(f"Nhân viên {nhan_vien.display_name} không thuộc dự án này.")
    @api.model
    def domain_my_cong_viec(self):
        nhan_vien = self.env['nhan_vien'].search(
            [('user_id', '=', self.env.uid)],
            limit=1
        )
        return [('nhan_vien_ids', 'in', nhan_vien.id)]


    @api.model
    def create(self, vals):
        # Tạo bản ghi trước để có ID và dữ liệu Many2many
        record = super(CongViec, self).create(vals)
        # Gọi hàm gửi thông báo
        record._create_activity_for_nhan_vien()
        return record

    def _create_activity_for_nhan_vien(self):
        for record in self:
            for nv in record.nhan_vien_ids:
                if nv.user_id:
                    # 1. Tạo Activity (Hiện ở biểu tượng Đồng hồ phía trên)
                    record.activity_schedule(
                        'mail.mail_activity_data_todo',
                        user_id=nv.user_id.id,
                        summary='Công việc mới: ' + (record.ten_cong_viec or ''),
                        note=f'Bạn được giao việc: {record.ten_cong_viec}. Vui lòng xác nhận.',
                        date_deadline=record.han_chot.date() if record.han_chot else fields.Date.today()
                    )
                    # 2. Gửi Message (Hiện ở khung Chatter dưới Form và gửi Mail nếu có cấu hình)
                    record.message_post(
                        body=f"Hệ thống đã giao việc cho <b>{nv.display_name}</b>.",
                        partner_ids=[nv.user_id.partner_id.id]
                    )

    def action_xac_nhan_nhan_viec(self):
        self.ensure_one()
        nhan_vien = self.env['nhan_vien'].search([('user_id', '=', self.env.uid)], limit=1)
        
        if nhan_vien not in self.nhan_vien_ids:
            raise ValidationError("Bạn không được giao công việc này.")

        self.trang_thai = 'dang_thuc_hien'
        
        # Tự động đóng Activity "Cần làm" khi nhân viên đã bấm xác nhận
        self.activity_feedback(['mail.mail_activity_data_todo'])
        
        self.message_post(body=f"Nhân viên <b>{nhan_vien.display_name}</b> đã xác nhận nhận việc.")

    def action_tu_choi_nhan_viec(self):
        self.ensure_one()
        return {
            'name': 'Lý do từ chối công việc',
            'type': 'ir.actions.act_window',
            'res_model': 'cong_viec.tu_choi.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_cong_viec_id': self.id}
        }
        
    def confirm_tu_choi(self):
        self.ensure_one()
        if self.cong_viec_id:
            # 1. Cập nhật trạng thái
            self.cong_viec_id.write({
                'trang_thai': 'tu_choi',
                'ly_do': self.ly_do,
            })

            # 2. Gửi Activity (Đây là thứ tạo ra số nhảy ở biểu tượng đồng hồ)
            # Gửi cho người tạo ra công việc (thường là Admin)
            self.cong_viec_id.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=self.cong_viec_id.create_uid.id,
                summary='Công việc bị từ chối!',
                note=f'Nhân viên từ chối việc: {self.cong_viec_id.ten_cong_viec}. Lý do: {self.ly_do}',
                date_deadline=fields.Date.today()
            )

            # 3. Gửi Message chuẩn (Để không bị lỗi False tiêu đề)
            self.cong_viec_id.message_post(
                subject="Từ chối công việc: " + self.cong_viec_id.ten_cong_viec,
                body=f"Nhân viên đã từ chối. Lý do: {self.ly_do}",
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )
                    
class CongViecTuChoiWizard(models.TransientModel):
    _name = 'cong_viec.tu_choi.wizard' 
    _description = 'Wizard từ chối công việc'

    cong_viec_id = fields.Many2one('cong_viec', string="Công việc")
    ly_do = fields.Text(string="Lý do từ chối", required=True)

    def confirm_tu_choi(self): 
        if self.cong_viec_id:
            self.cong_viec_id.write({
                'trang_thai': 'tu_choi',
                'ly_do': self.ly_do,
                'phan_tram_cong_viec': 0.0
            })
  
            self.cong_viec_id.message_post(body=f"<b>Đã từ chối công việc.</b> <br/> Lý do: {self.ly_do}")