# -*- coding: utf-8 -*-

{
    "name": "Global Brigades",
    "version": "18.0.1.0.0",
    "summary": "Customizations for Global Brigades",
    "category": "Tools",
    "author": "Largotek SRL - Juan Luis Garvía",
    "website": "https://www.largotek.com",
    "license": "LGPL-3",
    "depends": [
        "base",
        "contacts",
    ],
    "data": [
        "data/sequence.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/brigade_views.xml",
        "views/add_participants_wizard_views.xml",
        "views/hotel_offer_views.xml",
        "views/transport_views.xml",
        "views/partner_brigades_views.xml",
        "views/brigade_hotel_booking_views.xml",
        "views/passenger_list_wizard_views.xml",
        "views/brigade_transport_views.xml",
        "views/community_views.xml",
        "views/brigade_report_views.xml",
        "views/brigade_extended_report_views.xml",
        "views/roster_import_views.xml",          # NUEVO: wizard import
        "views/brigade_roster_import_button.xml", # NUEVO: botón en pestaña ROSTER
        "data/gb_activity_tag_data.xml",
    ],
    "application": True,
    "installable": True,
}
