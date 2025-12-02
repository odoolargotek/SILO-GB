# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


# =========================================================
# MODELO: Etiquetas de transporte (nuevo)
# =========================================================
class GBTransportTag(models.Model):
    _name = 'gb.transport.tag'
    _description = 'Transport Tag'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    color = fields.Integer(string='Color', default=0)
    active = fields.Boolean(default=True)


# =========================================================
# MODELO: Vehículo
# =========================================================
class GBTransportVehicle(models.Model):
    _name = 'gb.transport.vehicle'
    _description = 'Transport Vehicle'
    _order = 'name'

    name = fields.Char(string='Vehicle Name', required=True)
    provider_id = fields.Many2one(
        'gb.transport.provider',
        string='Transport Provider',
        required=True,
        ondelete='cascade'
    )
    license_plate = fields.Char(string='License Plate')
    vehicle_type = fields.Selection([
        ('bus', 'Bus'),
        ('minibus', 'Minibus'),
        ('van', 'Van'),
        ('car', 'Car'),
        ('other', 'Other'),
    ], string='Vehicle Type', default='bus')
    capacity = fields.Integer(string='Seating Capacity')
    driver_name = fields.Char(string='Driver Name')
    driver_phone = fields.Char(string='Driver Phone')
    tag_ids = fields.Many2many(
        'gb.transport.tag',
        'gb_transport_vehicle_tag_rel',
        'vehicle_id', 'tag_id',
        string='Tags'
    )
    notes = fields.Text(string='Notes')


# =========================================================
# MODELO: Proveedor de Transporte
# =========================================================
class GBTransportProvider(models.Model):
    _name = 'gb.transport.provider'
    _description = 'Transport Provider'
    _order = 'name'

    name = fields.Char(string='Provider Name', required=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        domain=[('is_company', '=', True)],
        help="Select the transport company contact."
    )
    contact_phone = fields.Char(related='partner_id.phone', string='Phone', readonly=True)
    contact_email = fields.Char(related='partner_id.email', string='Email', readonly=True)
    address = fields.Char(related='partner_id.contact_address', string='Address', readonly=True)
    notes = fields.Text(string='Notes')

    vehicle_ids = fields.One2many(
        'gb.transport.vehicle',
        'provider_id',
        string='Vehicles'
    )

    vehicle_count = fields.Integer(
        string='Vehicles Count',
        compute='_compute_vehicle_count'
    )

    # --- Cálculo de cantidad de vehículos ---
    def _compute_vehicle_count(self):
        for rec in self:
            rec.vehicle_count = len(rec.vehicle_ids)

    # --- Acción para ver vehículos desde el proveedor ---
    def action_view_vehicles(self):
        self.ensure_one()
        return {
            'name': _('Vehicles'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'gb.transport.vehicle',
            'domain': [('provider_id', '=', self.id)],
            'context': {'default_provider_id': self.id},
        }
