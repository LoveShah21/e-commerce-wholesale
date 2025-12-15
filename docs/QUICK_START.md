# Quick Start Guide

## Getting Started with the Vaitikan E-Commerce API

This guide will help you make your first API calls in under 5 minutes.

## Prerequisites

- API Base URL: `http://your-domain.com/api/`
- HTTP client (curl, Postman, or your favorite programming language)

## Step 1: Register a User (30 seconds)

Create a new customer account:

```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "full_name": "Test User",
    "password": "SecurePass123!"
  }'
```

**Response**:

```json
{
  "id": 1,
  "email": "test@example.com",
  "full_name": "Test User",
  "user_type": "customer"
}
```

## Step 2: Login (30 seconds)

Get your authentication tokens:

```bash
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

**Response**:

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

💡 **Save the access token** - you'll need it for authenticated requests!

## Step 3: Browse Products (30 seconds)

List available products (no authentication required):

```bash
curl http://localhost:8000/api/products/
```

**Response**:

```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "product_name": "Classic Formal Shirt",
      "primary_image": "https://example.com/media/products/shirt1.jpg",
      "price_range": "1500"
    }
  ]
}
```

## Step 4: Add to Cart (1 minute)

Add a product to your cart (requires authentication):

```bash
curl -X POST http://localhost:8000/api/cart-items/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "variant_size": 1,
    "quantity": 2
  }'
```

**Response**:

```json
{
  "id": 1,
  "variant_size": 1,
  "quantity": 2,
  "variant_details": {
    "size_code": "M",
    "final_price": 1575.0
  }
}
```

## Step 5: View Cart (30 seconds)

Check your cart contents:

```bash
curl http://localhost:8000/api/cart/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response**:

```json
{
  "id": 1,
  "status": "active",
  "total_price": 3150.0,
  "items": [
    {
      "id": 1,
      "quantity": 2,
      "variant_details": {
        "size_code": "M",
        "final_price": 1575.0
      }
    }
  ]
}
```

## Step 6: Create Order (1 minute)

Place an order from your cart:

```bash
curl -X POST http://localhost:8000/api/orders/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "delivery_address_id": 1,
    "notes": "Please deliver before 5 PM"
  }'
```

**Response**:

```json
{
  "id": 1,
  "order_date": "2024-01-15T10:30:00Z",
  "status": "pending",
  "items": [
    {
      "id": 1,
      "quantity": 2,
      "snapshot_unit_price": "1575.00"
    }
  ]
}
```

## Next Steps

### Explore More Endpoints

- **Products**: `/api/products/` - Browse and search products
- **Orders**: `/api/orders/` - View order history
- **Payments**: `/api/payments/create/` - Process payments
- **Dashboard**: `/api/dashboard/stats/` - View analytics (admin only)

### Read Full Documentation

- [API Documentation](./API_DOCUMENTATION.md) - Complete API reference
- [Authentication Guide](./AUTHENTICATION_GUIDE.md) - Detailed auth flow
- [Razorpay Integration](./API_DOCUMENTATION.md#razorpay-integration) - Payment setup

### Test with Postman

Import our Postman collection for easy testing:

1. Download [Postman Collection](./postman_collection.json)
2. Import into Postman
3. Set environment variables:
   - `base_url`: `http://localhost:8000/api`
   - `access_token`: Your JWT token

### Common Use Cases

#### Customer Flow

1. Register → Login → Browse Products → Add to Cart → Checkout → Pay → Track Order

#### Admin Flow

1. Login → View Dashboard → Manage Products → Process Orders → View Analytics

#### Operator Flow

1. Login → Manage Inventory → View Material Requirements → Update Stock

## Quick Reference

### Authentication Header Format

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Common HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found

### Base URLs by Environment

- **Development**: `http://localhost:8000/api/`
- **Staging**: `https://staging.vaitikan.com/api/`
- **Production**: `https://api.vaitikan.com/api/`

## Need Help?

- 📖 [Full API Documentation](./API_DOCUMENTATION.md)
- 🔐 [Authentication Guide](./AUTHENTICATION_GUIDE.md)
- 💳 [Payment Integration](./API_DOCUMENTATION.md#razorpay-integration)
- 📧 Email: api-support@vaitikan.com

---

**Happy Coding! 🚀**
