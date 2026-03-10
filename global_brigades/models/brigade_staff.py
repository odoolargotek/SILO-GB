# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class GBBrigadeStaff(models.Model):
    _name = 'gb.brigade.staff'
    _description = 'Brigade Staff Assignment'
    _order = 'sequence, start_datetime, person_id'
    _rec_name = 'name'

    sequence = fields.Integer(string="Sequence", default=10)
    line_number = fields.Integer(string="N", default=0)
    name = fields.Char(string='Name', compute='_compute_name', store=True)

    brigade_id = fields.Many2one('gb.brigade', string='Brigade', required=True, ondelete='cascade')
    person_id = fields.Many2one('res.partner', string='Person', required=True)

    gender = fields.Selection(related='person_id.gb_gender', string='Gender', readonly=True)
    diet = fields.Char(related='person_id.gb_diet', string='Diet', readonly=True)
    allergy = fields.Char(related='person_id.gb_allergy', string='Allergy', readonly=True)
    professional_registration = fields.Char(
        related='person_id.gb_professional_registration',
        string='Professional Registration',
        readonly=True,
        store=False,
    )

    # CHANGED: Many2one to gb.brigade.role catalog (user can add new roles freely)
    brigade_role_default = fields.Many2one(
        'gb.brigade.role',
        string='Brigade Role',
        help='Role for this staff member. You can add new roles directly from this field.',
    )

    staff_role = fields.Selection(
        [
            ('driver', 'DRIVER'),
            ('operations_coord', 'OPERATIONS COORDINATOR'),
            ('interpreter_1', 'INTERPRETER 1'),
            ('interpreter_2', 'INTERPRETER 2'),
            ('interpreter_3', 'INTERPRETER 3'),
            ('interpreter_4', 'INTERPRETER 4'),
            ('interpreter_5', 'INTERPRETER 5'),
            ('interpreter_extra', 'INTERPRETER EXTRA'),
            ('doctor_1', 'DOCTOR 1'),
            ('doctor_2', 'DOCTOR 2'),
            ('doctor_3', 'DOCTOR 3'),
            ('doctor_4', 'DOCTOR 4'),
            ('dentist_1', 'DENTIST 1'),
            ('dentist_2', 'DENTIST 2'),
            ('dentist_3', 'DENTIST 3'),
            ('dentist_4', 'DENTIST 4'),
            ('pharmacist', 'PHARMACIST'),
            ('cashier', 'CASHIER'),
            ('nutritionist', 'NUTRITIONIST'),
            ('public_health_tech', 'PUBLIC HEALTH TECHNICIAN'),
            ('paramedic', 'PARAMEDIC'),
            ('water_technician', 'WATER TECHNICIAN'),
            ('optometrist', 'OPTOMETRIST'),
            ('nurse', 'NURSE'),
            ('obgyn', 'OB/GYN'),
            ('pa_visit', 'PA VISIT'),
            ('emergency_vehicle', 'EMERGENCY VEHICLE'),
            ('physiotherapist', 'PHYSIOTHERAPIST'),
            ('doctor_de_cobertura', 'DOCTOR DE COBERTURA'),
            ('doctor_on_call', 'DOCTOR ON CALL'),
            ('coord_assistant_1', 'COORDINATION ASSISTANT 1'),
            ('coord_assistant_2', 'COORDINATION ASSISTANT 2'),
            ('coord_assistant_3', 'COORDINATION ASSISTANT 3'),
            ('coord_assistant_4', 'COORDINATION ASSISTANT 4'),
            ('coord_assistant_5', 'COORDINATION ASSISTANT 5'),
            ('coord_assistant_extra', 'COORDINATION ASSISTANT EXTRA'),
            ('counselor_1', 'COUNSELOR 1'),
            ('counselor_2', 'COUNSELOR 2'),
            ('counselor_3', 'COUNSELOR 3'),
            ('lead_coord_1', 'LEAD COORDINATOR 1'),
            ('lead_coord_2', 'LEAD COORDINATOR 2'),
            ('lead_coord_3', 'LEAD COORDINATOR 3'),
            ('lead_coord_4', 'LEAD COORDINATOR 4'),
            ('lead_coord_5', 'LEAD COORDINATOR 5'),
            ('lead_coord_extra', 'LEAD COORDINATOR EXTRA'),
            ('psychologist', 'PSYCHOLOGIST'),
            ('therapist', 'THERAPIST'),
            ('other', 'OTHER / NOTES IN FIELD'),
        ],
        string='Role',
    )

    start_datetime = fields.Datetime(string='Start Date/Time')
    end_datetime = fields.Datetime(string='End Date/Time')
    diet_allergy_note = fields.Char(string='Diet / Allergy / Notes')
    internal_note = fields.Text(string='Internal Notes')
    provider_id = fields.Many2one('res.partner', string='Provider')

    @api.onchange('person_id')
    def _onchange_person_id_brigade_role(self):
        """Pre-fill brigade_role_default from contact profile when person changes."""
        for rec in self:
            if rec.person_id and rec.person_id.gb_brigade_role:
                rec.brigade_role_default = rec.person_id.gb_brigade_role

    @api.depends('person_id', 'person_id.name', 'provider_id', 'provider_id.name', 'staff_role')
    def _compute_name(self):
        selection_dict = dict(self._fields['staff_role'].selection)
        for rec in self:
            base = rec.person_id.name or rec.provider_id.name or ""
            role_label = selection_dict.get(rec.staff_role, rec.staff_role or "")
            if base and role_label:
                rec.name = f"{base} ({role_label})"
            else:
                rec.name = base or role_label or _("Staff #%s") % rec.id

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for brigade in records.mapped('brigade_id'):
            brigade._renumber_staff()
        return records

    def write(self, vals):
        result = super().write(vals)
        if 'sequence' in vals:
            for brigade in self.mapped('brigade_id'):
                brigade._renumber_staff()
        return result

    def unlink(self):
        brigades = self.mapped('brigade_id')
        result = super().unlink()
        for brigade in brigades:
            brigade._renumber_staff()
        return result

    def name_get(self):
        res = []
        selection_dict = dict(self._fields['staff_role'].selection)
        for rec in self:
            base = rec.person_id.name or rec.provider_id.name or ""
            role_label = selection_dict.get(rec.staff_role, rec.staff_role or "")
            name = f"{base} ({role_label})" if base and role_label else base or role_label or _("Staff #%s") % rec.id
            res.append((rec.id, name))
        return res
