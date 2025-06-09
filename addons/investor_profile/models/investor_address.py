from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

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
    street = fields.Char(string='Số nhà, tên đường', required=True)
    city = fields.Char(string='City')
    district = fields.Char(string='Quận/Huyện', required=True)
    ward = fields.Char(string='Phường/Xã', required=True)
    state_id = fields.Many2one('res.country.state', string='Tỉnh/Thành', required=True)
    zip = fields.Char(string='ZIP')
    country_id = fields.Many2one('res.country', string='Quốc gia', required=True)
    is_default = fields.Boolean(string='Default Address')

    @api.model
    def create(self, vals):
        if vals.get('is_default'):
            self.search([
                ('partner_id', '=', self.env['investor.profile'].browse(vals.get('investor_id')).partner_id.id),
                ('is_default', '=', True)
            ]).write({'is_default': False})
        record = super().create(vals)
        if record.partner_id:
            self.env['status.info']._check_and_update_ho_so_goc(record.partner_id.id)
        return record

    def write(self, vals):
        if vals.get('is_default'):
            self.search([
                ('partner_id', '=', self.partner_id.id),
                ('is_default', '=', True),
                ('id', '!=', self.id)
            ]).write({'is_default': False})
        res = super().write(vals)
        if self.partner_id:
            self.env['status.info']._check_and_update_ho_so_goc(self.partner_id.id)
        return res

    @api.constrains('street', 'city', 'district', 'ward', 'state_id', 'country_id')
    def _check_required_address_fields(self):
        for record in self:
            if record.address_type in ['permanent', 'current']:
                if not record.street:
                    raise ValidationError(_('Vui lòng nhập số nhà, tên đường.'))
                if not record.district:
                    raise ValidationError(_('Vui lòng nhập quận/huyện.'))
                if not record.ward:
                    raise ValidationError(_('Vui lòng nhập phường/xã.'))
                if not record.state_id:
                    raise ValidationError(_('Vui lòng chọn tỉnh/thành phố.'))
                if not record.country_id:
                    raise ValidationError(_('Vui lòng chọn quốc gia.'))

    @api.constrains('zip')
    def _check_zip(self):
        for record in self:
            if record.zip:
                if not record.zip.isdigit() or len(record.zip) != 6:
                    raise ValidationError(_('Mã bưu điện phải gồm 6 chữ số.'))

    @api.constrains('address_type')
    def _check_address_type(self):
        for record in self:
            if record.address_type == 'permanent':
                permanent_count = self.search_count([
                    ('partner_id', '=', record.partner_id.id),
                    ('address_type', '=', 'permanent'),
                    ('id', '!=', record.id)
                ])
                if permanent_count > 0:
                    raise ValidationError(_('Mỗi người dùng chỉ được có một địa chỉ thường trú.')) 