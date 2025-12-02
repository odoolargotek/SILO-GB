# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class GBCommunity(models.Model):
    _name = 'gb.community'
    _description = 'Global Brigades Community'
    _order = 'province, district, corregimiento, name'

    # Nombre visible de la comunidad
    name = fields.Char(
        string='Community Name',
        required=True,
        help='Official community name as used by Global Brigades.'
    )

    # Código interno opcional (por si GB maneja códigos)
    code = fields.Char(
        string='Community Code',
        help='Internal code used to identify this community.'
    )

    # Localización
    province = fields.Char(
        string='Province',
        required=True,
        help='Province where the community is located.'
    )
    district = fields.Char(
        string='District',
        required=True,
        help='District where the community is located.'
    )
    corregimiento = fields.Char(
        string='Corregimiento',
        required=False,
        help='Corregimiento or similar administrative division.'
    )

    # Perfil de la comunidad
    profile_pdf = fields.Binary(
        string='Community Profile (PDF)',
        help='Upload a PDF document with the detailed community profile.'
    )
    profile_link = fields.Char(
        string='Profile Link (Drive / Web)',
        help='External link to Drive or another repository with the community profile.'
    )

    # Notas internas
    notes = fields.Text(
        string='Notes',
        help='Internal notes about this community.'
    )

    # Activo / archivo lógico
    active = fields.Boolean(
        string='Active',
        default=True,
        help='If unchecked, the community will be hidden without being deleted.'
    )

    _sql_constraints = [
        (
            'gb_community_unique_name_location',
            'unique(name, province, district, corregimiento)',
            'There is already a community with the same name and location (province/district/corregimiento).'
        ),
    ]
