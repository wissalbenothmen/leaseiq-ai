# LeaseIQ AI - API Reference

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

All endpoints (except `/auth/register` and `/auth/login`) require Bearer token authentication.

### Header Format
```
Authorization: Bearer <access_token>
```

### Token Duration
Tokens expire after 480 minutes (8 hours). Refresh by logging in again.

---

## Authentication Endpoints

### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Response (201 Created)**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "tenant",
  "is_active": "true",
  "created_at": "2026-04-25T10:30:00"
}
```

### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecurePass123!
```

**Response (200 OK)**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "tenant",
    "is_active": "true",
    "created_at": "2026-04-25T10:30:00"
  }
}
```

### Get Current User
```http
GET /auth/me
Authorization: Bearer <token>
```

**Response (200 OK)**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "tenant",
  "is_active": "true",
  "created_at": "2026-04-25T10:30:00"
}
```

---

## Lease Endpoints

### Create Lease
```http
POST /leases
Authorization: Bearer <token>
Content-Type: application/json

{
  "property_address": "123 Main St, New York, NY",
  "tenant_name": "Acme Corp",
  "landlord_name": "Landlord LLC",
  "lease_type": "gross",
  "term_start": "2020-01-01",
  "term_end": "2025-12-31",
  "base_rent": 5000.00,
  "rent_escalation_pct": 3.0,
  "suite_number": "100",
  "square_footage": 5000.0,
  "notes": "Optional notes"
}
```

**Response (201 Created)**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "property_address": "123 Main St, New York, NY",
  "tenant_name": "Acme Corp",
  "landlord_name": "Landlord LLC",
  "lease_type": "gross",
  "term_start": "2020-01-01",
  "term_end": "2025-12-31",
  "base_rent": 5000.00,
  "rent_escalation_pct": 3.0,
  "status": "active",
  "suite_number": "100",
  "square_footage": 5000.0,
  "created_at": "2026-04-25T10:30:00",
  "updated_at": "2026-04-25T10:30:00"
}
```

### List Leases
```http
GET /leases?status=active&tenant_name=Acme&skip=0&limit=50
Authorization: Bearer <token>
```

**Query Parameters**
- `status` (optional): active, expired, pending, terminated
- `tenant_name` (optional): Filter by tenant name (partial match)
- `skip` (optional): Pagination offset (default: 0)
- `limit` (optional): Results per page (default: 50, max: 500)

**Response (200 OK)**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "property_address": "123 Main St, New York, NY",
    "tenant_name": "Acme Corp",
    "landlord_name": "Landlord LLC",
    "lease_type": "gross",
    "term_start": "2020-01-01",
    "term_end": "2025-12-31",
    "status": "active",
    "square_footage": 5000.0
  }
]
```

### Get Lease Details
```http
GET /leases/{lease_id}
Authorization: Bearer <token>
```

**Response (200 OK)** - Same as Create Lease response

### Update Lease
```http
PATCH /leases/{lease_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "base_rent": 5500.00,
  "rent_escalation_pct": 3.5,
  "status": "expired"
}
```

**Response (200 OK)** - Updated lease object

### Delete Lease
```http
DELETE /leases/{lease_id}
Authorization: Bearer <token>
```

**Response (204 No Content)**

---

## Clause Endpoints

### Create Clause
```http
POST /clauses
Authorization: Bearer <token>
Content-Type: application/json

{
  "lease_id": "550e8400-e29b-41d4-a716-446655440001",
  "clause_type": "personal_guarantee",
  "extracted_text": "Tenant guarantees all lease obligations...",
  "risk_score": 85,
  "confidence_score": 0.95,
  "extraction_json": {
    "parties_bound": ["Individual Owner"],
    "cap_amount": null,
    "scope": "all obligations"
  }
}
```

