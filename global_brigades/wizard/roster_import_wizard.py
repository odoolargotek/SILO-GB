# -*- coding: utf-8 -*-

import base64
import io
from datetime import datetime, date

from odoo import fields, models, _
from odoo.exceptions import UserError


class GBRosterImportWizard(models.TransientModel):
    _name = "gb.roster.import.wizard"
    _description = "Import Roster from Excel"

    brigade_id = fields.Many2one("gb.brigade", string="Brigade", required=True)

    upload_file = fields.Binary(string="Excel File (.xlsx)", required=True)
    upload_filename = fields.Char(string="Filename")

    create_missing_contacts = fields.Boolean(
        string="Create contacts if not found",
        default=True,
    )
    update_existing_contacts = fields.Boolean(
        string="Update existing contacts",
        default=True,
    )

    def _to_bool(self, value):
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        s = str(value).strip().lower()
        if s in ("1", "true", "yes", "y", "si", "sí", "x"):
            return True
        if s in ("0", "false", "no", "n", ""):
            return False
        return None

    def _to_date(self, value):
        if not value:
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        s = str(value).strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y"):
            try:
                return datetime.strptime(s, fmt).date()
            except Exception:
                continue
        return None

    def _normalize_header(self, h):
        return (h or "").strip().lower()

    def _get_cell_str(self, v):
        if v is None:
            return ""
        return str(v).strip()

    def action_import(self):
        self.ensure_one()

        # Dependencia externa
        try:
            import openpyxl
        except Exception:
            raise UserError(_(
                "Missing Python library 'openpyxl'. Install it in the server environment:\n"
                "pip install openpyxl"
            ))

        if not self.upload_file:
            raise UserError(_("Please upload an Excel file (.xlsx)."))

        file_bytes = base64.b64decode(self.upload_file)
        try:
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        except Exception as e:
            raise UserError(_("Could not read the Excel file. Error: %s") % str(e))

        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            raise UserError(_("The Excel file is empty."))

        headers = [self._normalize_header(h) for h in rows[0]]

        def idx(*names):
            for n in names:
                n = self._normalize_header(n)
                if n in headers:
                    return headers.index(n)
            return None

        col = {
            "name": idx("name", "full name", "volunteer name", "participant", "nombre"),
            "email": idx("email", "e-mail", "mail", "correo"),
            "mobile": idx("mobile", "cell", "cellphone", "phone", "telefono", "teléfono"),
            "gender": idx("gender", "sexo", "género", "genero"),
            "birthdate": idx("birthdate", "date of birth", "dob", "fecha de nacimiento"),
            "spanish": idx("spanish speaker", "spanish", "habla español", "habla espanol"),
            "tshirt": idx("t-shirt size", "tshirt size", "shirt size", "talla polo", "talla camiseta"),
            "passport_no": idx("passport n°", "passport no", "passport", "pasaporte"),
            "passport_exp": idx("passport expiration date", "passport expiry", "passport exp", "vencimiento pasaporte"),
            "citizenship": idx("citizenship", "nationality", "nacionalidad"),
            "diet": idx("diet", "restrictions", "diet / restrictions"),
            "medical_condition": idx("medical condition", "condition", "condición médica", "condicion medica"),
            "medications": idx("medications", "medication", "medicina", "medicacion", "medicación"),
            "allergy": idx("allergies", "allergy", "alergias", "alergia"),
            "brigade_role": idx("brigade role", "role in brigade", "role", "rol"),
            "sa": idx("s.a.", "sa", "s a"),
            "emergency_name": idx("emergency contact", "emergency contact name", "contacto de emergencia"),
            "emergency_email": idx("emergency contact e-mail", "emergency contact email", "emergency email", "correo emergencia"),
        }

        if col["name"] is None and col["email"] is None:
            raise UserError(_("Your Excel must include at least a 'Name' or 'Email' column."))

        Partner = self.env["res.partner"].with_context(tracking_disable=True)
        Roster = self.env["gb.brigade.roster"].with_context(tracking_disable=True)

        def get(row, key):
            i = col.get(key)
            if i is None or i >= len(row):
                return None
            return row[i]

        def map_gender(v):
            if not v:
                return None
            s = str(v).strip().lower()
            if s in ("male", "m", "masculino", "hombre"):
                return "male"
            if s in ("female", "f", "femenino", "mujer"):
                return "female"
            if s in ("other", "o", "otro"):
                return "other"
            return None

        def map_tshirt(v):
            if not v:
                return None
            s = str(v).strip().lower().replace(" ", "")
            if s in ("xs", "s", "m", "l", "xl", "xxl", "2xl"):
                return "xxl" if s in ("xxl", "2xl") else s
            return None

        created_contacts = 0
        updated_contacts = 0
        created_roster = 0
        updated_roster = 0
        skipped = 0
        errors = []

        for r_index, row in enumerate(rows[1:], start=2):
            try:
                name = (self._get_cell_str(get(row, "name"))).strip()
                email = (self._get_cell_str(get(row, "email"))).strip().lower()

                if not name and not email:
                    skipped += 1
                    continue

                partner = False
                if email:
                    partner = Partner.search([("email", "=", email)], limit=1)
                if not partner and name:
                    partner = Partner.search([("name", "=", name)], limit=1)

                if not partner and not self.create_missing_contacts:
                    skipped += 1
                    continue

                vals_partner = {}
                if name:
                    vals_partner["name"] = name
                if email:
                    vals_partner["email"] = email

                mobile = (self._get_cell_str(get(row, "mobile"))).strip()
                if mobile:
                    vals_partner["mobile"] = mobile

                g = map_gender(get(row, "gender"))
                if g:
                    vals_partner["gb_gender"] = g

                bd = self._to_date(get(row, "birthdate"))
                if bd:
                    vals_partner["gb_birthdate"] = bd

                sp = self._to_bool(get(row, "spanish"))
                if sp is not None:
                    vals_partner["gb_spanish_speaker"] = sp

                ts = map_tshirt(get(row, "tshirt"))
                if ts:
                    vals_partner["gb_tshirt_size"] = ts

                pno = (self._get_cell_str(get(row, "passport_no"))).strip()
                if pno:
                    vals_partner["gb_passport_no"] = pno

                pexp = self._to_date(get(row, "passport_exp"))
                if pexp:
                    vals_partner["gb_passport_expiry"] = pexp

                cit = (self._get_cell_str(get(row, "citizenship"))).strip()
                if cit:
                    vals_partner["gb_citizenship"] = cit

                diet = (self._get_cell_str(get(row, "diet"))).strip()
                if diet:
                    vals_partner["gb_diet"] = diet

                mc = (self._get_cell_str(get(row, "medical_condition"))).strip()
                if mc:
                    vals_partner["gb_medical_condition"] = mc

                meds = (self._get_cell_str(get(row, "medications"))).strip()
                if meds:
                    vals_partner["gb_medications"] = meds

                alg = (self._get_cell_str(get(row, "allergy"))).strip()
                if alg:
                    vals_partner["gb_allergy"] = alg

                if partner:
                    if self.update_existing_contacts and vals_partner:
                        partner.write(vals_partner)
                        updated_contacts += 1
                else:
                    partner = Partner.create(vals_partner)
                    created_contacts += 1

                # Emergency contact (optional)
                emergency_partner = False
                e_name = (self._get_cell_str(get(row, "emergency_name"))).strip()
                e_email = (self._get_cell_str(get(row, "emergency_email"))).strip().lower()

                if e_name or e_email:
                    if e_email:
                        emergency_partner = Partner.search([("email", "=", e_email)], limit=1)
                    if not emergency_partner and e_name:
                        emergency_partner = Partner.search([("name", "=", e_name)], limit=1)
                    if not emergency_partner:
                        emergency_partner = Partner.create({
                            "name": e_name or e_email,
                            "email": e_email or False
                        })

                    # OJO: este campo debe existir en partner.py (gb_emergency_contact_id)
                    if getattr(partner, "gb_emergency_contact_id", False) != emergency_partner:
                        partner.write({"gb_emergency_contact_id": emergency_partner.id})

                roster_line = Roster.search(
                    [("brigade_id", "=", self.brigade_id.id), ("partner_id", "=", partner.id)],
                    limit=1
                )

                vals_roster = {}
                role = (self._get_cell_str(get(row, "brigade_role"))).strip()
                if role:
                    vals_roster["brigade_role"] = role

                sa_val = self._to_bool(get(row, "sa"))
                if sa_val is not None:
                    vals_roster["sa"] = sa_val

                if emergency_partner:
                    vals_roster["emergency_contact_id"] = emergency_partner.id

                if roster_line:
                    if vals_roster:
                        roster_line.write(vals_roster)
                        updated_roster += 1
                    else:
                        skipped += 1
                else:
                    vals_roster.update({
                        "brigade_id": self.brigade_id.id,
                        "partner_id": partner.id
                    })
                    Roster.create(vals_roster)
                    created_roster += 1

            except Exception as e:
                errors.append(_("Row %s: %s") % (r_index, str(e)))

        msg = _(
            "Import finished.\n"
            "- Contacts created: %(cc)s\n"
            "- Contacts updated: %(cu)s\n"
            "- Roster lines created: %(rc)s\n"
            "- Roster lines updated: %(ru)s\n"
            "- Skipped: %(sk)s\n"
        ) % {
            "cc": created_contacts,
            "cu": updated_contacts,
            "rc": created_roster,
            "ru": updated_roster,
            "sk": skipped,
        }

        if errors:
            msg += _("\nErrors:\n- ") + "\n- ".join(errors[:50])
            if len(errors) > 50:
                msg += _("\n... (%s more)") % (len(errors) - 50)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Roster Import"),
                "message": msg,
                "type": "success" if not errors else "warning",
                "sticky": True if errors else False,
            },
        }
