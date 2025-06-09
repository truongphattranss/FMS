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
    bank_account_ids = fields.One2many('investor.bank.account', 'investor_id', string='Bank Accounts')

    # Address information
    address_ids = fields.One2many('investor.address', 'investor_id', string='Addresses')

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

class InvestorBankAccount(models.Model):
    _name = 'investor.bank.account'
    _description = 'Investor Bank Account'

    investor_id = fields.Many2one('investor.profile', string='Investor', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', related='investor_id.partner_id', string='Partner', store=True)
    bank_name = fields.Char(string='Bank Name', required=True)
    account_number = fields.Char(string='Account Number', required=True)
    account_holder = fields.Char(string='Account Holder Name', required=True)
    branch = fields.Char(string='Branch')
    is_default = fields.Boolean(string='Default Account')

    @api.model
    def create(self, vals):
        if vals.get('is_default'):
            self.search([
                ('partner_id', '=', self.env['investor.profile'].browse(vals.get('investor_id')).partner_id.id),
                ('is_default', '=', True)
            ]).write({'is_default': False})
        return super().create(vals)

    def write(self, vals):
        if vals.get('is_default'):
            self.search([
                ('partner_id', '=', self.partner_id.id),
                ('is_default', '=', True),
                ('id', '!=', self.id)
            ]).write({'is_default': False})
        return super().write(vals)

class InvestorAddress(models.Model):
    _name = 'investor.address'
    _description = 'Investor Address'

    investor_id = fields.Many2one('investor.profile', string='Investor', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', related='investor_id.partner_id', string='Partner', store=True)
    address_type = fields.Selection([
        ('permanent', 'Permanent Address'),
        ('current', 'Current Address'),
        ('other', 'Other')
    ], string='Address Type', required=True)
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    city = fields.Char(string='City')
    district = fields.Char(string='Quận/Huyện')
    ward = fields.Char(string='Phường/Xã')
    state_id = fields.Many2one('res.country.state', string='State')
    zip = fields.Char(string='ZIP')
    country_id = fields.Many2one('res.country', string='Country')
    is_default = fields.Boolean(string='Default Address')

    @api.model
    def create(self, vals):
        if vals.get('is_default'):
            self.search([
                ('partner_id', '=', self.env['investor.profile'].browse(vals.get('investor_id')).partner_id.id),
                ('is_default', '=', True)
            ]).write({'is_default': False})
        return super().create(vals)

    def write(self, vals):
        if vals.get('is_default'):
            self.search([
                ('partner_id', '=', self.partner_id.id),
                ('is_default', '=', True),
                ('id', '!=', self.id)
            ]).write({'is_default': False})
        return super().write(vals)

