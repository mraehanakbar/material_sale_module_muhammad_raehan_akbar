# -*- coding: utf-8 -*-
import json
from odoo.tests import HttpCase, tagged

API_PARAM_KEY = 'material_registry.api_key'
API_KEY = 'TEST_SECRET'

@tagged('post_install', '-at_install')
class TestMaterialAPI(HttpCase):

    def setUp(self):
        super().setUp()
        # Set API key untuk controller
        self.env['ir.config_parameter'].sudo().set_param(API_PARAM_KEY, API_KEY)

        # Seed data
        self.supplier = self.env['res.partner'].sudo().create({
            'name': 'API Supplier',
            'supplier_rank': 1,
        })
        self.material = self.env['material.registry'].sudo().create({
            'code': 'API-001',
            'name': 'Kain API',
            'material_type': 'fabric',
            'buy_price': 150.0,
            'supplier_id': self.supplier.id,
        })

        # Base URL absolut untuk requests.Session
        base = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        self._base = base or 'http://127.0.0.1:8069'

    def _headers(self, with_key=True):
        h = {}
        if with_key:
            h['X-API-Key'] = API_KEY
        return h

    def _json_body(self, resp):
        """Parse JSON dari requests.Response dengan aman."""
        txt = getattr(resp, 'text', None)
        if txt is None and hasattr(resp, 'content'):
            try:
                txt = resp.content.decode('utf-8', errors='ignore')
            except Exception:
                txt = ''
        return json.loads(txt) if txt else {}

    # ---------- GET ----------
    def test_01_auth_required(self):
        resp = self.url_open('/api/materials', headers={})
        self.assertEqual(resp.status_code, 401, "Harus 401 tanpa API key")

    def test_02_list_materials(self):
        resp = self.url_open('/api/materials', headers=self._headers())
        self.assertEqual(resp.status_code, 200)
        data = self._json_body(resp)
        self.assertIn('results', data)
        self.assertGreaterEqual(data.get('count', 0), 1)

    def test_03_get_detail(self):
        resp = self.url_open(f'/api/materials/{self.material.id}', headers=self._headers())
        self.assertEqual(resp.status_code, 200)
        data = self._json_body(resp)
        self.assertEqual(data['id'], self.material.id)
        self.assertEqual(data['code'], 'API-001')

    # ---------- POST (create) ----------
    def test_04_create_ok(self):
        payload = {
            'code': 'API-NEW',
            'name': 'Kain Baru',
            'material_type': 'cotton',
            'buy_price': 120.0,
            'supplier_id': self.supplier.id,
        }
        # url_open → POST jika data != None (route type='http')
        resp = self.url_open('/api/materials',
                             data=json.dumps(payload).encode('utf-8'),
                             headers=self._headers())
        self.assertEqual(resp.status_code, 201)
        data = self._json_body(resp)
        self.assertEqual(data['code'], 'API-NEW')
        self.assertEqual(data['material_type'], 'cotton')
        self.assertEqual(data['supplier_id'], self.supplier.id)

    def test_05_create_reject_price_lt_100(self):
        payload = {
            'code': 'API-BAD',
            'name': 'Salah',
            'material_type': 'jeans',
            'buy_price': 50.0,
            'supplier_id': self.supplier.id,
        }
        resp = self.url_open('/api/materials',
                             data=json.dumps(payload).encode('utf-8'),
                             headers=self._headers())
        self.assertEqual(resp.status_code, 400)
        err = self._json_body(resp)
        self.assertIn('error', err)

    # ---------- PATCH (update) ----------
    def test_06_update_ok(self):
        payload = {'buy_price': 220.0, 'material_type': 'jeans'}
        resp = self.opener.request(
            'PATCH',
            f'{self._base}/api/materials/{self.material.id}',
            data=json.dumps(payload).encode('utf-8'),
            headers=self._headers(),          # <-- penting!
        )
        self.assertEqual(resp.status_code, 200)
        data = self._json_body(resp)
        self.assertEqual(data['buy_price'], 220.0)
        self.assertEqual(data['material_type'], 'jeans')

    def test_07_update_reject_price_lt_100(self):
        payload = {'buy_price': 10.0}
        resp = self.opener.request(
            'PATCH',
            f'{self._base}/api/materials/{self.material.id}',
            data=json.dumps(payload).encode('utf-8'),
            headers=self._headers(),          # <-- penting!
        )
        self.assertEqual(resp.status_code, 400)
        err = self._json_body(resp)
        self.assertIn('error', err)

    # ---------- GET filter ----------
    def test_08_list_filter_by_type(self):
        self.env['material.registry'].sudo().create({
            'code': 'API-JEANS',
            'name': 'Kain Jeans',
            'material_type': 'jeans',
            'buy_price': 130.0,
            'supplier_id': self.supplier.id,
        })
        resp = self.url_open('/api/materials?material_type=jeans',
                             headers=self._headers())
        self.assertEqual(resp.status_code, 200)
        data = self._json_body(resp)
        self.assertGreaterEqual(data.get('count', 0), 1)
        for r in data['results']:
            self.assertEqual(r['material_type'], 'jeans')

    # ---------- DELETE ----------
    def test_09_delete_ok(self):
        rec = self.env['material.registry'].sudo().create({
            'code': 'API-DEL',
            'name': 'To Delete',
            'material_type': 'fabric',
            'buy_price': 150.0,
            'supplier_id': self.supplier.id,
        })
        resp = self.opener.request(
            'DELETE',
            f'{self._base}/api/materials/{rec.id}',
            headers=self._headers(),          # <-- penting!
        )
        self.assertEqual(resp.status_code, 204, "DELETE harus return 204 No Content")

        # konfirmasi sudah hilang (biasanya 404)
        resp2 = self.url_open(f'/api/materials/{rec.id}', headers=self._headers())
        self.assertIn(resp2.status_code, (404, 400))

    def test_10_delete_not_found(self):
        resp = self.opener.request(
            'DELETE',
            f'{self._base}/api/materials/9999999',
            headers=self._headers(),          # <-- penting!
        )
        self.assertIn(resp.status_code, (404, 400))
