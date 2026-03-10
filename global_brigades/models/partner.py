# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import re


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # --- Perfil GB ---
    gb_gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Gender')
    gb_birthdate = fields.Date(string='Birthdate')
    gb_spanish_speaker = fields.Boolean(string='Spanish Speaker')
    gb_tshirt_size = fields.Selection([
        ('xs', 'X-Small'),
        ('s', 'Small'),
        ('m', 'Medium'),
        ('l', 'Large'),
        ('xl', 'X-Large'),
        ('xxl', 'XX-Large'),
    ], string='T-Shirt Size')

    gb_passport_no = fields.Char(string='Passport No.')
    gb_passport_expiry = fields.Date(string='Passport Expiry')
    gb_citizenship = fields.Char(string='Citizenship')

    # Salud / preferencias
    gb_diet = fields.Char(string='Diet')
    gb_medical_condition = fields.Char(string='Medical Condition')
    gb_allergy = fields.Char(string='Allergy')

    # ⛑️ PROFESIONAL DE LA SALUD
    gb_is_health_professional = fields.Boolean(
        string='Health Professional',
        help='Indicates whether this contact is a licensed health professional.',
    )

    gb_professional_registration = fields.Char(
        string='Professional Registration',
        help='Professional license or registration number of this health professional.',
    )

    # --- NUEVOS CAMPOS ---
    gb_emergency_contact_id = fields.Many2one(
        'res.partner',
        string='Emergency Contact',
        help='Primary emergency contact for this person.',
    )
    gb_medications = fields.Text(
        string='Medications',
        help='Relevant medications that the volunteer is currently taking.',
    )

    # --- Business Profile ---
    business_profile_link = fields.Char(
        string="Business Profile Link",
    )

    business_profile_html = fields.Html(
        string="Written Business Profile",
        sanitize=True,
    )

    # CHANGED: Selection -> Many2one to gb.brigade.role (user can add new roles)
    gb_brigade_role = fields.Many2one(
        'gb.brigade.role',
        string='Default Brigade Role',
        help='Default role that this person usually has in a brigade.',
    )

    # One2many de registros de idoneidad profesional
    gb_eligibility_ids = fields.One2many(
        'gb.partner.eligibility',
        'partner_id',
        string='Eligibility Records',
    )

    # --- Contadores (KPI) ---
    gb_hotel_offer_count = fields.Integer(
        string="Hotel Offers",
        compute="_compute_gb_counts",
        store=False,
    )

    gb_transport_vehicle_count = fields.Integer(
        string="Transport",
        compute="_compute_gb_counts",
        store=False,
    )

    def _should_show_phone(self):
        return self.env.context.get('show_mobile_in_name', False)

    @api.depends('name', 'mobile', 'phone')
    def _compute_display_name(self):
        super(ResPartner, self)._compute_display_name()
        if self._should_show_phone():
            for partner in self:
                name = partner.display_name or partner.name or ''
                mobile = partner.mobile or partner.phone or ''
                if mobile and mobile not in name:
                    partner.display_name = f"{name} ({mobile})"

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        result = super(ResPartner, self).name_search(name=name, args=args, operator=operator, limit=limit)
        if self._should_show_phone():
            new_result = []
            partner_ids = [r[0] for r in result]
            partners = self.browse(partner_ids)
            for partner in partners:
                partner_name = partner.name or ''
                mobile = partner.mobile or partner.phone or ''
                if mobile:
                    display_name = f"{partner_name} ({mobile})"
                else:
                    display_name = partner_name
                new_result.append((partner.id, display_name))
            return new_result
        return result

    def name_get(self):
        if self._should_show_phone():
            result = []
            for partner in self:
                name = partner.name or ''
                mobile = partner.mobile or partner.phone or ''
                if mobile:
                    display_name = f"{name} ({mobile})"
                else:
                    display_name = name
                result.append((partner.id, display_name))
            return result
        return super(ResPartner, self).name_get()

    def _normalize_tshirt_size(self, size_value):
        if not size_value:
            return size_value
        size_str = str(size_value).strip().lower()
        size_clean = re.sub(r'[\s\-_]+', '', size_str)
        size_map = {
            'xs': 'xs', 'xsmall': 'xs', 'extrasmall': 'xs', 'x-small': 'xs',
            's': 's', 'small': 's', 'sm': 's',
            'm': 'm', 'medium': 'm', 'med': 'm',
            'l': 'l', 'large': 'l', 'lrg': 'l',
            'xl': 'xl', 'xlarge': 'xl', 'extralarge': 'xl', 'x-large': 'xl',
            'xxl': 'xxl', 'xxlarge': 'xxl', '2xl': 'xxl', 'xx-large': 'xxl',
        }
        normalized = size_map.get(size_clean) or size_map.get(size_str)
        if normalized:
            return normalized
        if size_clean in ['xs', 's', 'm', 'l', 'xl', 'xxl']:
            return size_clean
        return size_value

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'gb_tshirt_size' in vals and vals['gb_tshirt_size']:
                vals['gb_tshirt_size'] = self._normalize_tshirt_size(vals['gb_tshirt_size'])
        return super(ResPartner, self).create(vals_list)

    def write(self, vals):
        if 'gb_tshirt_size' in vals and vals['gb_tshirt_size']:
            vals['gb_tshirt_size'] = self._normalize_tshirt_size(vals['gb_tshirt_size'])
        return super(ResPartner, self).write(vals)

    def _compute_gb_counts(self):
        HotelOffer = self.env['gb.hotel.offer']
        TransportProvider = self.env['gb.transport.provider']
        TransportVehicle = self.env['gb.transport.vehicle']
        for partner in self:
            partner.gb_hotel_offer_count = HotelOffer.search_count([('partner_id', '=', partner.id)])
            provider_ids = TransportProvider.search([('partner_id', '=', partner.id)]).ids
            partner.gb_transport_vehicle_count = TransportVehicle.search_count([('provider_id', 'in', provider_ids)])

    def action_view_gb_hotel_offers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Hotel Offers'),
            'res_model': 'gb.hotel.offer',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
            'target': 'current',
        }

    def action_view_gb_transport_vehicles(self):
        self.ensure_one()
        provider_ids = self.env['gb.transport.provider'].search([('partner_id', '=', self.id)]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Transport Vehicles'),
            'res_model': 'gb.transport.vehicle',
            'view_mode': 'list,form',
            'domain': [('provider_id', 'in', provider_ids)],
            'context': {'default_provider_id': provider_ids[:1] if provider_ids else False},
            'target': 'current',
        }


class GBPartnerEligibility(models.Model):
    _name = 'gb.partner.eligibility'
    _description = 'Health Professional Eligibility Record'

    partner_id = fields.Many2one('res.partner', string='Contact', required=True, ondelete='cascade')
    name = fields.Char(string='Eligibility Record', required=True)
    validity_date = fields.Date(string='Validity Date')
    attachment = fields.Binary(string='Eligibility Document')
    attachment_filename = fields.Char(string='File Name')
