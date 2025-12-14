# -*- coding: utf-8 -*-

# LT Brigade Module - Mejoras Odoo 18
# Largotek SRL - Juan Luis Garvía - www.largotek.com
# License: LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class GBBrigade(models.Model):
    _name = "gb.brigade"
    _description = "Global Brigades - Chapter / Brigade"
    _order = "id desc"

    # =========================
    # IDENTIFICACIÓN BÁSICA
    # =========================
    external_brigade_code = fields.Char(
        string="Brigade Code",
        help="External reference / code from CRM or other system.",
    )

    brigade_code = fields.Char(
        string="Internal Code",
        readonly=True,
        copy=False,
        default="/",
    )

    name = fields.Char(string="CHAPTER NAME", required=True)
    arrival_date = fields.Date(string="Arrival Date")
    departure_date = fields.Date(string="Departure Date")

    # =========================
    # ESTADO OPERATIVO
    # =========================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("planned", "Planned"),
            ("ready", "Ready"),
            ("in_field", "In Field"),
            ("completed", "Completed"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        required=True,
        help="Operational state of the Brigade",
    )

    brigade_type = fields.Selection(
        [
            ("onsite", "In Person"),
            ("virtual", "Virtual"),
        ],
        string="Brigade Type",
        default="onsite",
        required=True,
        help="If set to Virtual, logistics sections should not be used.",
    )

    brigade_restriction = fields.Selection(
        [
            ("darien_golfo", "Darien & Golfo de Mosquito"),
            ("este_darien", "Este y Darien"),
            ("solo_darien", "Solo Darien"),
            ("otros", "Otros"),
        ],
        string="Restrictions",
        help="Geographic / operational restrictions.",
    )

    brigade_program = fields.Selection(
        [
            ("medical", "Medical"),
            ("dental", "Dental"),
            ("business", "Business"),
            ("water", "Water"),
            ("public_health", "Public Health"),
            ("engineering", "Engineering"),
            ("squads", "Squads"),
        ],
        string="Official Program",
        help="Main official program.",
    )

    # =========================
    # LT ITINERARY SIMPLE
    # =========================
    lt_itinerary_link = fields.Char(
        string="Itinerary Link",
        help="Pegar link de GDrive o cualquier URL.",
    )

    lt_itinerary_locked = fields.Boolean(
        string="Bloquear Link",
        default=False,
    )

    lt_itinerary_url = fields.Char(
        string="Itinerary URL",
        compute="_compute_lt_itinerary_url",
        store=True,
        readonly=True,
    )

    # =========================
    # BUSINESS / TIER
    # =========================
    business_client_id = fields.Many2one(
        "res.partner",
        string="Business Client",
        help="Client when program is Business.",
    )

    business_profile_link = fields.Char(
        string="Business Profile Link",
        related="business_client_id.business_profile_link",
        readonly=True,
    )

    @api.onchange("brigade_program")
    def _onchange_brigade_program_business_client(self):
        for record in self:
            if record.brigade_program != "business":
                record.business_client_id = False

    brigade_tier = fields.Selection(
        [
            ("sustainable", "Sustainable"),
            ("empowered", "Empowered"),
            ("scaled", "Scaled"),
        ],
        string="Brigade Tier",
        help="Tier: Sustainable(14-25), Empowered(26-39), Scaled(40+).",
    )

    # =========================
    # CONTADORES UNIFICADOS
    # =========================
    volunteer_count = fields.Integer(
        string="Volunteers", compute="_compute_counts"
    )
    program_count = fields.Integer(
        string="Programs", compute="_compute_counts"
    )
    activity_count = fields.Integer(
        string="Activities", compute="_compute_counts"
    )
    transport_count = fields.Integer(
        string="Transports", compute="_compute_counts"
    )

    university_logo = fields.Image(string="University Logo")
    compound_manager_id = fields.Many2one(
        "res.partner", string="COMPOUND SUPERVISOR"
    )
    arrival_time_compound = fields.Datetime(
        string="Arrival time to Compound"
    )
    departure_time_compound = fields.Datetime(
        string="Departure time from Compound"
    )
    coordinator_id = fields.Many2one(
        "res.partner", string="LEAD COORDINATOR"
    )
    program_associate_id = fields.Many2one(
        "res.partner", string="PROGRAM ADVISOR"
    )

    chapter_leader_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_brigade_chapter_leader_rel",
        "brigade_id",
        "roster_id",
        string="Chapter Leader(s)",
    )
    chapter_president_faculty_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_brigade_chapter_president_faculty_rel",
        "brigade_id",
        "roster_id",
        string="Chapter President / Faculty",
    )
    professor_chaperone_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_brigade_professor_chaperone_rel",
        "brigade_id",
        "roster_id",
        string="Professor / Chaperone",
    )

    extra_info = fields.Text(string="Additional Information")

    # =========================
    # ONE2MANY RELACIONES
    # =========================
    program_line_ids = fields.One2many(
        "gb.brigade.program", "brigade_id", string="Programs"
    )
    roster_ids = fields.One2many(
        "gb.brigade.roster", "brigade_id", string="Roster"
    )
    arrival_ids = fields.One2many(
        "gb.brigade.arrival", "brigade_id", string="Arrivals"
    )
    departure_ids = fields.One2many(
        "gb.brigade.departure", "brigade_id", string="Departures"
    )
    staff_ids = fields.One2many(
        "gb.brigade.staff", "brigade_id", string="Temp Staff"
    )
    activity_ids = fields.One2many(
        "gb.brigade.activity", "brigade_id", string="Activities"
    )
    hotel_booking_ids = fields.One2many(
        "gb.brigade.hotel.booking", "brigade_id", string="Hotel"
    )
    transport_ids = fields.One2many(
        "gb.brigade.transport", "brigade_id", string="Transport"
    )

    _sql_constraints = [
        (
            "chapter_code_uniq",
            "unique(brigade_code)",
            "Brigade Code must be unique!",
        ),
    ]

    # =========================
    # COMPUTES / CONSTRAINS
    # =========================
    @api.depends("roster_ids", "program_line_ids", "activity_ids", "transport_ids")
    def _compute_counts(self):
        for rec in self:
            rec.volunteer_count = len(rec.roster_ids)
            rec.program_count = len(rec.program_line_ids)
            rec.activity_count = len(rec.activity_ids)
            rec.transport_count = len(rec.transport_ids)

    @api.constrains(
        "brigade_type",
        "transport_ids",
        "hotel_booking_ids",
        "arrival_ids",
        "departure_ids",
    )
    def _check_virtual_no_logistics(self):
        for rec in self:
            if rec.brigade_type == "virtual" and (
                rec.transport_ids
                or rec.hotel_booking_ids
                or rec.arrival_ids
                or rec.departure_ids
            ):
                raise ValidationError(
                    _("Virtual brigades cannot have logistics records.")
                )

    # =========================
    # ITINERARY URL (compute)
    # =========================
    @api.depends("lt_itinerary_link")
    def _compute_lt_itinerary_url(self):
        for rec in self:
            if rec.lt_itinerary_link:
                url = rec.lt_itinerary_link.strip()
                if not (url.startswith("http://") or url.startswith("https://")):
                    url = "https://" + url
                rec.lt_itinerary_url = url
            else:
                rec.lt_itinerary_url = False


