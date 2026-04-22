# -*- coding: utf-8 -*-
{
    "name": "Global Brigades",
    "version": "18.0.1.0.8",
    "summary": "Customizations for Global Brigades",
    "description": """
Logistics and volunteer management for Global Brigades:
- Planning and tracking brigades and trips
- Managing volunteers, hotels and transport
- Community visit coordination and reports
""",
    "category": "Tools",
    "author": "Largotek SRL",
    "website": "https://largotek.com",
    "license": "LGPL-3",
    "depends": [
        "base",
        "contacts",
        "mail",
    ],
    "data": [
        "data/sequence.xml",
        "data/gb_brigade_role_data.xml",
        "data/mail_template_sa_notification.xml",
        "security/security.xml",
        "security/security_rules.xml",
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
        "data/gb_activity_tag_data.xml",
        "views/roster_import_wizard_views.xml",
        "views/brigade_general_report_views.xml",
        "views/brigade_rooming_report_views.xml",
        "views/brigade_transport_report_views.xml",
        "views/sa_notification_brigade_view.xml",
        "views/brigade_detailed_report_views.xml",
        "data/paperformat_landscape.xml",
        "views/brigade_roster_report_views.xml",
        "data/brigade_detailed_report_action.xml",
    ],
    "images": ["static/description/icon.png"],
    "application": True,
    "installable": True,
}