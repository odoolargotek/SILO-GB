# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


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
        ('xs', 'XS'), ('s', 'S'), ('m', 'M'),
        ('l', 'L'), ('xl', 'XL'), ('xxl', 'XXL'),
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
    # Contacto de emergencia y medicación
    gb_emergency_contact_id = fields.Many2one(
        'res.partner',
        string='Emergency Contact',
        help='Primary emergency contact for this person.',
    )
    gb_medications = fields.Text(
        string='Medications',
        help='Relevant medications that the volunteer is currently taking.',
    )

    # --- Business Profile (para programas / clientes de negocio) ---
    business_profile_link = fields.Char(
        string="Business Profile Link",
        help=(
            "External link (e.g. Google Drive, website, shared folder) with "
            "additional business information for this contact."
        ),
    )

    business_profile_html = fields.Html(
        string="Written Business Profile",
        sanitize=True,
        help=(
            "Rich-text description of the business profile. You can paste "
            "content from documents, emails or websites."
        ),
    )

    # Default brigade role (lista actualizada y simplificada)
    gb_brigade_role = fields.Selection(
        [
            ('lead_coordinator', 'Lead Coordinator'),
            ('interpreter', 'Interpreter'),
            ('assistant_coordinator', 'Assistant Coordinator'),
            ('counselor', 'Counselor'),
            ('doctor', 'Doctor'),
            ('dentist', 'Dentist'),
            ('pharmacist', 'Pharmacist'),
            ('paramedic', 'Paramedic'),
            ('optometrist', 'Optometrist'),
            ('nurse', 'Nurse'),
            ('nurse_technician', 'Nurse Technician'),
            ('lab_technician', 'Lab Technician'),
            ('dental_technician', 'Dental Technician'),
            ('obgyn', 'OB/GYN'),
            ('compound_supervisor', 'Compound Supervisor'),
            ('driver_pacecar', 'Driver (Pacecar)'),
            ('bus_driver', 'Bus Driver'),
            ('driver', 'Driver'),
            ('physiotherapist', 'Physiotherapist'),
            ('public_health_technician', 'Public Health Technician'),
            ('water_technician', 'Water Technician'),
            ('program_advisor', 'Program Advisor'),
            ('chapter_leader', 'Chapter Leader'),
            ('chapter_president', 'Chapter President'),
            ('brigade_leader', 'Brigade Leader'),
            ('hcp', 'HCP'),
            ('faculty_member', 'Faculty Member'),
            ('chaperone', 'Chaperone'),
            ('volunteer', 'Volunteer'),
            ('student', 'Student'),
            ('team_lead', 'Team Lead'),
            ('ambassador', 'Ambassador'),
            ('mentor', 'Mentor'),
            ('other', 'Other'),
        ],
        string='Default Brigade Role',
        help='Default role that this person usually has in a brigade.',
    )
    # One2many de registros de idoneidad profesional
    gb_eligibility_ids = fields.One2many(
        'gb.partner.eligibility',
        'partner_id',
        string='Eligibility Records',
        help='Professional eligibility / licensing records for this contact.',
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

    def _compute_gb_counts(self):
        HotelOffer = self.env['gb.hotel.offer']
        TransportProvider = self.env['gb.transport.provider']
        TransportVehicle = self.env['gb.transport.vehicle']
        for partner in self:
            partner.gb_hotel_offer_count = HotelOffer.search_count([
                ('partner_id', '=', partner.id)
            ])

            provider_ids = TransportProvider.search([
                ('partner_id', '=', partner.id)
            ]).ids

            partner.gb_transport_vehicle_count = TransportVehicle.search_count([
                ('provider_id', 'in', provider_ids)
            ])

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
        provider_ids = self.env['gb.transport.provider'].search([
            ('partner_id', '=', self.id)
        ]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Transport Vehicles'),
            'res_model': 'gb.transport.vehicle',
            'view_mode': 'list,form',
            'domain': [('provider_id', 'in', provider_ids)],
            'context': {
                'default_provider_id': provider_ids[:1] if provider_ids else False,
            },
            'target': 'current',
        }


class GBPartnerEligibility(models.Model):
    _name = 'gb.partner.eligibility'
    _description = 'Health Professional Eligibility Record'

    partner_id = fields.Many2one(
        'res.partner',
        string='Contact',
        required=True,
        ondelete='cascade',
    )

    name = fields.Char(
        string='Eligibility Record',
        required=True,
        help='Description or number of the eligibility / license record.',
    )

    validity_date = fields.Date(
        string='Validity Date',
        help='Date until which this eligibility record is valid.',
    )

    attachment = fields.Binary(
        string='Eligibility Document',
        help='Digital copy of the eligibility / license certificate.',
    )

    attachment_filename = fields.Char(
        string='File Name',
    )
