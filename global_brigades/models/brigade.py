# -*- coding: utf-8 -*-
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class GBBrigade(models.Model):
    _name = "gb.brigade"
    _description = "Global Brigades - Chapter / Brigade"
    _order = "id desc"

    # Identificación básica
    external_brigade_code = fields.Char(
        string="External Brigade Code",
        help="External reference / code from CRM or other system.",
    )

    brigade_code = fields.Char(
        string="BRIGADE CODE",
        readonly=True,
        copy=False,
        default="/",
    )

    name = fields.Char(string="CHAPTER NAME", required=True)

    arrival_date = fields.Date(string="Arrival Date")
    departure_date = fields.Date(string="Departure Date")

    # Estado operativo de la brigada
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

    # Tipo de brigada
    brigade_type = fields.Selection(
        [
            ("onsite", "In Person"),
            ("virtual", "Virtual"),
        ],
        string="Brigade Type",
        default="onsite",
        required=True,
        help="If set to Virtual, logistics sections (Transport, Hotels, Arrivals and Departures) "
             "should not be used for this brigade.",
    )

    # Restricciones
    brigade_restriction = fields.Selection(
        [
            ("darien_golfo", "Darien & Golfo de Mosquito"),
            ("este_darien", "Este y Darien"),
            ("solo_darien", "Solo Darien"),
            ("otros", "Otros"),
        ],
        string="Restrictions",
        help="Geographic / operational restrictions for this brigade.",
    )

    # Programa oficial de la brigada
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
        help="Main official program of this brigade.",
    )

    itinerary_link = fields.Char(
        string="Itinerary Link",
        help="Copy & paste link from GDrive or other.",
    )

    # Cliente asociado cuando el programa es Business
    business_client_id = fields.Many2one(
        "res.partner",
        string="Business Client",
        help="Client associated to this brigade when the Official Program is Business.",
    )

    # Link al Business Profile del cliente de negocio (solo lectura)
    business_profile_link = fields.Char(
        string="Business Profile Link",
        related="business_client_id.business_profile_link",
        readonly=True,
    )

    @api.onchange("brigade_program")
    def _onchange_brigade_program_business_client(self):
        """Limpiar el cliente si no es Business."""
        for record in self:
            if record.brigade_program != "business":
                record.business_client_id = False

    # Niveles / Tier de brigada
    brigade_tier = fields.Selection(
        [
            ("sustainable", "Sustainable"),
            ("empowered", "Empowered"),
            ("scaled", "Scaled"),
        ],
        string="Brigade Tier",
        help="Tier based on number of volunteers/students.\n"
             "- Sustainable: 14–25 volunteers\n"
             "- Empowered: 26–39 volunteers\n"
             "- Scaled: 40+ volunteers",
    )

    # Conteo de voluntarios / estudiantes
    volunteer_count = fields.Integer(
        string="Volunteers / Students",
        compute="_compute_volunteer_count",
        store=False,
        help="Number of volunteers / students in the roster.",
    )

    # Logo / Identidad visual
    university_logo = fields.Image(string="University Logo (image)")

    # Datos de compound / base
    compound_manager_id = fields.Many2one(
        "res.partner",
        string="COMPOUND SUPERVISOR",
    )
    arrival_time_compound = fields.Datetime(string="Arrival time to Compound")
    departure_time_compound = fields.Datetime(string="Departure time from Compound")

    # Coordinación
    coordinator_id = fields.Many2one(
        "res.partner",
        string="LEAD COORDINATOR",
    )
    program_associate_id = fields.Many2one(
        "res.partner",
        string="PROGRAM ADVISOR",
    )

    # Líderes de capítulo / universidad (pueden ser varios)
    chapter_leader_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_brigade_chapter_leader_rel",
        "brigade_id",
        "roster_id",
        string="Chapter Leader(s)",
        help="Roster members acting as Chapter Leader for this brigade.",
    )

    chapter_president_faculty_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_brigade_chapter_president_faculty_rel",
        "brigade_id",
        "roster_id",
        string="Chapter President / Faculty",
        help="Roster members acting as Chapter President or Faculty for this brigade.",
    )

    professor_chaperone_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_brigade_professor_chaperone_rel",
        "brigade_id",
        "roster_id",
        string="Professor / Chaperone",
        help="Roster members acting as Professors or Chaperones for this brigade.",
    )

    extra_info = fields.Text(
        string="Additional Information & Observations / Country Specific Section"
    )

    # Programas asociados a la brigada
    program_line_ids = fields.One2many(
        "gb.brigade.program",
        "brigade_id",
        string="Programs",
    )
    program_count = fields.Integer(
        string="Programs",
        compute="_compute_program_count",
        store=False,
    )

    # Roster / llegada / salida / staff
    roster_ids = fields.One2many(
        "gb.brigade.roster",
        "brigade_id",
        string="Roster",
    )
    arrival_ids = fields.One2many(
        "gb.brigade.arrival",
        "brigade_id",
        string="Arrivals",
    )
    departure_ids = fields.One2many(
        "gb.brigade.departure",
        "brigade_id",
        string="Departures",
    )
    staff_ids = fields.One2many(
        "gb.brigade.staff",
        "brigade_id",
        string="Temp Staff",
    )

    # ITINERARIO
    activity_ids = fields.One2many(
        "gb.brigade.activity",
        "brigade_id",
        string="Activities / Itinerary",
    )
    activity_count = fields.Integer(
        string="Activities",
        compute="_compute_activity_count",
        store=False,
    )

    # HOTEL / ROOMING LIST
    hotel_booking_ids = fields.One2many(
        "gb.brigade.hotel.booking",
        "brigade_id",
        string="Hotel Nights / Rooming",
    )

    # TRANSPORT
    transport_ids = fields.One2many(
        "gb.brigade.transport",
        "brigade_id",
        string="Transport Plan",
    )

    transport_count = fields.Integer(
        string="Transports",
        compute="_compute_transport_count",
        store=False,
    )

    _sql_constraints = [
        (
            "chapter_code_uniq",
            "unique(brigade_code)",
            "Brigade Code must be unique!",
        ),
    ]

    # ---------- COMPUTES ----------

    @api.depends("transport_ids")
    def _compute_transport_count(self):
        for rec in self:
            rec.transport_count = len(rec.transport_ids)

    @api.depends("program_line_ids")
    def _compute_program_count(self):
        for rec in self:
            rec.program_count = len(rec.program_line_ids)

    @api.depends("activity_ids")
    def _compute_activity_count(self):
        for rec in self:
            rec.activity_count = len(rec.activity_ids)

    @api.depends("roster_ids")
    def _compute_volunteer_count(self):
        for rec in self:
            rec.volunteer_count = len(rec.roster_ids)

    # ---------- REGLA NEGOCIO: brigada virtual sin logística ----------
    @api.constrains(
        "brigade_type",
        "transport_ids",
        "hotel_booking_ids",
        "arrival_ids",
        "departure_ids",
    )
    def _check_virtual_no_logistics(self):
        for rec in self:
            if rec.brigade_type == "virtual":
                if rec.transport_ids or rec.hotel_booking_ids or rec.arrival_ids or rec.departure_ids:
                    raise ValidationError(_(
                        "Virtual brigades cannot have Transport, Hotel, Arrivals or Departures records.\n"
                        "Remove those records or change the Brigade Type back to 'In Person'."
                    ))

    # ---------- CONTROL DE EDICIÓN DEL ITINERARY LINK ----------

    def write(self, vals):
        """Controla que el itinerary_link no se cambie sin usar el botón dedicado."""
        if "itinerary_link" in vals:
            for rec in self:
                old_link = rec.itinerary_link or False
                new_link = vals.get("itinerary_link") or False

                # Si no cambia realmente, nada que hacer
                if old_link == new_link:
                    continue

                # Primera vez: antes vacío, ahora con valor -> permitido
                if not old_link and new_link:
                    continue

                # Cambio posterior sin contexto especial -> bloquear
                if old_link and old_link != new_link and not self.env.context.get("force_itinerary_edit"):
                    raise ValidationError(_(
                        "The itinerary link is already set and cannot be changed directly.\n"
                        "Use the 'Edit Itinerary' button to modify it explicitly."
                    ))

        return super().write(vals)

    def action_open_itinerary_link(self):
        """Abre el itinerary_link en una nueva pestaña del navegador."""
        self.ensure_one()
        if not self.itinerary_link:
            raise UserError(_("There is no itinerary link set for this brigade."))
        return {
            "type": "ir.actions.act_url",
            "url": self.itinerary_link,
            "target": "new",
        }

    def action_edit_itinerary_link(self):
        """Recarga el formulario permitiendo editar el itinerary_link."""
        self.ensure_one()
        ctx = dict(self.env.context or {})
        ctx["force_itinerary_edit"] = True
        return {
            "type": "ir.actions.act_window",
            "name": _("Edit Itinerary Link"),
            "res_model": "gb.brigade",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
            "context": ctx,
        }

    # ---------- ASIGNACIÓN DE SECUENCIA ----------

    @api.model
    def create(self, vals):
        # Si no viene código o viene con el placeholder "/", tomamos de la secuencia
        code = vals.get("brigade_code") or "/"
        if code == "/":
            next_code = self.env["ir.sequence"].next_by_code("gb.brigade.code")
            if not next_code:
                raise ValidationError(_(
                    "Could not get sequence 'gb.brigade.code'. "
                    "Make sure sequence.xml is loaded in the manifest."
                ))
            vals["brigade_code"] = next_code
        return super().create(vals)
    # ---------- ASIGNACIÓN DE SECUENCIA ----------

    @api.model
    def create(self, vals):
        # Si no viene código o viene con el placeholder "/", tomamos de la secuencia
        code = vals.get("brigade_code") or "/"
        if code == "/":
            self.env.ref("base.sequence_code", raise_if_not_found=False)
            next_code = self.env["ir.sequence"].next_by_code("gb.brigade.code")
            if not next_code:
                raise ValidationError(_(
                    "No se pudo obtener la secuencia 'gb.brigade.code'. "
                    "Asegúrate de cargar 'sequence.xml' en el manifest."
                ))
            vals["brigade_code"] = next_code
        return super().create(vals)
    # -------------------------------------------------------------
    # BOTÓN: Abrir formulario desde la vista lista
    # -------------------------------------------------------------
    def open_form_action(self):
        """Abre el formulario de la brigada desde la vista lista."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Brigade",
            "res_model": "gb.brigade",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }

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
    diet = fields.Char(string="Diet / Restrictions")
    medical_condition = fields.Char(string="Medical Condition")
    medications = fields.Char(string="Medications")
    allergy = fields.Char(string="Allergies")

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
# Arrivals
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
    arrival_hotel_city_time = fields.Char(string="Arrival Hotel / City / Time")

    passenger_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_arrival_roster_rel",
        "arrival_id",
        "roster_id",
        string="Passengers",
    )

    # NUEVO: lista de pasajeros disponibles para el dominio
    available_passenger_ids = fields.Many2many(
        "gb.brigade.roster",
        compute="_compute_available_passenger_ids",
        string="Available Passengers",
        store=False,
    )

    n_pax = fields.Integer(
        string="# Pax",
        compute="_compute_n_pax",
        store=False,
        help="Calculated as number of selected passengers.",
    )

    special_transport = fields.Boolean(string="Special Transport Needed?")
    extra_charge = fields.Char(string="Extra Charge / Notes")

    @api.depends("passenger_ids")
    def _compute_n_pax(self):
        for rec in self:
            rec.n_pax = len(rec.passenger_ids or [])

    @api.depends(
        "brigade_id",
        "brigade_id.roster_ids",
        "brigade_id.arrival_ids.passenger_ids",
        "brigade_id.departure_ids.passenger_ids",
        "passenger_ids",
    )
    def _compute_available_passenger_ids(self):
        """
        Pasajeros disponibles = roster de la brigada
        - pasajeros ya usados en otros arrivals
        - pasajeros ya usados en cualquier departure
        + los pasajeros ya seleccionados en ESTE arrival (para poder editar).
        """
        for rec in self:
            if not rec.brigade_id:
                rec.available_passenger_ids = False
                continue

            all_roster = rec.brigade_id.roster_ids

            other_arrivals_passengers = rec.brigade_id.arrival_ids.filtered(
                lambda a: a.id != rec.id
            ).mapped("passenger_ids")

            departures_passengers = rec.brigade_id.departure_ids.mapped(
                "passenger_ids"
            )

            used = (other_arrivals_passengers | departures_passengers)
            available = (all_roster - used) | rec.passenger_ids
            rec.available_passenger_ids = available

    # --- AVISO (se puede dejar, no molesta) ---
    @api.onchange("passenger_ids")
    def _onchange_passenger_ids_duplicates(self):
        for rec in self:
            if not rec.brigade_id or not rec.passenger_ids:
                continue

            passenger_ids = rec.passenger_ids.ids

            Arrival = self.env["gb.brigade.arrival"]
            Departure = self.env["gb.brigade.departure"]

            other_arrivals = Arrival.search([
                ("brigade_id", "=", rec.brigade_id.id),
                ("id", "!=", rec.id),
                ("passenger_ids", "in", passenger_ids),
            ])
            other_departures = Departure.search([
                ("brigade_id", "=", rec.brigade_id.id),
                ("passenger_ids", "in", passenger_ids),
            ])

            if not (other_arrivals or other_departures):
                continue

            conflicts = {}
            for other in other_arrivals:
                common = other.passenger_ids.filtered(
                    lambda p: p.id in passenger_ids
                )
                for p in common:
                    conflicts.setdefault(p.partner_id.name or p.display_name, []).append(
                        _("Arrival: %(title)s (%(date)s)") % {
                            "title": other.title or "",
                            "date": fields.Datetime.to_string(other.date_time_arrival) if other.date_time_arrival else "",
                        }
                    )

            for other in other_departures:
                common = other.passenger_ids.filtered(
                    lambda p: p.id in passenger_ids
                )
                for p in common:
                    conflicts.setdefault(p.partner_id.name or p.display_name, []).append(
                        _("Departure: %(title)s (%(date)s)") % {
                            "title": other.title or "",
                            "date": fields.Datetime.to_string(other.date_time_departure) if other.date_time_departure else "",
                        }
                    )

            if conflicts:
                lines = []
                for name, entries in conflicts.items():
                    lines.append(f"- {name}: " + "; ".join(entries))
                message = _(
                    "Some passengers are already assigned to other flights in this brigade:\n%s"
                ) % "\n".join(lines)

                return {
                    "warning": {
                        "title": _("Passenger already assigned"),
                        "message": message,
                    }
                }

    # --- CONSTRAINT (seguro extra por si alguien fuerza datos vía API) ---
    @api.constrains("brigade_id", "passenger_ids")
    def _check_unique_passengers_in_brigade_arrivals(self):
        for rec in self:
            if not rec.brigade_id or not rec.passenger_ids:
                continue

            passenger_ids = rec.passenger_ids.ids
            Arrival = self.env["gb.brigade.arrival"]
            Departure = self.env["gb.brigade.departure"]

            other_arrivals = Arrival.search([
                ("brigade_id", "=", rec.brigade_id.id),
                ("id", "!=", rec.id),
                ("passenger_ids", "in", passenger_ids),
            ])
            other_departures = Departure.search([
                ("brigade_id", "=", rec.brigade_id.id),
                ("passenger_ids", "in", passenger_ids),
            ])

            if other_arrivals or other_departures:
                conflicts = {}
                for other in other_arrivals:
                    common = other.passenger_ids.filtered(
                        lambda p: p.id in passenger_ids
                    )
                    for p in common:
                        conflicts.setdefault(p.partner_id.name or p.display_name, []).append(
                            _("Arrival: %(title)s (%(date)s)") % {
                                "title": other.title or "",
                                "date": fields.Datetime.to_string(other.date_time_arrival) if other.date_time_arrival else "",
                            }
                        )
                for other in other_departures:
                    common = other.passenger_ids.filtered(
                        lambda p: p.id in passenger_ids
                    )
                    for p in common:
                        conflicts.setdefault(p.partner_id.name or p.display_name, []).append(
                            _("Departure: %(title)s (%(date)s)") % {
                                "title": other.title or "",
                                "date": fields.Datetime.to_string(other.date_time_departure) if other.date_time_departure else "",
                            }
                        )

                lines = []
                for name, entries in conflicts.items():
                    lines.append(f"- {name}: " + "; ".join(entries))
                raise ValidationError(_(
                    "The following passengers are already assigned to other flights in this brigade:\n%s"
                ) % "\n".join(lines))


# ===========================================================
# Departures
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
    departure_hotel_city = fields.Char(string="Departure Hotel / City")

    passenger_ids = fields.Many2many(
        "gb.brigade.roster",
        "gb_departure_roster_rel",
        "departure_id",
        "roster_id",
        string="Passengers",
    )

    # NUEVO: lista de pasajeros disponibles para el dominio
    available_passenger_ids = fields.Many2many(
        "gb.brigade.roster",
        compute="_compute_available_passenger_ids",
        string="Available Passengers",
        store=False,
    )

    n_pax = fields.Integer(
        string="# Pax",
        compute="_compute_n_pax",
        store=False,
        help="Calculated as number of selected passengers.",
    )

    special_transport = fields.Boolean(string="Special Transport Needed?")
    extra_charge = fields.Char(string="Extra Charge / Notes")

    @api.depends("passenger_ids")
    def _compute_n_pax(self):
        for rec in self:
            rec.n_pax = len(rec.passenger_ids or [])

    @api.depends(
        "brigade_id",
        "brigade_id.roster_ids",
        "brigade_id.arrival_ids.passenger_ids",
        "brigade_id.departure_ids.passenger_ids",
        "passenger_ids",
    )
    def _compute_available_passenger_ids(self):
        """
        Pasajeros disponibles = roster de la brigada
        - pasajeros ya usados en otros departures
        - pasajeros ya usados en cualquier arrival
        + los pasajeros ya seleccionados en ESTE departure.
        """
        for rec in self:
            if not rec.brigade_id:
                rec.available_passenger_ids = False
                continue

            all_roster = rec.brigade_id.roster_ids

            other_departures_passengers = rec.brigade_id.departure_ids.filtered(
                lambda d: d.id != rec.id
            ).mapped("passenger_ids")

            arrivals_passengers = rec.brigade_id.arrival_ids.mapped(
                "passenger_ids"
            )

            used = (other_departures_passengers | arrivals_passengers)
            available = (all_roster - used) | rec.passenger_ids
            rec.available_passenger_ids = available

    # --- AVISO (onchange) ---
    @api.onchange("passenger_ids")
    def _onchange_passenger_ids_duplicates(self):
        for rec in self:
            if not rec.brigade_id or not rec.passenger_ids:
                continue

            passenger_ids = rec.passenger_ids.ids

            Arrival = self.env["gb.brigade.arrival"]
            Departure = self.env["gb.brigade.departure"]

            other_departures = Departure.search([
                ("brigade_id", "=", rec.brigade_id.id),
                ("id", "!=", rec.id),
                ("passenger_ids", "in", passenger_ids),
            ])
            other_arrivals = Arrival.search([
                ("brigade_id", "=", rec.brigade_id.id),
                ("passenger_ids", "in", passenger_ids),
            ])

            if not (other_arrivals or other_departures):
                continue

            conflicts = {}
            for other in other_departures:
                common = other.passenger_ids.filtered(
                    lambda p: p.id in passenger_ids
                )
                for p in common:
                    conflicts.setdefault(p.partner_id.name or p.display_name, []).append(
                        _("Departure: %(title)s (%(date)s)") % {
                            "title": other.title or "",
                            "date": fields.Datetime.to_string(other.date_time_departure) if other.date_time_departure else "",
                        }
                    )

            for other in other_arrivals:
                common = other.passenger_ids.filtered(
                    lambda p: p.id in passenger_ids
                )
                for p in common:
                    conflicts.setdefault(p.partner_id.name or p.display_name, []).append(
                        _("Arrival: %(title)s (%(date)s)") % {
                            "title": other.title or "",
                            "date": fields.Datetime.to_string(other.date_time_arrival) if other.date_time_arrival else "",
                        }
                    )

            if conflicts:
                lines = []
                for name, entries in conflicts.items():
                    lines.append(f"- {name}: " + "; ".join(entries))
                message = _(
                    "Some passengers are already assigned to other flights in this brigade:\n%s"
                ) % "\n".join(lines)

                return {
                    "warning": {
                        "title": _("Passenger already assigned"),
                        "message": message,
                    }
                }

    # --- CONSTRAINT (seguro extra) ---
    @api.constrains("brigade_id", "passenger_ids")
    def _check_unique_passengers_in_brigade_departures(self):
        for rec in self:
            if not rec.brigade_id or not rec.passenger_ids:
                continue

            passenger_ids = rec.passenger_ids.ids
            Arrival = self.env["gb.brigade.arrival"]
            Departure = self.env["gb.brigade.departure"]

            other_departures = Departure.search([
                ("brigade_id", "=", rec.brigade_id.id),
                ("id", "!=", rec.id),
                ("passenger_ids", "in", passenger_ids),
            ])
            other_arrivals = Arrival.search([
                ("brigade_id", "=", rec.brigade_id.id),
                ("passenger_ids", "in", passenger_ids),
            ])

            if other_arrivals or other_departures:
                conflicts = {}
                for other in other_departures:
                    common = other.passenger_ids.filtered(
                        lambda p: p.id in passenger_ids
                    )
                    for p in common:
                        conflicts.setdefault(p.partner_id.name or p.display_name, []).append(
                            _("Departure: %(title)s (%(date)s)") % {
                                "title": other.title or "",
                                "date": fields.Datetime.to_string(other.date_time_departure) if other.date_time_departure else "",
                            }
                        )
                for other in other_arrivals:
                    common = other.passenger_ids.filtered(
                        lambda p: p.id in passenger_ids
                    )
                    for p in common:
                        conflicts.setdefault(p.partner_id.name or p.display_name, []).append(
                            _("Arrival: %(title)s (%(date)s)") % {
                                "title": other.title or "",
                                "date": fields.Datetime.to_string(other.date_time_arrival) if other.date_time_arrival else "",
                            }
                        )

                lines = []
                for name, entries in conflicts.items():
                    lines.append(f"- {name}: " + "; ".join(entries))
                raise ValidationError(_(
                    "The following passengers are already assigned to other flights in this brigade:\n%s"
                ) % "\n".join(lines))


# ===========================================================
# Staff temporal
# ===========================================================
class GBBrigadeStaff(models.Model):
    _name = 'gb.brigade.staff'
    _description = 'Brigade Staff Assignment'
    _order = 'start_datetime, person_id'
    _rec_name = 'name'  # <--- NUEVO

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

    start_datetime = fields.Datetime(
        string='Start Date/Time',
        help='Date and time when this person starts working with the brigade.',
    )

    end_datetime = fields.Datetime(
        string='End Date/Time',
        help='Date and time when this person stops working with the brigade.',
    )

    diet_allergy_note = fields.Char(
        string='Diet / Allergy / Notes',
        help='Relevant dietary restrictions, allergies or short notes.',
    )

    internal_note = fields.Char(
        string='Internal Note / Justification',
        help='Internal notes for GB staff (not shown externally).',
    )

    provider_id = fields.Many2one(
        'res.partner',
        string='Provider',
        help='Optional provider record, kept for backwards compatibility.',
    )

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