# =========================
# WRITE / CREATE / ACTIONS
# =========================

def write(self, vals):
    if "lt_itinerary_link" in vals:
        for rec in self:
            if rec.lt_itinerary_locked:
                raise ValidationError(
                    _("Itinerary Link está BLOQUEADO. Desactiva el switch primero.")
                )
    return super().write(vals)


@api.model
def create(self, vals):
    code = vals.get("brigade_code") or "/"
    if code == "/":
        next_code = self.env["ir.sequence"].next_by_code("gb.brigade.code")
        if not next_code:
            raise ValidationError(
                _(
                    "No se pudo obtener la secuencia 'gb.brigade.code'. "
                    "Verifica que 'sequence.xml' esté cargado en el manifest."
                )
            )
        vals["brigade_code"] = next_code
    return super().create(vals)


def open_form_action(self):
    """Abre el formulario de la brigada desde la vista lista."""
    self.ensure_one()
    return {
        "type": "ir.actions.act_window",
        "name": _("Brigade"),
        "res_model": "gb.brigade",
        "view_mode": "form",
        "res_id": self.id,
        "target": "current",
    }


def action_open_roster_import_wizard(self):
    """
    Abre el wizard de importación de Roster desde Excel.
    (Odoo 18 safe: NO usa active_id en XML)
    """
    self.ensure_one()
    action = self.env.ref(
        "global_brigades.action_gb_roster_import_wizard"
    ).read()[0]
    action["context"] = dict(
        self.env.context,
        default_brigade_id=self.id,
    )
    return action
