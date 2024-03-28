{
    'name': "Realtime values",

    'summary': """Realtime values""",

    'description': """Realtime values are being gotten by MQTT protocol""",

    'author': "Huy Nguyen",
    'website': "http://localhost:8069",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'bus', 'web'],
    'application': True,
    'installable': True,

    'license': 'GPL-3',

    'post_init_hook': "_post_init_hook",

    'data': [
        'data/sensor_data.xml',
        'security/ir.model.access.csv',
        'views/sensor_views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'sensor/static/src/**/*',
        ],

        'sensor.assets_sensor_value': [
            # bootstrap
            ('include', 'web._assets_helpers'),
            'web/static/src/scss/pre_variables.scss',
            'web/static/lib/bootstrap/scss/_variables.scss',
            ('include', 'web._assets_bootstrap'),

            'web/static/src/libs/fontawesome/css/font-awesome.css',  # required for fa icons
            'web/static/src/legacy/js/promise_extension.js',  # required by boot.js
            'web/static/src/boot.js',  # odoo module system
            'web/static/src/env.js',  # required for services
            'web/static/src/session.js',  # expose __session_info__ containing server information
            'web/static/lib/owl/owl.js',  # owl library
            'web/static/lib/owl/odoo_module.js',  # to be able to import "@odoo/owl"
            'web/static/src/core/utils/functions.js',
            'web/static/src/core/browser/browser.js',
            'web/static/src/core/registry.js',
            'web/static/src/core/assets.js',
            'bus/static/src/workers/websocket_worker_utils.js',
            'bus/static/src/workers/websocket_worker.js',
            'sensor/static/src/**/*',
        ],
    },

    'demo': []
}
