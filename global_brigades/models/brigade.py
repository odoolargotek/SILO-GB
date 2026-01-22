# -*- coding: utf-8 -*-

# LT Brigade Module - Mejoras Odoo 18
# Largotek SRL - Juan Luis Garvía - www.largotek.com
# License: LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import base64
import io
from datetime import datetime

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    raise ImportError("Please install openpyxl: pip install openpyxl")


class GBBrigade(models.Model):
    _name = "gb.brigade"
    _description = "Global Brigades - Chapter / Brigade"
    _inherit = ['mail.thread']
    _order = "id desc"

    # =========================
    # IDENTIFICACIÓN BÁSICA
    # =========================
    external_brigade_code = fields.Char(
        string="Brigade Code",
        help="External reference / code from CRM or other system.",
        tracking=True,
    )

    brigade_code = fields.Char(
        string="Internal Code",
        readonly=True,
        copy=False,
        default="/",
        tracking=True,
    )

    name = fields.Char(
        string="CHAPTER NAME",
        required=True,
        tracking=True,
    )
    arrival_date = fields.Date(
        string="Arrival Date",
        tracking=True,
    )
    departure_date = fields.Date(
        string="Departure Date",
        tracking=True,
    )