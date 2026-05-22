{
    'name': 'KPM Villa Management',
    'version': '18.0.1.0.0',
    'category': 'Real Estate',
    'summary': 'Comprehensive Villa Rental & Revenue Management',
    'description': """
KPM Villa Management System
============================
* Villa Master with Kanban & Status tracking
* Rent Agreement Management with Sequences
* Rent Payment Tracking with inline editable lines
* Water Bill Split Management (Equal & Manual)
* Expense Management with Pivot & Graph views
* Revenue Dashboard with KPI cards
* Mobile-friendly Website Frontend
* QWeb PDF Reports
    """,
    'author': 'KPM',
    'website': 'https://kpm.com',
    'depends': ['base', 'mail', 'website', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/kpm_villa_views.xml',
        'views/kpm_villa_rent_views.xml',
        'views/kpm_villa_water_bill_views.xml',
        'views/kpm_villa_expense_views.xml',
        'views/kpm_villa_dashboard_views.xml',
        'views/kpm_villa_menu.xml',
        'report/kpm_villa_reports.xml',
        'report/kpm_villa_report_templates.xml',
        'views/website_templates.xml',
        'views/website_edit_templates.xml',
        'views/website_list_templates.xml',
        'views/res_partner_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'kpm_villa/static/src/scss/villa_backend.scss',
            'kpm_villa/static/src/xml/villa_dashboard.xml',
            'kpm_villa/static/src/js/villa_dashboard.js',
        ],
        'web.assets_frontend': [
            'kpm_villa/static/src/scss/villa_website.scss',
            'kpm_villa/static/src/js/villa_website.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
}