# ===========================================================
# Program Lines (PROGRAMS tab)
# ===========================================================
class GBBrigadeProgram(models.Model):
    _name = "gb.brigade.program"
    _description = "Brigade Program Line"
    _order = "sequence, id"

    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        ondelete="cascade",
        required=True,
    )

    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Order of this program line in the list.",
    )

    program_id = fields.Many2one(
        "gb.program",
        string="Program",
        required=True,
        help="Program type (Medical, Dental, Business, etc.) for this line.",
    )

    start_date = fields.Date(
        string="Start Date",
        help="When this program begins for this brigade.",
    )

    end_date = fields.Date(
        string="End Date",
        help="When this program ends for this brigade.",
    )

    # NUEVO: selección de comunidad desde el nuevo modelo
    community_id = fields.Many2one(
        "gb.community",
        string="Community",
        help="Community where this program activity will take place.",
    )

    # Seguimos usando el campo location para guardar el nombre de la comunidad
    location = fields.Char(
        string="Location / Community / Site",
        help="Where this program activity will take place.",
    )

    coordinator_id = fields.Many2one(
        "res.partner",
        string="Program Lead / Coordinator",
        help="Main staff contact for this program line.",
    )

    notes = fields.Char(
        string="Notes / Focus Area",
        help="Extra notes about this program line (focus, goals, etc.).",
    )

    @api.onchange("community_id")
    def _onchange_community_id(self):
        """Cuando se elige una comunidad, copiamos el nombre al campo location."""
        for rec in self:
            rec.location = rec.community_id.name or False

# ===========================================================
# Program Lines (PROGRAMS tab)
# ===========================================================

class GBBrigadeProgram(models.Model):
    _name = "gb.brigade.program"
    _description = "Brigade Program Line"
    _order = "sequence, id"
    
    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        ondelete="cascade",
        required=True,
    )
    
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Order of this program line in the list.",
    )
    
    program_id = fields.Many2one(
        "gb.program",
        string="Program",
        required=True,
        help="Program type (Medical, Dental, Business, etc.) for this line.",
    )
    
    start_date = fields.Date(
        string="Start Date",
        help="When this program begins for this brigade.",
    )
    
    end_date = fields.Date(
        string="End Date",
        help="When this program ends for this brigade.",
    )
    
    community_id = fields.Many2one(
        "gb.community",
        string="Community",
        help="Community where this program activity will take place.",
    )
    
    location = fields.Char(
        string="Location / Community / Site",
        help="Where this program activity will take place.",
    )
    
    coordinator_id = fields.Many2one(
        "res.partner",
        string="Program Lead / Coordinator",
        help="Main staff contact for this program line.",
    )
    
    notes = fields.Char(
        string="Notes / Focus Area",
        help="Extra notes about this program line (focus, goals, etc.).",
    )
    
    @api.onchange("community_id")
    def _onchange_community_id(self):
        """Cuando se elige una comunidad, copiamos el nombre al campo location."""
        for rec in self:
            rec.location = rec.community_id.name or False

# ===========================================================
# Roster (participantes / voluntarios)
# ===========================================================

