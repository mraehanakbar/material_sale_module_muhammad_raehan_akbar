
# material_sale_module — Material Registry (Odoo 14)

This module adds a simple **Material Registry** with CRUD **REST-style endpoints** and unit tests.

## Features
- Model: `material.registry` (code, name, material_type, buy_price, supplier_id)
- Constraints:
  - All fields required
  - `buy_price >= 100`
  - `material_type ∈ {fabric, jeans, cotton}`
  - `code` unique
- Controllers (API):
  - `GET /api/materials` — list + filters
  - `GET /api/materials/<id>` — detail
  - `POST /api/materials` — create
  - `PATCH /api/materials/<id>` — update (partial)
  - `DELETE /api/materials/<id>` — delete (204)
- Unit tests:
  - Model (TransactionCase) — run at install
  - API (HttpCase) — run post-install

---

## 1) Dependencies & Installation

### Required modules
- `base`
- **Recommended:** `purchase` (provides `res.partner.supplier_rank` used for supplier filtering)

> If `supplier_rank` is missing in your environment, install the **Purchase** app.

### Install the addon
1. Place `material_sale_module/` in your Odoo addons path.
2. Update app list and install **Material Sale Module** (technical name: `material_sale_module`).

### Configure API key
Set a System Parameter (developer mode):
- **Key:** `material_registry.api_key`
- **Value:** your secret (example: `TEST_SECRET`)

All API endpoints require header: `X-API-Key: <your_secret>`

---

## 2) API Usage

### Authentication
All endpoints require request header:
```
X-API-Key: YOUR_SECRET
```

> These controllers are implemented with `type='http'`. Avoid forcing `Content-Type: application/json` if your server treats that as a JSON-RPC call. The examples below work out of the box. If you switch routes to `type='json'`, then include `Content-Type: application/json` in requests.

### Data shape
A `material` record looks like:
```json
{
  "id": 1,
  "code": "MAT-001",
  "name": "Kain Fabrik",
  "material_type": "fabric",
  "buy_price": 150.0,
  "supplier_id": 23,
  "supplier_name": "Supplier A",
  "create_date": "2025-08-14T05:00:00",
  "write_date": "2025-08-14T05:05:00"
}
```

### 2.1 List materials
**GET** `/api/materials`  
Query params (optional): `material_type`, `supplier_id`, `limit`, `offset`

**curl**
```bash
curl -i "{{BASE}}/api/materials" \
  -H "X-API-Key: YOUR_SECRET"
```

Filter by type:
```bash
curl -i "{{BASE}}/api/materials?material_type=jeans" \
  -H "X-API-Key: YOUR_SECRET"
```

### 2.2 Get one material
**GET** `/api/materials/<id>`

```bash
curl -i "{{BASE}}/api/materials/1" \
  -H "X-API-Key: YOUR_SECRET"
```

### 2.3 Create material
**POST** `/api/materials`  
All fields required: `code`, `name`, `material_type`, `buy_price` (>=100), `supplier_id`

```bash
curl -i "{{BASE}}/api/materials" \
  -H "X-API-Key: YOUR_SECRET" \
  --data-binary '{
    "code": "MAT-CURL",
    "name": "Kain Sample",
    "material_type": "cotton",
    "buy_price": 150,
    "supplier_id": 1
  }'
```

**Responses**
- 201 + JSON (created)
- 400 + `{"error": "..."}` on validation failure (e.g., price < 100, duplicate code)

### 2.4 Update material (partial)
**PATCH** `/api/materials/<id>`

```bash
curl -i -X PATCH "{{BASE}}/api/materials/1" \
  -H "X-API-Key: YOUR_SECRET" \
  --data-binary '{"buy_price": 200, "material_type": "jeans"}'
```

**Responses**
- 200 + JSON (updated)
- 400 on validation failure (e.g., `buy_price` < 100)
- 404 if not found

### 2.5 Delete material
**DELETE** `/api/materials/<id>`

```bash
curl -i -X DELETE "{{BASE}}/api/materials/1" \
  -H "X-API-Key: YOUR_SECRET"
```
**Response**: 204 No Content (empty body).

---

## 3) Postman (optional)

Set an environment with variables:
- `baseUrl` = `http://localhost:8069`
- `apiKey` = your secret

Common headers:
- `X-API-Key: {{apiKey}}`

Requests:
- `GET {{baseUrl}}/api/materials`
- `GET {{baseUrl}}/api/materials/{{id}}`
- `POST {{baseUrl}}/api/materials` (raw body JSON, **no** explicit `Content-Type` for `type='http'` routes)
- `PATCH {{baseUrl}}/api/materials/{{id}}`
- `DELETE {{baseUrl}}/api/materials/{{id}}`

---

## 4) Running Tests

### 4.1 Model tests (run at install)
Use a **fresh DB** so `at_install` tests run:
```bash
odoo-bin -d <new_db> -i material_sale_module \
  --test-enable --log-level=test --stop-after-init
```

### 4.2 API tests (run after install/update)
Run on an existing DB where the module is already installed:
```bash
odoo-bin -d <db_name> -u material_sale_module \
  --test-enable --test-tags /material_sale_module,post_install,-at_install \
  --log-level=test --stop-after-init
```

### 4.3 Run a single class or method
```bash
# one class
odoo-bin -d <db_name> -u material_sale_module --test-enable \
  --test-tags /material_sale_module:TestMaterialAPI \
  --log-level=test --stop-after-init

# one test method
odoo-bin -d <db_name> -u material_sale_module --test-enable \
  --test-tags /material_sale_module:TestMaterialAPI:test_06_update_ok \
  --log-level=test --stop-after-init
```

### 4.4 Troubleshooting
- **“0 tests”**: ensure folder is named `tests` (not `test`), contains `__init__.py`, and files match `test_*.py`.
- **401 on PATCH/DELETE**: header `X-API-Key` missing; include it explicitly on non-GET methods.
- **400 “Function declared as 'http' but called as 'json'”**: don’t force `Content-Type: application/json` unless your routes use `type='json'`.
- **supplier filter**: if using domain on `supplier_id` by `supplier_rank`, make sure the **Purchase** app is installed (it provides `supplier_rank`).

---

## 5) Notes
- Technical name: `material_sale_module`
- System parameter key for API auth: `material_registry.api_key`
- `material_type` allowed values: `fabric`, `jeans`, `cotton`
- Monetary values use float for simplicity; adapt to your accounting setup if needed.
