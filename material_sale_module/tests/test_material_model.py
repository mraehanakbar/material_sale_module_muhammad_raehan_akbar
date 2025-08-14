from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo.tests import tagged


@tagged('at_install')
class TestMaterialModel(TransactionCase):

    def setUp(self):
        super().setUp()
        self.supplier = self.env['res.partner'].create({
            'name': 'Supplier A',
            'supplier_rank': 1,
        })

    def _vals(self, **kw):
        base = {
            'code': 'MAT-001',
            'name': 'Kain Fabrik',
            'material_type': 'fabric',
            'buy_price': 150.0,
            'supplier_id': self.supplier.id,
        }
        base.update(kw)
        return base

    def test_01_create_ok(self):
        rec = self.env['material.registry'].create(self._vals())
        self.assertTrue(rec.id)
        self.assertEqual(rec.buy_price, 150.0)
        self.assertEqual(rec.material_type, 'fabric')

    def test_02_buy_price_min_constraint(self):
        with self.assertRaises(ValidationError):
            self.env['material.registry'].create(self._vals(buy_price=99.99))

    def test_03_required_name(self):
        with self.assertRaises(Exception):
            self.env['material.registry'].create(self._vals(name=False))

    def test_03b_required_supplier(self):
        with self.assertRaises(Exception):
            self.env['material.registry'].create(self._vals(supplier_id=False))

    def test_04_unique_code_constraint(self):
        self.env['material.registry'].create(self._vals(code='UNIQ-1'))
        with self.assertRaises(Exception):
            self.env['material.registry'].create(self._vals(code='UNIQ-1'))

    def test_05_update_material(self):
        rec = self.env['material.registry'].create(self._vals())
        rec.write({'buy_price': 200.0, 'material_type': 'jeans'})
        self.assertEqual(rec.buy_price, 200.0)
        self.assertEqual(rec.material_type, 'jeans')

    def test_06_delete_ok(self):
        rec = self.env['material.registry'].create(self._vals(code='DEL-1'))
        rec_id = rec.id
        ok = rec.unlink()
        self.assertTrue(ok)
        self.assertFalse(self.env['material.registry'].browse(rec_id).exists())
        self.assertEqual(self.env['material.registry'].search_count([('id', '=', rec_id)]), 0)