class GBBrigadeRoster(models.Model):
    _name = "gb.brigade.roster"
    _description = "Global Brigades - Roster"
    _rec_name = "partner_id"
    _order = "id"

    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        required=True,
        ondelete="cascade",
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Name",
        required=True,
    )

    email = fields.Char(
        string="Email",
        related="partner_id.email",
        store=False,
        readonly=True,
    )

    phone_display = fields.Char(
        string="Phone Number",
        compute="_compute_phone_display",
        help="Concatenates Mobile and Phone if available.",
    )

    gender = fields.Selection(
        related="partner_id.gb_gender",
        readonly=True,
        store=False,
    )

    birthdate = fields.Date(
        related="partner_id.gb_birthdate",
        readonly=True,
        store=False,
    )

    spanish_speaker = fields.Boolean(
        string="Spanish Speaker",
        related="partner_id.gb_spanish_speaker",
        readonly=True,
        store=False,
    )

    passport_no = fields.Char(
        related="partner_id.gb_passport_no",
        readonly=True,
        store=False,
    )

    passport_expiry = fields.Date(
        related="partner_id.gb_passport_expiry",
        readonly=True,
        store=False,
    )

    citizenship = fields.Char(
        related="partner_id.gb_citizenship",
        readonly=True,
        store=False,
    )

    tshirt_size = fields.Selection(
        related="partner_id.gb_tshirt_size",
        readonly=True,
        store=False,
    )

    brigade_role = fields.Char(string="Role in Brigade")
    sa = fields.Boolean(string="S.A.")

    # Estos vienen desde res.partner (gb_diet, gb_medical_condition, gb_medications, gb_allergy)
    diet = fields.Char(
        string="Diet / Restrictions",
        related="partner_id.gb_diet",
        store=False,
        readonly=True,
    )

    medical_condition = fields.Char(
        string="Medical Condition",
        related="partner_id.gb_medical_condition",
        store=False,
        readonly=True,
    )

    medications = fields.Text(
        string="Medications",
        related="partner_id.gb_medications",
        store=False,
        readonly=True,
    )

    allergy = fields.Char(
        string="Allergies",
        related="partner_id.gb_allergy",
        store=False,
        readonly=True,
    )

    emergency_contact_id = fields.Many2one(
        "res.partner",
        string="Emergency Contact",
    )

    emergency_contact_email = fields.Char(
        string="Emergency Contact Email",
        related="emergency_contact_id.email",
        store=False,
        readonly=True,
    )

    @api.depends("partner_id.mobile", "partner_id.phone")
    def _compute_phone_display(self):
        for rec in self:
            mobile = rec.partner_id.mobile or ""
            phone = rec.partner_id.phone or ""
            if mobile and phone and mobile != phone:
                rec.phone_display = f"{mobile} / {phone}"
            else:
                rec.phone_display = mobile or phone or ""
# ===========================================================
# Arrivals (Warning only, no blocking)
# ===========================================================

class GBBrigadeArrival(models.Model):
    _name = "gb.brigade.arrival"
    _description = "Global Brigades - Arrival Info"
    _order = "date_time_arrival, id"

    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        required=True,
        ondelete="cascade",
    )

    title = fields.Char(string="Title / Ref", required=True)
    flight_number = fields.Char(string="Flight #")
    date_time_arrival = fields.Datetime(string="Arrival DateTime")
    flight_through_sap = fields.Char(string="Through SAP / Stopover")

    arrival_hotel_id = fields.Many2one(
        "gb.hotel.offer",
        string="Arrival Hotel",
    )

    arrival_hotel_city_time = fields.Char(
        string="Arrival Hotel Notes (City / Time)",
    )

    passenger_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_arrival_roster_rel",
        "arrival_id",
        "roster_id",
        string="Passengers",
    )

    available_passenger_ids = fields.Many2many(
        "gb.brigade.roster",
        compute="_compute_available_passenger_ids",
        store=False,
    )

    n_pax = fields.Integer(
        string="# Pax",
        compute="_compute_n_pax",
        store=False,
    )

    special_transport = fields.Boolean(string="Special Transport Needed?")
    extra_charge = fields.Char(string="Extra Charge / Notes")

    # ---------------- COMPUTES ----------------

    @api.depends("passenger_ids")
    def _compute_n_pax(self):
        for rec in self:
            rec.n_pax = len(rec.passenger_ids)

    @api.depends("brigade_id", "brigade_id.roster_ids",
                 "brigade_id.arrival_ids.passenger_ids", "passenger_ids")
    def _compute_available_passenger_ids(self):
        for rec in self:
            if not rec.brigade_id:
                rec.available_passenger_ids = False
                continue

            all_roster = rec.brigade_id.roster_ids
            other_arrivals_passengers = rec.brigade_id.arrival_ids.filtered(
                lambda a: a.id != rec.id
            ).mapped("passenger_ids")

            used = other_arrivals_passengers
            available = (all_roster - used) | rec.passenger_ids
            rec.available_passenger_ids = available

    # ---------------- WARNING ONLY ----------------

    @api.onchange("passenger_ids")
    def _onchange_passenger_ids_duplicates(self):
        """
        Warning only (no constraint). User can still save.
        """
        for rec in self:
            if not rec.brigade_id or not rec.passenger_ids:
                continue

            passenger_ids = rec.passenger_ids.ids
            Arrival = self.env["gb.brigade.arrival"]

            other_arrivals = Arrival.search([
                ("brigade_id", "=", rec.brigade_id.id),
                ("id", "!=", rec.id),
                ("passenger_ids", "in", passenger_ids),
            ])

            if not other_arrivals:
                continue

            conflicts = {}
            for other in other_arrivals:
                common = other.passenger_ids.filtered(
                    lambda p: p.id in passenger_ids
                )
                for p in common:
                    conflicts.setdefault(
                        p.partner_id.name or p.display_name, []
                    ).append(
                        _("Arrival: %(title)s (%(date)s)") % {
                            "title": other.title or "",
                            "date": fields.Datetime.to_string(
                                other.date_time_arrival
                            ) if other.date_time_arrival else "",
                        }
                    )

            if conflicts:
                lines = []
                for name, entries in conflicts.items():
                    lines.append(f"- {name}: " + "; ".join(entries))

                message = (
                    "These passengers already appear in another Arrival of this brigade:\n"
                    + "\n".join(lines)
                )

                return {
                    "warning": {
                        "title": _("Passenger already in another Arrival"),
                        "message": message,
                    }
                }

