# -*- coding: utf-8 -*-
import base64
from io import BytesIO

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class GBRosterImportWizard(models.TransientModel):
    _name = "gb.roster.import.wizard"
    _description = "Import Roster from Excel"

    brigade_id = fields.Many2one(
        "gb.brigade",
        string="Brigade",
        required=True,
        ondelete="cascade",
    )
    upload_file = fields.Binary(string="Excel File (.xlsx)", required=True)
    filename = fields.Char(string="Filename")

    create_missing_partners = fields.Boolean(
        string="Create contact if email not found",
        default=True,
    )
    update_existing_partners = fields.Boolean(
        string="Update contact data if email exists",
        default=False,
        help="If checked, updates partner name/phone/mobile from the Excel row.",
    )

    def _require_openpyxl(self):
        try:
            import openpyxl  # noqa: F401
        except Exception:
            raise UserError(_(
                "Missing python dependency: openpyxl.\n\n"
                "Install it on the server, for example:\n"
                "  sudo -u odoo -H /opt/odoo/venv/bin/pip install openpyxl\n"
            ))

    def _normalize_email(self, email):
        email = (email or "").strip()
        return email.lower()

    def action_import(self):
        self.ensure_one()
        self._require_openpyxl()

        if not self.upload_file:
            raise UserError(_("Please upload an Excel file."))

        # Lazy import after dependency check
        import openpyxl

        content = base64.b64decode(self.upload_file)
        try:
            wb = openpyxl.load_workbook(BytesIO(content), data_only=True)
        except Exception as e:
            raise UserError(_("Could not read the Excel file. Error: %s") % (e,))

        ws = wb.active

        # Read header
        header_row = []
        for cell in ws[1]:
            header_row.append((str(cell.value).strip() if cell.value is not None else "").strip())

        if not any(header_row):
            raise UserError(_("The Excel file seems empty (no header row found)."))

        # Map columns by normalized header names
        def norm(h):
            return (h or "").strip().lower()

        col_map = {norm(h): idx for idx, h in enumerate(header_row)}

        # Required: email
        if "email" not in col_map:
            raise UserError(_(
                "Missing required column: 'email'.\n\n"
                "Your header must include at least:\n"
                "  email\n\n"
                "Optional columns:\n"
                "  name, phone, mobile, brigade_role, sa\n"
            ))

        # Optional columns
        name_col = col_map.get("name")
        phone_col = col_map.get("phone")
        mobile_col = col_map.get("mobile")
        brigade_role_col = col_map.get("brigade_role")
        sa_col = col_map.get("sa")

        Partner = self.env["res.partner"].sudo()
        Roster = self.env["gb.brigade.roster"].sudo()

        created_partners = 0
        updated_partners = 0
        created_roster = 0
        skipped_existing = 0

        errors = []

        # Process rows starting from row 2
        for row_idx in range(2, ws.max_row + 1):
            row = ws[row_idx]
            email_raw = row[col_map["email"]].value if col_map["email"] < len(row) else None
            email = self._normalize_email(email_raw)

            # Skip blank lines
            if not email:
                # If entire row is blank -> skip silently
                if all((c.value is None or str(c.value).strip() == "") for c in row):
                    continue
                errors.append(_("Row %s: missing email") % row_idx)
                continue

            # Read optional fields
            name = (str(row[name_col].value).strip() if name_col is not None and row[name_col].value is not None else "").strip()
            phone = (str(row[phone_col].value).strip() if phone_col is not None and row[phone_col].value is not None else "").strip()
            mobile = (str(row[mobile_col].value).strip() if mobile_col is not None and row[mobile_col].value is not None else "").strip()

            brigade_role = (str(row[brigade_role_col].value).strip() if brigade_role_col is not None and row[brigade_role_col].value is not None else "").strip()
            sa = False
            if sa_col is not None and row[sa_col].value is not None:
                v = row[sa_col].value
                if isinstance(v, bool):
                    sa = v
                else:
                    sval = str(v).strip().lower()
                    sa = sval in ("1", "true", "yes", "y", "si", "sí")

            # Find partner by email
            partner = Partner.search([("email", "=", email)], limit=1)

            if not partner:
                if not self.create_missing_partners:
                    errors.append(_("Row %s: email '%s' not found in contacts and 'Create contact' is disabled")
                                  % (row_idx, email))
                    continue

                partner_vals = {
                    "name": name or email,
                    "email": email,
                }
                if phone:
                    partner_vals["phone"] = phone
                if mobile:
                    partner_vals["mobile"] = mobile

                partner = Partner.create(partner_vals)
                created_partners += 1
            else:
                if self.update_existing_partners:
                    upd = {}
                    if name and (partner.name or "").strip() != name:
                        upd["name"] = name
                    # Only set if provided (don’t wipe existing)
                    if phone and (partner.phone or "").strip() != phone:
                        upd["phone"] = phone
                    if mobile and (partner.mobile or "").strip() != mobile:
                        upd["mobile"] = mobile
                    if upd:
                        partner.write(upd)
                        updated_partners += 1

            # Avoid duplicate roster line for same brigade+partner
            existing = Roster.search([
                ("brigade_id", "=", self.brigade_id.id),
                ("partner_id", "=", partner.id),
            ], limit=1)

            if existing:
                skipped_existing += 1
                continue

            roster_vals = {
                "brigade_id": self.brigade_id.id,
                "partner_id": partner.id,
            }
            # Optional roster-only fields
            if brigade_role:
                roster_vals["brigade_role"] = brigade_role
            roster_vals["sa"] = sa

            Roster.create(roster_vals)
            created_roster += 1

        if errors:
            # Show only first 15 errors to avoid huge popups
            msg = _("Import finished with errors:\n\n- %s") % ("\n- ".join(errors[:15]))
            if len(errors) > 15:
                msg += _("\n\n(+%s more)") % (len(errors) - 15)
            raise UserError(msg)

        # Success notification
        message = _(
            "Roster import completed.\n"
            "- New contacts: %(cp)s\n"
            "- Updated contacts: %(up)s\n"
            "- Roster lines created: %(cr)s\n"
            "- Already existed (skipped): %(sk)s"
        ) % {
            "cp": created_partners,
            "up": updated_partners,
            "cr": created_roster,
            "sk": skipped_existing,
        }

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Import successful"),
                "message": message,
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
