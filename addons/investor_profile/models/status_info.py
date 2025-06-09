from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import random
import string

class StatusInfo(models.Model):
    _name = 'status.info'
    _description = 'Investor Status Information'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True, ondelete='cascade')
    so_tk = fields.Char(string="Số TK", readonly=True, copy=False)
    ma_gioi_thieu = fields.Char(string="Mã giới thiệu", readonly=True, copy=False)
    trang_thai_tk_dau_tu = fields.Selection([
        ('da_duyet', 'Đã duyệt'),
        ('cho_duyet', 'Chờ duyệt'),
        ('tu_choi', 'Từ chối')
    ], string="Trạng thái TK đầu tư", default='cho_duyet', required=True)
    ho_so_goc = fields.Selection([
        ('da_nhan', 'Đã nhận'),
        ('chua_nhan', 'Chưa nhận')
    ], string="Hồ sơ gốc", default='chua_nhan', required=True)
    rm_id = fields.Many2one('res.users', string="RM")
    bda_id = fields.Many2one('res.users', string="BDA")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Tạo số tài khoản tự động (format: TK + 8 số ngẫu nhiên)
            if not vals.get('so_tk'):
                while True:
                    so_tk = 'TK' + ''.join(random.choices(string.digits, k=8))
                    if not self.search([('so_tk', '=', so_tk)]):
                        vals['so_tk'] = so_tk
                        break

            # Tạo mã giới thiệu tự động (format: MG + 6 ký tự ngẫu nhiên)
            if not vals.get('ma_gioi_thieu'):
                while True:
                    ma_gioi_thieu = 'MG' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    if not self.search([('ma_gioi_thieu', '=', ma_gioi_thieu)]):
                        vals['ma_gioi_thieu'] = ma_gioi_thieu
                        break

        return super().create(vals_list)

    @api.constrains('partner_id')
    def _check_unique_partner(self):
        for record in self:
            if record.partner_id:
                duplicate = self.search([
                    ('partner_id', '=', record.partner_id.id),
                    ('id', '!=', record.id)
                ])
                if duplicate:
                    raise ValidationError(_('Mỗi đối tác chỉ được có một thông tin trạng thái.'))

    @api.constrains('rm_id', 'bda_id')
    def _check_rm_bda(self):
        for record in self:
            if record.rm_id and record.bda_id and record.rm_id.id == record.bda_id.id:
                raise ValidationError(_('RM và BDA không thể là cùng một người.'))

    @api.constrains('trang_thai_tk_dau_tu', 'ho_so_goc')
    def _check_status_consistency(self):
        for record in self:
            if record.trang_thai_tk_dau_tu == 'da_duyet' and record.ho_so_goc == 'chua_nhan':
                raise ValidationError(_('Không thể duyệt tài khoản khi chưa nhận hồ sơ gốc.'))

    @api.model
    def _check_and_update_ho_so_goc(self, partner_id):
        """Kiểm tra và cập nhật trạng thái hồ sơ gốc dựa trên thông tin đã nhập"""
        status_info = self.search([('partner_id', '=', partner_id)], limit=1)
        if not status_info:
            return

        partner = self.env['res.partner'].browse(partner_id)
        
        # Kiểm tra thông tin cá nhân
        profile = self.env['investor.profile'].search([
            ('partner_id', '=', partner_id),
            ('name', '!=', False),
            ('birth_date', '!=', False),
            ('gender', '!=', False),
            ('nationality', '!=', False),
            ('id_type', '!=', False),
            ('id_number', '!=', False),
            ('id_issue_date', '!=', False),
            ('id_issue_place', '!=', False),
            ('id_front', '!=', False),
            ('id_back', '!=', False)
        ], limit=1)

        # Kiểm tra thông tin tài khoản ngân hàng
        bank_account = self.env['investor.bank.account'].search([
            ('partner_id', '=', partner_id),
            ('bank_name', '!=', False),
            ('account_number', '!=', False),
            ('account_holder', '!=', False),
            ('branch', '!=', False)
        ], limit=1)

        # Kiểm tra thông tin địa chỉ
        address = self.env['investor.address'].search([
            ('partner_id', '=', partner_id),
            ('address_type', 'in', ['permanent', 'current']),
            ('street', '!=', False),
            ('district', '!=', False),
            ('ward', '!=', False),
            ('state_id', '!=', False),
            ('country_id', '!=', False)
        ], limit=1)

        # Nếu tất cả thông tin đã được nhập đầy đủ, cập nhật trạng thái hồ sơ gốc
        if profile and bank_account and address:
            status_info.write({'ho_so_goc': 'da_nhan'})
        else:
            status_info.write({'ho_so_goc': 'chua_nhan'}) 