# ===========================================================
# Departures (Warning only, no blocking)
# ===========================================================

class GBBrigadeDeparture(models.Model):
    _name = "gb.brigade.departure"
    _description = "Global Brigades - Departure Info"
    _order = "date_time_departure, id"

    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        required=True,
        ondelete="cascade",
    )

    title = fields.Char(string="Title / Ref", required=True)
    flight_number = fields.Char(string="Flight #")
    date_time_departure = fields.Datetime(string="Departure DateTime")
    flight_through_sap = fields.Char(string="Through SAP / Stopover")

    departure_hotel_id = fields.Many2one(
        "gb.hotel.offer",
        string="Departure Hotel",
    )

    departure_hotel_city = fields.Char(
        string="Departure Hotel Notes (City)",
    )

    passenger_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_departure_roster_rel",
        "departure_id",
        "roster_id",
        string="Passengers",
    )

    available_passenger_ids = fields.Many2many(
        "gb.brigade.roster",
        compute="_compute_available_passenger_ids",
        store=False,
    )

    n_pax = fields.Integer(
        string="# Pax",
        compute="_compute_n_pax",
        store=False,
    )

    special_transport = fields.Boolean(string="Special Transport Needed?")
    extra_charge = fields.Char(string="Extra Charge / Notes")

    # ---------------- COMPUTES ----------------

    @api.depends("passenger_ids")
    def _compute_n_pax(self):
        for rec in self:
            rec.n_pax = len(rec.passenger_ids)

    @api.depends("brigade_id", "brigade_id.roster_ids",
                 "brigade_id.departure_ids.passenger_ids", "passenger_ids")
    def _compute_available_passenger_ids(self):
        for rec in self:
            if not rec.brigade_id:
                rec.available_passenger_ids = False
                continue

            all_roster = rec.brigade_id.roster_ids
            other_departures_passengers = rec.brigade_id.departure_ids.filtered(
                lambda d: d.id != rec.id
            ).mapped("passenger_ids")

            used = other_departures_passengers
            available = (all_roster - used) | rec.passenger_ids
            rec.available_passenger_ids = available

    # ---------------- WARNING ONLY ----------------

    @api.onchange("passenger_ids")
    def _onchange_passenger_ids_duplicates(self):
        """
        Warning only (no constraint). User can still save.
        """
        for rec in self:
            if not rec.brigade_id or not rec.passenger_ids:
                continue

            passenger_ids = rec.passenger_ids.ids
            Departure = self.env["gb.brigade.departure"]

            other_departures = Departure.search([
                ("brigade_id", "=", rec.brigade_id.id),
                ("id", "!=", rec.id),
                ("passenger_ids", "in", passenger_ids),
            ])

            if not other_departures:
                continue

            conflicts = {}
            for other in other_departures:
                common = other.passenger_ids.filtered(
                    lambda p: p.id in passenger_ids
                )
                for p in common:
                    conflicts.setdefault(
                        p.partner_id.name or p.display_name, []
                    ).append(
                        _("Departure: %(title)s (%(date)s)") % {
                            "title": other.title or "",
                            "date": fields.Datetime.to_string(
                                other.date_time_departure
                            ) if other.date_time_departure else "",
                        }
                    )

            if conflicts:
                lines = []
                for name, entries in conflicts.items():
                    lines.append(f"- {name}: " + "; ".join(entries))

                message = (
                    "These passengers already appear in another Departure of this brigade:\n"
                    + "\n".join(lines)
                )

                return {
                    "warning": {
                        "title": _("Passenger already in another Departure"),
                        "message": message,
                    }
                }