**Response (201 Created)**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "lease_id": "550e8400-e29b-41d4-a716-446655440001",
  "clause_type": "personal_guarantee",
  "extracted_text": "Tenant guarantees all lease obligations...",
  "risk_score": 85,
  "risk_factors": ["No cap on guarantee", "Indefinite duration"],
  "landlord_favorable": "true",
  "tenant_favorable": "false",
  "confidence_score": 0.95,
  "created_at": "2026-04-25T10:30:00"
}
```

### List Clauses by Lease
```http
GET /clauses/lease/{lease_id}?clause_type=personal_guarantee&min_risk=70&max_risk=100&skip=0&limit=50
Authorization: Bearer <token>
```

**Query Parameters**
- `clause_type` (optional): Filter by clause type
- `min_risk` (optional): Minimum risk score (default: 0)
- `max_risk` (optional): Maximum risk score (default: 100)
- `skip` (optional): Pagination offset (default: 0)
- `limit` (optional): Results per page (default: 50, max: 500)

**Response (200 OK)**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "clause_type": "personal_guarantee",
    "risk_score": 85,
    "landlord_favorable": "true",
    "tenant_favorable": "false",
    "confidence_score": 0.95
  }
]
```

### Get Clause Details
```http
GET /clauses/{clause_id}
Authorization: Bearer <token>
```

**Response (200 OK)** - Same as Create Clause response

### Update Clause
```http
PATCH /clauses/{clause_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "risk_score": 90,
  "landlord_favorable": "true"
}
```

**Response (200 OK)** - Updated clause object

---

## Obligation Endpoints

### Create Obligation
```http
POST /obligations
Authorization: Bearer <token>
Content-Type: application/json

{
  "lease_id": "550e8400-e29b-41d4-a716-446655440001",
  "obligation_type": "rent_payment",
  "due_date": "2026-05-01",
  "recurrence": "monthly",
  "amount": 5000.00,
  "description": "Monthly base rent",
  "responsible_party": "Tenant"
}
```

**Response (201 Created)**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "lease_id": "550e8400-e29b-41d4-a716-446655440001",
  "obligation_type": "rent_payment",
  "due_date": "2026-05-01",
  "recurrence": "monthly",
  "status": "pending",
  "amount": 5000.00,
  "description": "Monthly base rent",
  "responsible_party": "Tenant",
  "created_at": "2026-04-25T10:30:00"
}
```

### List Obligations by Lease
```http
GET /obligations/lease/{lease_id}?status=pending&obligation_type=rent_payment&skip=0&limit=50
Authorization: Bearer <token>
```

**Query Parameters**
- `status` (optional): pending, completed, overdue
- `obligation_type` (optional): Filter by obligation type
- `skip` (optional): Pagination offset
- `limit` (optional): Results per page

**Response (200 OK)**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "obligation_type": "rent_payment",
    "due_date": "2026-05-01",
    "recurrence": "monthly",
    "status": "pending",
    "amount": 5000.00
  }
]
```

### Get Overdue Obligations
```http
GET /obligations/overdue
Authorization: Bearer <token>
```

**Response (200 OK)** - Array of overdue obligations

### Get Upcoming Obligations
```http
GET /obligations/upcoming?days=30
Authorization: Bearer <token>
```

**Query Parameters**
- `days` (optional): Threshold days (default: 30, max: 365)

**Response (200 OK)** - Array of upcoming obligations

### Get Obligation Details
```http
GET /obligations/{obligation_id}
Authorization: Bearer <token>
```

**Response (200 OK)** - Same as Create Obligation response

### Update Obligation
```http
PATCH /obligations/{obligation_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "completed",
  "due_date": "2026-06-01"
}
```

**Response (200 OK)** - Updated obligation object

### Mark Obligation Complete
```http
POST /obligations/{obligation_id}/complete
Authorization: Bearer <token>
```

**Response (200 OK)** - Updated obligation with status="completed"

---

## Critical Date Endpoints

### Create Critical Date
```http
POST /critical-dates
Authorization: Bearer <token>
Content-Type: application/json

{
  "lease_id": "550e8400-e29b-41d4-a716-446655440001",
  "date_type": "renewal_option",
  "date_value": "2025-12-31",
  "days_until": 250
}
```

