from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class MaterialRegistry(models.Model):
    _name = "material.registry"
    _description = "Material Registry"
    _order = "code, name"

    code = fields.Char("Material Code", required=True)
    name = fields.Char("Material Name", required=True)
    material_type = fields.Selection(
        [
            ("fabric", "Fabric"),
            ("jeans", "Jeans"),
            ("cotton", "Cotton"),
        ],
        string="Material Type",
        required=True,
    )
    buy_price = fields.Float("Material Buy Price", required=True, digits=(16, 2))
    supplier_id = fields.Many2one(
        "res.partner",
        string="Related Supplier",
        domain="[('supplier_rank','>',0)]",
        required=True,
    )

    _sql_constraints = [
        ("material_code_uniq", "unique(code)", "Material Code harus unik."),
    ]

    @api.constrains("buy_price")
    def _check_buy_price_minimum(self):
        for rec in self:
            if rec.buy_price is None:
                continue
            if rec.buy_price < 100:
                raise ValidationError(_("Material Buy Price tidak boleh kurang dari 100."))
