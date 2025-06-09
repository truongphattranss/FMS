from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re

class InvestorProfile(models.Model):
    _name = 'investor.profile'
    _description = 'Personal Information'
    _rec_name = 'name'

    name = fields.Char(string='Họ và tên', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, ondelete='cascade')
    birth_date = fields.Date(string='Ngày sinh', required=True)
    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác')
    ], string='Giới tính', required=True)
    nationality = fields.Many2one('res.country', string='Quốc tịch', required=True)
    id_type = fields.Selection([
        ('id_card', 'CMND/CCCD'),
        ('passport', 'Hộ chiếu'),
        ('other', 'Khác')
    ], string='Loại giấy tờ', required=True)
    id_number = fields.Char(string='Số giấy tờ', required=True)
    id_issue_date = fields.Date(string='Ngày cấp', required=True)
    id_issue_place = fields.Char(string='Nơi cấp', required=True)
    id_front = fields.Binary(string='ID Front:', attachment=True)
    id_front_filename = fields.Char(string='ID Mặt Trước Filename')
    id_back = fields.Binary(string='ID Back:', attachment=True)
    id_back_filename = fields.Char(string='ID Mặt Sau Filename')
    phone = fields.Char(string='Phone Number:')
    email = fields.Char(string='Email:')

    # Bank account information
    bank_account_ids = fields.One2many('investor.bank.account', 'investor_id', string='Tài khoản ngân hàng')

    # Address information
    address_ids = fields.One2many('investor.address', 'investor_id', string='Địa chỉ')

    # Status information
    status_info_ids = fields.One2many('status.info', 'partner_id', string='Thông tin trạng thái')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.name = self.partner_id.name
            self.phone = self.partner_id.phone
            self.email = self.partner_id.email

    @api.constrains('phone')
    def _check_phone(self):
        for record in self:
            if record.phone:
                if not re.match(r'^\+?[0-9]{10,15}$', record.phone):
                    raise ValidationError(_('Số điện thoại không hợp lệ. Vui lòng nhập số điện thoại có 10-15 chữ số.'))

    @api.constrains('email')
    def _check_email(self):
        for record in self:
            if record.email:
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', record.email):
                    raise ValidationError(_('Email không hợp lệ.'))

    @api.constrains('birth_date')
    def _check_birth_date(self):
        for record in self:
            if record.birth_date:
                if record.birth_date > fields.Date.today():
                    raise ValidationError(_('Ngày sinh không thể lớn hơn ngày hiện tại.'))

    @api.constrains('id_number')
    def _check_id_number(self):
        for record in self:
            if record.id_type == 'id_card' and record.id_number:
                if not re.match(r'^[0-9]{9,12}$', record.id_number):
                    raise ValidationError(_('Số CMND/CCCD không hợp lệ. Vui lòng nhập 9-12 chữ số.'))
            elif record.id_type == 'passport' and record.id_number:
                if not re.match(r'^[A-Z][0-9]{7}$', record.id_number):
                    raise ValidationError(_('Số hộ chiếu không hợp lệ. Vui lòng nhập theo định dạng: 1 chữ cái in hoa + 7 chữ số.'))

    @api.constrains('id_issue_date')
    def _check_id_issue_date(self):
        for record in self:
            if record.id_issue_date:
                if record.id_issue_date > fields.Date.today():
                    raise ValidationError(_('Ngày cấp không thể lớn hơn ngày hiện tại.'))
                if record.birth_date and record.id_issue_date < record.birth_date:
                    raise ValidationError(_('Ngày cấp không thể nhỏ hơn ngày sinh.'))

    @api.constrains('partner_id')
    def _check_unique_partner(self):
        for record in self:
            if record.partner_id:
                duplicate = self.search([
                    ('partner_id', '=', record.partner_id.id),
                    ('id', '!=', record.id)
                ])
                if duplicate:
                    raise ValidationError(_('Mỗi đối tác chỉ được có một hồ sơ nhà đầu tư.'))

    def write(self, vals):
        res = super().write(vals)
        if self.partner_id:
            self.env['status.info']._check_and_update_ho_so_goc(self.partner_id.id)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.partner_id:
                self.env['status.info']._check_and_update_ho_so_goc(record.partner_id.id)
        return records