**Response (201 Created)**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "lease_id": "550e8400-e29b-41d4-a716-446655440001",
  "date_type": "renewal_option",
  "date_value": "2025-12-31",
  "days_until": 250,
  "alert_sent": "false",
  "created_at": "2026-04-25T10:30:00"
}
```

### List Critical Dates by Lease
```http
GET /critical-dates/lease/{lease_id}?date_type=renewal_option&skip=0&limit=50
Authorization: Bearer <token>
```

**Query Parameters**
- `date_type` (optional): expiry, renewal_option, rent_review, option_exercise, notice_deadline
- `skip` (optional): Pagination offset
- `limit` (optional): Results per page

**Response (200 OK)**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440004",
    "date_type": "renewal_option",
    "date_value": "2025-12-31",
    "days_until": 250,
    "alert_sent": "false"
  }
]
```

### Get Upcoming Critical Dates
```http
GET /critical-dates/upcoming/portfolio?days=90
Authorization: Bearer <token>
```

**Query Parameters**
- `days` (optional): Threshold days (default: 90, max: 365)

**Response (200 OK)** - Array of upcoming critical dates

### Get Critical Date Details
```http
GET /critical-dates/{critical_date_id}
Authorization: Bearer <token>
```

**Response (200 OK)** - Same as Create Critical Date response

### Update Critical Date
```http
PATCH /critical-dates/{critical_date_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "alert_sent": "true"
}
```

**Response (200 OK)** - Updated critical date object

---

## Analytics Endpoints

### Get Portfolio Risk Summary
```http
GET /analytics/portfolio/risk-summary
Authorization: Bearer <token>
```

**Response (200 OK)**
```json
{
  "summary": [
    {
      "clause_type": "personal_guarantee",
      "avg_risk_score": 82.5,
      "clause_count": 12
    },
    {
      "clause_type": "cam_charges",
      "avg_risk_score": 68.3,
      "clause_count": 25
    }
  ]
}
```

### Get Expiring Leases
```http
GET /analytics/portfolio/expiring-leases?days=365
Authorization: Bearer <token>
```

**Query Parameters**
- `days` (optional): Threshold days (default: 365, max: 3650)

**Response (200 OK)**
```json
{
  "expiring_count": 8,
  "leases": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "tenant_name": "Acme Corp",
      "property_address": "123 Main St, New York, NY",
      "term_end": "2025-12-31",
      "days_until_expiry": 250
    }
  ]
}
```

### Get Obligation Compliance
```http
GET /analytics/portfolio/obligation-compliance
Authorization: Bearer <token>
```

**Response (200 OK)**
```json
{
  "total_obligations": 245,
  "completed": 198,
  "compliance_rate": 80.82,
  "overdue_count": 5,
  "upcoming_30_days": 23
}
```

### Get Lease Risk Breakdown
```http
GET /analytics/lease/{lease_id}/risk-breakdown
Authorization: Bearer <token>
```

**Response (200 OK)**
```json
{
  "lease_id": "550e8400-e29b-41d4-a716-446655440001",
  "total_clauses": 18,
  "avg_risk_score": 52.3,
  "high_risk_count": 3,
  "medium_risk_count": 7,
  "low_risk_count": 8,
  "clauses": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "clause_type": "personal_guarantee",
      "risk_score": 85,
      "landlord_favorable": "true",
      "tenant_favorable": "false"
    }
  ]
}
```

### Get Lease Status Distribution
```http
GET /analytics/portfolio/lease-status-distribution
Authorization: Bearer <token>
```

**Response (200 OK)**
```json
{
  "distribution": [
    {
      "status": "active",
      "count": 87
    },
    {
      "status": "expired",
      "count": 12
    },
    {
      "status": "pending",
      "count": 5
    }
  ]
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request data"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Lease not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

- Default: 100 requests per minute per IP
- Authentication endpoints: 10 requests per minute
- Bulk operations: 5 requests per minute

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1714041600
```

---

## Pagination

All list endpoints support cursor-based pagination:

```http
GET /leases?skip=0&limit=50
```

- `skip`: Offset from start (default: 0)
- `limit`: Results per page (default: 50, max: 500)

---

## API Documentation

Interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

---

**Last Updated:** April 2026 | **API Version:** 1.0.0
