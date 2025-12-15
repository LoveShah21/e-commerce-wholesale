# Vaitikan E-Commerce Platform - Developer Documentation

Welcome to the Vaitikan E-Commerce Platform API documentation. This comprehensive guide will help you integrate with our platform and build amazing applications.

## 📚 Documentation Index

### Getting Started

- **[Quick Start Guide](./QUICK_START.md)** - Get up and running in 5 minutes
  - Register a user
  - Make your first API call
  - Complete a basic workflow

### Core Documentation

- **[API Documentation](./API_DOCUMENTATION.md)** - Complete API reference

  - All endpoints with request/response examples
  - Error handling
  - Razorpay payment integration
  - Rate limiting and pagination

- **[Authentication Guide](./AUTHENTICATION_GUIDE.md)** - Security and authentication
  - JWT token management
  - Role-based access control
  - Security best practices
  - Complete code examples

### Additional Resources

- **[Database Design](./database_design.md)** - Database schema and relationships
- **[Fixture Documentation](../backend/database/fixtures/README.md)** - Sample data and testing

## 🚀 Quick Links

### For Developers

| Task                | Documentation                                                      |
| ------------------- | ------------------------------------------------------------------ |
| First API call      | [Quick Start](./QUICK_START.md)                                    |
| User authentication | [Authentication Guide](./AUTHENTICATION_GUIDE.md)                  |
| Product management  | [API Docs - Products](./API_DOCUMENTATION.md#product-management)   |
| Shopping cart       | [API Docs - Cart](./API_DOCUMENTATION.md#shopping-cart)            |
| Order processing    | [API Docs - Orders](./API_DOCUMENTATION.md#orders)                 |
| Payment integration | [API Docs - Razorpay](./API_DOCUMENTATION.md#razorpay-integration) |

### For Admins

| Task                 | Documentation                                                       |
| -------------------- | ------------------------------------------------------------------- |
| Dashboard analytics  | [API Docs - Dashboard](./API_DOCUMENTATION.md#dashboard--analytics) |
| Inventory management | [API Docs - Manufacturing](./API_DOCUMENTATION.md#manufacturing)    |
| Order management     | [API Docs - Orders](./API_DOCUMENTATION.md#orders)                  |
| Customer support     | [API Docs - Support](./API_DOCUMENTATION.md#support--feedback)      |

## 🏗️ Platform Overview

The Vaitikan E-Commerce Platform is a production-grade, API-first web application built with:

- **Backend**: Django 5.2 + Django REST Framework
- **Database**: MySQL 8.4
- **Authentication**: JWT (JSON Web Tokens)
- **Payment Gateway**: Razorpay
- **PDF Generation**: ReportLab

### Key Features

✅ **User Management**

- Role-based access control (Customer, Operator, Admin)
- JWT authentication with token refresh
- Secure password management

✅ **Product Catalog**

- Multi-variant products (fabric, color, pattern, sleeve, pocket)
- Size-based pricing with markups
- Stock management with reservations
- Image management

✅ **E-Commerce**

- Shopping cart with session persistence
- Order management with status tracking
- Two-stage payment (50% advance, 50% final)
- Invoice generation with GST

✅ **Manufacturing**

- Material requirements calculation
- Inventory management with reorder alerts
- Supplier management
- Manufacturing specifications

✅ **Customer Service**

- Inquiry and quotation system
- Complaint management
- Feedback and ratings

✅ **Analytics**

- Sales trends and metrics
- Low stock alerts
- Order statistics

## 🔐 Authentication

The API uses JWT (JSON Web Token) authentication. Here's a quick example:

```bash
# 1. Login
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Response: {"access": "token...", "refresh": "token..."}

# 2. Use access token
curl http://localhost:8000/api/products/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

See the [Authentication Guide](./AUTHENTICATION_GUIDE.md) for complete details.

## 💳 Payment Integration

The platform integrates with Razorpay for secure payment processing:

1. **Advance Payment**: 50% of order total at confirmation
2. **Final Payment**: Remaining 50% before dispatch

See the [Razorpay Integration Guide](./API_DOCUMENTATION.md#razorpay-integration) for implementation details.

## 📊 API Endpoints Overview

### Public Endpoints (No Authentication)

```
GET  /api/products/              # List products
GET  /api/products/{id}/         # Product details
POST /api/users/register/        # Register user
POST /api/users/login/           # Login
POST /api/users/token/refresh/   # Refresh token
```

### Customer Endpoints (Authentication Required)

```
GET  /api/cart/                  # View cart
POST /api/cart-items/            # Add to cart
POST /api/orders/                # Create order
GET  /api/orders/                # List orders
POST /api/payments/create/       # Create payment
POST /api/payments/verify/       # Verify payment
GET  /api/invoices/{id}/download/ # Download invoice
POST /api/support/inquiries/     # Submit inquiry
POST /api/support/complaints/    # Submit complaint
POST /api/support/feedback/      # Submit feedback
```

### Admin Endpoints (Admin Role Required)

```
POST /api/products/              # Create product
PUT  /api/products/{id}/         # Update product
GET  /api/dashboard/stats/       # Dashboard analytics
GET  /api/admin/orders/          # List all orders
PUT  /api/admin/orders/{id}/     # Update order status
POST /api/support/admin/inquiries/{id}/quotation-requests/ # Create quotation
```

### Operator Endpoints (Operator/Admin Role)

```
GET  /api/manufacturing/materials/     # List materials
POST /api/manufacturing/materials/     # Add material
PUT  /api/manufacturing/materials/{id}/quantity/ # Update quantity
GET  /api/manufacturing/inventory/     # Inventory view
GET  /api/manufacturing/inventory/alerts/ # Reorder alerts
```

## 🧪 Testing

### Test Credentials

**Customer Account**:

- Email: `customer@example.com`
- Password: `customer123`

**Admin Account**:

- Email: `admin@example.com`
- Password: `admin123`

**Operator Account**:

- Email: `operator@example.com`
- Password: `operator123`

### Razorpay Test Mode

**Test Card**:

- Card Number: `4111 1111 1111 1111`
- CVV: Any 3 digits
- Expiry: Any future date

## 📝 Code Examples

### JavaScript (Fetch API)

```javascript
// Login
const response = await fetch("http://localhost:8000/api/users/login/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "user@example.com",
    password: "password123",
  }),
});
const { access, refresh } = await response.json();

// Authenticated request
const products = await fetch("http://localhost:8000/api/products/", {
  headers: { Authorization: `Bearer ${access}` },
});
```

### Python (Requests)

```python
import requests

# Login
response = requests.post('http://localhost:8000/api/users/login/', json={
    'email': 'user@example.com',
    'password': 'password123'
})
tokens = response.json()

# Authenticated request
headers = {'Authorization': f'Bearer {tokens["access"]}'}
products = requests.get('http://localhost:8000/api/products/', headers=headers)
```

### cURL

```bash
# Login
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Authenticated request
curl http://localhost:8000/api/products/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🔧 Development Setup

### Prerequisites

- Python 3.11+
- MySQL 8.4+
- pip (Python package manager)

### Installation

```bash
# Clone repository
git clone https://github.com/vaitikan/ecommerce-platform.git
cd ecommerce-platform

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Configure database
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
python manage.py migrate

# Load sample data
python manage.py loaddata database/fixtures/*.json

# Run development server
python manage.py runserver
```

### Environment Variables

Create a `.env` file in the `backend` directory:

```env
# Database
DB_NAME=vaitikan_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Razorpay
RAZORPAY_KEY_ID=rzp_test_XXXXXXXXXXXXXXX
RAZORPAY_KEY_SECRET=XXXXXXXXXXXXXXXXXXXXXXXX
```

## 📖 API Versioning

Current API version: **v1.0**

The API follows semantic versioning. Breaking changes will result in a new major version.

## 🚦 Rate Limiting

API endpoints are rate-limited to prevent abuse:

- Authentication endpoints: 5 requests/minute
- Payment endpoints: 10 requests/minute
- General endpoints: 100 requests/minute

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

## 🐛 Error Handling

All errors follow a consistent format:

```json
{
  "error": "Error type",
  "message": "Human-readable error message",
  "details": {
    "field": ["Specific error details"]
  }
}
```

Common HTTP status codes:

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error

## 📞 Support

### Documentation Issues

If you find any issues with the documentation:

- Open an issue on GitHub
- Email: docs@vaitikan.com

### API Support

For API-related questions:

- Email: api-support@vaitikan.com
- Response time: Within 24 hours

### Bug Reports

Report bugs via:

- GitHub Issues: https://github.com/vaitikan/ecommerce-platform/issues
- Email: bugs@vaitikan.com

## 📄 License

This project is proprietary software. All rights reserved.

## 🔄 Changelog

### Version 1.0.0 (January 2024)

- Initial API release
- User authentication with JWT
- Product catalog management
- Shopping cart and orders
- Razorpay payment integration
- Invoice generation
- Manufacturing workflow
- Customer support features
- Admin dashboard and analytics

---

**Last Updated**: January 15, 2024  
**API Version**: 1.0  
**Documentation Version**: 1.0