# ===========================================================
# Staff temporal
# ===========================================================

class GBBrigadeStaff(models.Model):
    _name = 'gb.brigade.staff'
    _description = 'Brigade Staff Assignment'
    _order = 'start_datetime, person_id'
    _rec_name = 'name'

    # Nombre “humano” que usaremos en checkboxes, tags, etc.
    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
    )

    brigade_id = fields.Many2one(
        'gb.brigade',
        string='Brigade',
        required=True,
        ondelete='cascade',
    )

    person_id = fields.Many2one(
        'res.partner',
        string='Person',
        required=True,
        help='Person (contact) assigned as staff member in this brigade.',
    )

    # Datos traídos desde el contacto
    gender = fields.Selection(
        related='person_id.gb_gender',
        string='Gender',
        readonly=True,
    )

    diet = fields.Char(
        related='person_id.gb_diet',
        string='Diet',
        readonly=True,
    )

    allergy = fields.Char(
        related='person_id.gb_allergy',
        string='Allergy',
        readonly=True,
    )

    professional_registration = fields.Char(
        string='Professional Registration',
        compute='_compute_professional_registration',
        store=False,
        readonly=True,
        help='Professional registration / eligibility information pulled from the contact.',
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
        help='Role of this person during the brigade.',
    )

    # Fechas propias de la brigada
    start_datetime = fields.Datetime(
        string='Start Date/Time',
        help='Date and time when this person starts working with the brigade.',
    )

    end_datetime = fields.Datetime(
        string='End Date/Time',
        help='Date and time when this person stops working with the brigade.',
    )

    # Campo antiguo (compatibilidad, opcional en vistas)
    diet_allergy_note = fields.Char(
        string='Diet / Allergy / Notes',
        help='Relevant dietary restrictions, allergies or short notes.',
    )

    internal_note = fields.Text(
        string='Internal Notes',
        help='Internal notes for GB staff (not shown externally).',
    )

    provider_id = fields.Many2one(
        'res.partner',
        string='Provider',
        help='Optional provider record, kept for backwards compatibility.',
    )

    @api.depends('person_id.gb_eligibility_ids', 'person_id.gb_eligibility_ids.name')
    def _compute_professional_registration(self):
        """Compute professional registration / eligibility from partner records."""
        for rec in self:
            elig_records = rec.person_id.gb_eligibility_ids
            if elig_records:
                rec.professional_registration = ", ".join(elig_records.mapped('name'))
            else:
                rec.professional_registration = False

    @api.depends('person_id', 'person_id.name', 'provider_id', 'provider_id.name', 'staff_role')
    def _compute_name(self):
        """Nombre amigable para staff: 'Juan Pérez (LEAD COORDINATOR 1)'."""
        selection_dict = dict(self._fields['staff_role'].selection)
        for rec in self:
            base = rec.person_id.name or rec.provider_id.name or ""
            role_label = selection_dict.get(rec.staff_role, rec.staff_role or "")
            if base and role_label:
                rec.name = f"{base} ({role_label})"
            else:
                rec.name = base or role_label or _("Staff #%s") % rec.id

    def name_get(self):
        res = []
        selection_dict = dict(self._fields['staff_role'].selection)
        for rec in self:
            base = rec.person_id.name or rec.provider_id.name or ""
            role_label = selection_dict.get(rec.staff_role, rec.staff_role or "")
            if base and role_label:
                name = f"{base} ({role_label})"
            else:
                name = base or role_label or _("Staff #%s") % rec.id
            res.append((rec.id, name))
        return res


# ===========================================================
# Activity Tag (for itinerary activities)
# ===========================================================

class GBActivityTag(models.Model):
    _name = "gb.activity.tag"
    _description = "Activity Tag / Type"
    _order = "name"
    
    name = fields.Char(string="Tag", required=True)
    color = fields.Integer(string="Color Index")

# ===========================================================
# Brigade Activity / Itinerary entry
# ===========================================================

