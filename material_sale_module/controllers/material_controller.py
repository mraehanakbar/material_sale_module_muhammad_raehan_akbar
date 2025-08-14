# -*- coding: utf-8 -*-
import json
from odoo import http, _
from odoo.http import request

API_PARAM_KEY = 'material_registry.api_key'

class MaterialRegistryAPI(http.Controller):

    def _auth_ok(self):
        cfg_key = request.env['ir.config_parameter'].sudo().get_param(API_PARAM_KEY)
        given = request.httprequest.headers.get('X-API-Key')
        return bool(cfg_key) and (cfg_key == given)


    def _json(self, payload, status=200, headers=None):
        body = json.dumps(payload) if payload is not None else ""
        resp = request.make_response(body, headers=(headers or [('Content-Type', 'application/json')]))
        resp.status_code = status
        return resp

    def _unauthorized(self, msg="Unauthorized"):
        return self._json({"error": msg}, status=401)

    def _bad_request(self, msg):
        return self._json({"error": msg}, status=400)

    def _ok(self, payload, status=200):
        return self._json(payload, status=status)

    def _no_content(self):
        return self._json(None, status=204, headers=[])  

    def _serialize(self, rec):
        return {
            "id": rec.id,
            "code": rec.code,
            "name": rec.name,
            "material_type": rec.material_type,
            "buy_price": rec.buy_price,
            "supplier_id": rec.supplier_id.id if rec.supplier_id else False,
            "supplier_name": rec.supplier_id.name if rec.supplier_id else False,
            "create_date": rec.create_date and rec.create_date.isoformat(),
            "write_date": rec.write_date and rec.write_date.isoformat(),
        }

    def _validate_payload(self, vals, is_update=False):
        required = ["code", "name", "material_type", "buy_price", "supplier_id"]
        if not is_update:
            missing = [k for k in required if vals.get(k) in (None, "", False)]
            if missing:
                raise ValueError(_("Missing required fields: %s") % ", ".join(missing))

        if "buy_price" in vals and vals["buy_price"] is not None:
            try:
                price = float(vals["buy_price"])
            except Exception:
                raise ValueError(_("buy_price must be a number"))
            if price < 100:
                raise ValueError(_("Material Buy Price tidak boleh kurang dari 100."))

        if "material_type" in vals and vals["material_type"] not in ("fabric", "jeans", "cotton"):
            raise ValueError(_("material_type must be one of: fabric, jeans, cotton"))

        return True


    @http.route('/api/materials', auth='public', type='http', methods=['GET'], csrf=False)
    def list_materials(self, **params):
        if not self._auth_ok():
            return self._unauthorized()

        domain = []
        mtype = params.get('material_type')
        if mtype:
            domain.append(('material_type', '=', mtype))

        supplier_id = params.get('supplier_id')
        if supplier_id:
            try:
                supplier_id = int(supplier_id)
            except Exception:
                return self._bad_request("supplier_id must be integer")
            domain.append(('supplier_id', '=', supplier_id))

        limit = params.get('limit')
        offset = params.get('offset')
        try:
            limit = int(limit) if limit else 80
            offset = int(offset) if offset else 0
        except Exception:
            return self._bad_request("limit/offset must be integers")

        records = request.env['material.registry'].sudo().search(domain, limit=limit, offset=offset, order='id desc')
        data = [self._serialize(r) for r in records]
        return self._ok({"count": len(data), "results": data})

    @http.route('/api/materials/<int:material_id>', auth='public', type='http', methods=['GET'], csrf=False)
    def get_material(self, material_id, **kwargs):
        if not self._auth_ok():
            return self._unauthorized()

        rec = request.env['material.registry'].sudo().browse(material_id)
        if not rec.exists():
            return self._bad_request("Material not found")

        return self._ok(self._serialize(rec))

    @http.route('/api/materials', auth='public', type='http', methods=['POST'], csrf=False)
    def create_material(self, **kwargs):
        if not self._auth_ok():
            return self._unauthorized()

        try:
            payload = json.loads(request.httprequest.data or b"{}")
        except Exception:
            return self._bad_request("Invalid JSON")

        try:
            self._validate_payload(payload, is_update=False)
        except ValueError as e:
            return self._bad_request(str(e))

        vals = {
            "code": payload.get("code"),
            "name": payload.get("name"),
            "material_type": payload.get("material_type"),
            "buy_price": float(payload.get("buy_price")),
            "supplier_id": int(payload.get("supplier_id")),
        }
        try:
            rec = request.env['material.registry'].sudo().create(vals)
        except Exception as e:
            return self._bad_request(str(e))

        return self._ok(self._serialize(rec), status=201)

    @http.route('/api/materials/<int:material_id>', auth='public', type='http', methods=['PUT', 'PATCH'], csrf=False)
    def update_material(self, material_id, **kwargs):
        """PUT/PATCH /api/materials/<id>
        Body JSON: any of {code, name, material_type, buy_price, supplier_id}
        """
        if not self._auth_ok():
            return self._unauthorized()

        rec = request.env['material.registry'].sudo().browse(material_id)
        if not rec.exists():
            return self._bad_request("Material not found")

        try:
            payload = json.loads(request.httprequest.data or b"{}")
        except Exception:
            return self._bad_request("Invalid JSON")

        try:
            self._validate_payload(payload, is_update=True)
        except ValueError as e:
            return self._bad_request(str(e))

        vals = {}
        if "code" in payload: vals["code"] = payload["code"]
        if "name" in payload: vals["name"] = payload["name"]
        if "material_type" in payload: vals["material_type"] = payload["material_type"]
        if "buy_price" in payload: vals["buy_price"] = float(payload["buy_price"])
        if "supplier_id" in payload: vals["supplier_id"] = int(payload["supplier_id"])

        try:
            rec.write(vals)
        except Exception as e:
            return self._bad_request(str(e))

        return self._ok(self._serialize(rec))

    @http.route('/api/materials/<int:material_id>', auth='public', type='http', methods=['DELETE'], csrf=False)
    def delete_material(self, material_id, **kwargs):
        if not self._auth_ok():
            return self._unauthorized()

        rec = request.env['material.registry'].sudo().browse(material_id)
        if not rec.exists():
            return self._not_found("Material not found")

        try:
            rec.unlink()
        except Exception as e:
            return self._bad_request(str(e))

        return self._no_content()