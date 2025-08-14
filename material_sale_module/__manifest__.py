{
    "name": "Material Registry",
    "version": "14.0.1.0.0",
    "summary": "Registrasi Material untuk Penjualan + REST API",
    "author": "Raehan",
    "category": "Inventory",
    "depends": ["base",'purchase','account'],
    "data": [
        "security/ir.model.access.csv",
        "views/material_views.xml",
        "views/supplier_views.xml",
    ],
    "installable": True,
    "application": True,
}