class GBBrigadeActivity(models.Model):
    _name = "gb.brigade.activity"
    _description = "Global Brigades - Brigade Activity / Itinerary Entry"
    _order = "start_datetime, id"
    
    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        required=True,
        ondelete="cascade",
        help="Which brigade this activity belongs to.",
    )
    
    name = fields.Char(string="Nombre de la actividad", required=True)
    
    tag_ids = fields.Many2many(
        "gb.activity.tag",
        "gb_activity_tag_rel",
        "activity_id",
        "tag_id",
        string="Tipo de actividad",
        help="Labels / categories for this activity (clinic, travel, orientation, etc.).",
    )
    
    start_datetime = fields.Datetime(string="Inicio", help="Start datetime for this activity.")
    end_datetime = fields.Datetime(string="Fin", help="End datetime for this activity.")
    
    place = fields.Char(string="Lugar", help="Location where the activity takes place.")
    
    responsible_id = fields.Many2one(
        "res.partner",
        string="Responsable",
        help="Main person in charge of this activity.",
    )
    
    participant_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_activity_participant_rel",
        "activity_id",
        "roster_id",
        string="Participantes",
        help="Participants attending this activity.",
    )
    
    participant_count = fields.Integer(
        string="N°",
        compute="_compute_participant_count",
        store=False,
        help="How many participants are assigned to this activity.",
    )
    
    notes = fields.Text(string="Notas", help="Any notes / logistics / reminders for this activity.")
    
    @api.depends("participant_ids")
    def _compute_participant_count(self):
        for rec in self:
            rec.participant_count = len(rec.participant_ids)
    
    def action_add_all_participants(self):
        """Botón 'Todos': mete todo el roster de la brigada en la actividad."""
        for rec in self:
            if rec.brigade_id:
                all_roster = rec.brigade_id.roster_ids
                rec.participant_ids = [(6, 0, all_roster.ids)]
        return True
    
    def action_open_add_participants_wizard(self):
        """Botón 'Seleccionar': abre el wizard para marcar participantes manualmente."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Seleccionar Participantes"),
            "res_model": "gb.add.participants.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_activity_id": self.id},
        }

# ===========================================================
# Activity Tag (for itinerary activities)
# ===========================================================
class GBActivityTag(models.Model):
    _name = "gb.activity.tag"
    _description = "Activity Tag / Type"
    _order = "name"

    name = fields.Char(string="Tag", required=True)
    color = fields.Integer(string="Color Index")


# ===========================================================
# Brigada Activity / Itinerary entry
# ===========================================================
class GBBrigadeActivity(models.Model):
    _name = "gb.brigade.activity"
    _description = "Global Brigades - Brigade Activity / Itinerary Entry"
    _order = "start_datetime, id"

    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        required=True,
        ondelete="cascade",
        help="Which brigade this activity belongs to.",
    )

    name = fields.Char(
        string="Nombre de la actividad",
        required=True,
    )

    tag_ids = fields.Many2many(
        "gb.activity.tag",
        "gb_activity_tag_rel",
        "activity_id",
        "tag_id",
        string="Tipo de actividad",
        help="Labels / categories for this activity (clinic, travel, orientation, etc.).",
    )

    start_datetime = fields.Datetime(
        string="Inicio",
        help="Start datetime for this activity.",
    )

    end_datetime = fields.Datetime(
        string="Fin",
        help="End datetime for this activity.",
    )

    place = fields.Char(
        string="Lugar",
        help="Location where the activity takes place.",
    )

    responsible_id = fields.Many2one(
        "res.partner",
        string="Responsable",
        help="Main person in charge of this activity.",
    )

    participant_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_activity_participant_rel",
        "activity_id",
        "roster_id",
        string="Participantes",
        help="Participants attending this activity.",
    )

    participant_count = fields.Integer(
        string="N°",
        compute="_compute_participant_count",
        store=False,
        help="How many participants are assigned to this activity.",
    )

    notes = fields.Text(
        string="Notas",
        help="Any notes / logistics / reminders for this activity.",
    )

    @api.depends("participant_ids")
    def _compute_participant_count(self):
        for rec in self:
            rec.participant_count = len(rec.participant_ids)

    def action_add_all_participants(self):
        """Botón 'Todos': mete todo el roster de la brigada en la actividad."""
        for rec in self:
            if rec.brigade_id:
                all_roster = rec.brigade_id.roster_ids
                rec.participant_ids = [(6, 0, all_roster.ids)]
        return True

    def action_open_add_participants_wizard(self):
        """
        Botón 'Seleccionar': abre el wizard existente
        para marcar participantes manualmente.
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Seleccionar Participantes"),
            "res_model": "gb.add.participants.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_activity_id": self.id,
            },
        }
