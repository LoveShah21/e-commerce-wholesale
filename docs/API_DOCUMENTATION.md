# Vaitikan E-Commerce Platform - API Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [Error Handling](#error-handling)
4. [API Endpoints](#api-endpoints)
   - [User Management](#user-management)
   - [Product Management](#product-management)
   - [Shopping Cart](#shopping-cart)
   - [Orders](#orders)
   - [Payments](#payments)
   - [Invoices](#invoices)
   - [Dashboard & Analytics](#dashboard--analytics)
   - [Manufacturing](#manufacturing)
   - [Support & Feedback](#support--feedback)
5. [Razorpay Integration](#razorpay-integration)

---

## Introduction

The Vaitikan E-Commerce Platform API is a RESTful API built with Django REST Framework. It provides comprehensive functionality for managing an e-commerce platform with manufacturing workflow capabilities.

**Base URL**: `http://your-domain.com/api/`

**API Version**: 1.0

**Content Type**: `application/json`

---

## Authentication

The API uses JWT (JSON Web Token) authentication for securing endpoints.

### Authentication Flow

1. **Register** a new user account
2. **Login** to receive access and refresh tokens
3. Include the **access token** in the Authorization header for subsequent requests
4. **Refresh** the access token when it expires
5. **Logout** to invalidate the refresh token

### Token Format

Include the access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Token Expiration

- **Access Token**: Expires after 60 minutes
- **Refresh Token**: Expires after 7 days

---

## Error Handling

All API endpoints return consistent error responses following this format:

### Error Response Format

```json
{
  "error": "Error type",
  "message": "Human-readable error message",
  "details": {
    "field_name": ["Specific error details"]
  }
}
```

### HTTP Status Codes

| Status Code                       | Description                                           |
| --------------------------------- | ----------------------------------------------------- |
| 200                               | OK - Request succeeded                                |
| 201                               | Create                                                |
| d - Resource created successfully |
| 204                               | No Content - Request succeeded with no response body  |
| 400                               | Bad Request - Invalid input data                      |
| 401                               | Unauthorized - Missing or invalid authentication      |
| 403                               | Forbidden - Insufficient permissions                  |
| 404                               | Not Found - Resource does not exist                   |
| 409                               | Conflict - Duplicate entry or business rule violation |
| 500                               | Internal Server Error - Server-side error             |

### Common Error Examples

**Authentication Error (401)**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Permission Error (403)**

```json
{
  "detail": "You do not have permission to perform this action."
}
```

**Validation Error (400)**

```json
{
  "email": ["This field is required."],
  "password": ["This password is too short."]
}
```

**Not Found Error (404)**

```json
{
  "detail": "Not found."
}
```

---

## API Endpoints

### User Management

#### 1. Register User

Create a new user account with customer role by default.

**Endpoint**: `POST /api/users/register/`

**Authentication**: Not required

**Request Body**:

```json
{
  "email": "customer@example.com",
  "full_name": "John Doe",
  "phone": "+919876543210",
  "password": "SecurePassword123!"
}
```

**Response** (201 Created):

```json
{
  "id": 1,
  "email": "customer@example.com",
  "full_name": "John Doe",
  "phone": "+919876543210",
  "user_type": "customer",
  "account_status": "active",
  "date_joined": "2024-01-15T10:30:00Z"
}
```

**Validation Rules**:

- Email must be unique and valid format
- Password must meet Django's password validation requirements
- Phone number is optional

---

#### 2. Login

Authenticate user and receive JWT tokens.

**Endpoint**: `POST /api/users/login/`

**Authentication**: Not required

**Request Body**:

```json
{
  "email": "customer@example.com",
  "password": "SecurePassword123!"
}
```

**Response** (200 OK):

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

#### 3. Refresh Token

Get a new access token using the refresh token.

**Endpoint**: `POST /api/users/token/refresh/`

**Authentication**: Not required

**Request Body**:

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response** (200 OK):

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

#### 4. Get User Profile

Retrieve the authenticated user's profile information.

**Endpoint**: `GET /api/users/profile/`

**Authentication**: Required

**Response** (200 OK):

```json
{
  "id": 1,
  "email": "customer@example.com",
  "full_name": "John Doe",
  "phone": "+919876543210",
  "user_type": "customer",
  "account_status": "active",
  "date_joined": "2024-01-15T10:30:00Z"
}
```

---

#### 5. Update User Profile

Update the authenticated user's profile information.

**Endpoint**: `PUT /api/users/profile/`

**Authentication**: Required

**Request Body**:

```json
{
  "full_name": "John Smith",
  "phone": "+919876543211"
}
```

**Response** (200 OK):

```json
{
  "id": 1,
  "email": "customer@example.com",
  "full_name": "John Smith",
  "phone": "+919876543211",
  "user_type": "customer",
  "account_status": "active",
  "date_joined": "2024-01-15T10:30:00Z"
}
```

---

#### 6. Logout

Invalidate the refresh token (blacklist it).

**Endpoint**: `POST /api/users/logout/`

**Authentication**: Required

**Request Body**:

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response** (205 Reset Content):

```json
{
  "message": "Logout successful"
}
```

---

### Product Management

#### 1. List Products

Retrieve a list of all products with optional filtering.

**Endpoint**: `GET /api/products/`

**Authentication**: Not required

**Query Parameters**:

- `fabric` (optional): Filter by fabric ID
- `color` (optional): Filter by color ID
- `pattern` (optional): Filter by pattern ID
- `search` (optional): Search by product name or description

**Example Request**:

```
GET /api/products/?fabric=1&search=formal
```

**Response** (200 OK):

```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "product_name": "Classic Formal Shirt",
      "primary_image": "https://example.com/media/products/shirt1.jpg",
      "price_range": "1500",
      "created_at": "2024-01-10T08:00:00Z"
    }
  ]
}
```

---

#### 2. Get Product Details

Retrieve detailed information about a specific product including variants and sizes.

**Endpoint**: `GET /api/products/{id}/`

**Authentication**: Not required

**Response** (200 OK):

```json
{
  "id": 1,
  "product_name": "Classic Formal Shirt",
  "description": "Premium cotton formal shirt",
  "created_at": "2024-01-10T08:00:00Z",
  "images": [
    {
      "id": 1,
      "image_url": "https://example.com/media/products/shirt1.jpg",
      "alt_text": "Front view",
      "is_primary": true,
      "display_order": 1
    }
  ],
  "variants": [
    {
      "id": 1,
      "sku": "SHIRT-001-ABC",
      "fabric_name": "Cotton",
      "color_name": "White",
      "pattern_name": "Solid",
      "sleeve_type": "Full Sleeve",
      "pocket_type": "Single Pocket",
      "base_price": "1500.00",
      "sizes": [
        {
          "id": 1,
          "size": 1,
          "size_code": "M",
          "size_name": "Medium",
          "stock_quantity": 50,
          "final_price": 1575.0,
          "stock_available": 45,
          "stock_info": {
            "in_stock": 50,
            "reserved": 5,
            "available": 45
          }
        }
      ]
    }
  ]
}
```

---

#### 3. Create Product (Admin Only)

Create a new product with variants and sizes.

**Endpoint**: `POST /api/products/`

**Authentication**: Required (Admin only)

**Request Body**:

```json
{
  "product_name": "Premium Casual Shirt",
  "description": "Comfortable casual shirt for everyday wear",
  "variants": [
    {
      "fabric": 1,
      "color": 2,
      "pattern": 1,
      "sleeve": 1,
      "pocket": 1,
      "base_price": "1200.00",
      "sizes": [
        {
          "size": 1,
          "stock_quantity": 100
        }
      ]
    }
  ]
}
```

**Response** (201 Created):

```json
{
  "id": 2,
  "product_name": "Premium Casual Shirt",
  "description": "Comfortable casual shirt for everyday wear",
  "created_at": "2024-01-15T10:30:00Z",
  "images": [],
  "variants": [
    {
      "id": 2,
      "sku": "SHIRT-002-XYZ",
      "fabric_name": "Cotton",
      "color_name": "Blue",
      "pattern_name": "Solid",
      "sleeve_type": "Full Sleeve",
      "pocket_type": "Single Pocket",
      "base_price": "1200.00",
      "sizes": [
        {
          "id": 2,
          "size": 1,
          "size_code": "M",
          "size_name": "Medium",
          "stock_quantity": 100,
          "final_price": 1260.0,
          "stock_available": 100
        }
      ]
    }
  ]
}
```

---

#### 4. Update Product (Admin Only)

Update product information.

**Endpoint**: `PUT /api/products/{id}/`

**Authentication**: Required (Admin only)

**Request Body**:

```json
{
  "product_name": "Premium Casual Shirt - Updated",
  "description": "Updated description"
}
```

**Response** (200 OK):

```json
{
  "id": 2,
  "product_name": "Premium Casual Shirt - Updated",
  "description": "Updated description"
}
```

---

#### 5. Delete Product (Admin Only)

Delete a product and all associated variants.

**Endpoint**: `DELETE /api/products/{id}/`

**Authentication**: Required (Admin only)

**Response** (204 No Content)

---

#### 6. Add Variant to Product (Admin Only)

Add a new variant to an existing product.

**Endpoint**: `POST /api/products/{product_id}/variants/`

**Authentication**: Required (Admin only)

**Request Body**:

```json
{
  "fabric": 2,
  "color": 3,
  "pattern": 2,
  "sleeve": 2,
  "pocket": 2,
  "base_price": "1800.00",
  "sizes": [
    {
      "size": 2,
      "stock_quantity": 75
    }
  ]
}
```

**Response** (201 Created):

```json
{
  "id": 3,
  "sku": "SHIRT-003-DEF",
  "fabric_name": "Linen",
  "color_name": "Black",
  "pattern_name": "Striped",
  "sleeve_type": "Short Sleeve",
  "pocket_type": "No Pocket",
  "base_price": "1800.00",
  "sizes": [
    {
      "id": 3,
      "size": 2,
      "size_code": "L",
      "size_name": "Large",
      "stock_quantity": 75,
      "final_price": 1890.0,
      "stock_available": 75
    }
  ]
}
```

---

#### 7. Update Stock (Admin Only)

Update stock quantity for a variant size.

**Endpoint**: `PUT /api/products/sizes/{variant_size_id}/stock/`

**Authentication**: Required (Admin only)

**Request Body**:

```json
{
  "quantity_in_stock": 150,
  "quantity_reserved": 10
}
```

**Response** (200 OK):

```json
{
  "quantity_in_stock": 150,
  "quantity_reserved": 10,
  "quantity_available": 140,
  "last_updated": "2024-01-15T11:00:00Z"
}
```

---

#### 8. Upload Product Image (Admin Only)

Upload an image for a product.

**Endpoint**: `POST /api/products/{product_id}/images/`

**Authentication**: Required (Admin only)

**Content-Type**: `multipart/form-data`

**Request Body**:

```
image_file: [binary file data]
alt_text: "Product front view"
is_primary: true
display_order: 1
```

**Response** (201 Created):

```json
{
  "id": 2,
  "image_url": "https://example.com/media/products/shirt2.jpg",
  "alt_text": "Product front view",
  "is_primary": true,
  "display_order": 1
}
```

---

### Shopping Cart

#### 1. Get Active Cart

Retrieve the authenticated user's active shopping cart.

**Endpoint**: `GET /api/cart/`

**Authentication**: Required

**Response** (200 OK):

```json
{
  "id": 1,
  "status": "active",
  "total_price": 3150.0,
  "items": [
    {
      "id": 1,
      "variant_size": 1,
      "quantity": 2,
      "variant_details": {
        "id": 1,
        "size_code": "M",
        "size_name": "Medium",
        "final_price": 1575.0,
        "stock_available": 45
      }
    }
  ]
}
```

---

#### 2. Add Item to Cart

Add a product variant size to the cart or update quantity if already exists.

**Endpoint**: `POST /api/cart-items/`

**Authentication**: Required

**Request Body**:

```json
{
  "variant_size": 1,
  "quantity": 2
}
```

**Response** (201 Created):

```json
{
  "id": 1,
  "variant_size": 1,
  "quantity": 2,
  "variant_details": {
    "id": 1,
    "size_code": "M",
    "size_name": "Medium",
    "final_price": 1575.0,
    "stock_available": 45
  }
}
```

**Business Rules**:

- If item already exists in cart, quantity is updated (idempotent)
- Stock availability is validated before adding
- Returns 400 if insufficient stock

---

#### 3. Update Cart Item

Update the quantity of a cart item.

**Endpoint**: `PUT /api/cart-items/{id}/`

**Authentication**: Required

**Request Body**:

```json
{
  "quantity": 3
}
```

**Response** (200 OK):

```json
{
  "id": 1,
  "variant_size": 1,
  "quantity": 3,
  "variant_details": {
    "id": 1,
    "size_code": "M",
    "size_name": "Medium",
    "final_price": 1575.0,
    "stock_available": 45
  }
}
```

---

#### 4. Remove Cart Item

Remove an item from the cart.

**Endpoint**: `DELETE /api/cart-items/{id}/`

**Authentication**: Required

**Response** (204 No Content)

---

#### 5. Clear Cart

Remove all items from the cart.

**Endpoint**: `DELETE /api/cart/clear/`

**Authentication**: Required

**Response** (204 No Content)

---

### Orders

#### 1. List Orders

Retrieve all orders for the authenticated user.

**Endpoint**: `GET /api/orders/`

**Authentication**: Required

**Response** (200 OK):

```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "order_date": "2024-01-15T10:30:00Z",
      "status": "confirmed",
      "delivery_address": 1,
      "notes": "Please deliver before 5 PM",
      "items": [
        {
          "id": 1,
          "variant_size": 1,
          "quantity": 2,
          "snapshot_unit_price": "1575.00",
          "variant_details": {
            "id": 1,
            "size_code": "M",
            "size_name": "Medium"
          }
        }
      ]
    }
  ]
}
```

---

#### 2. Get Order Details

Retrieve detailed information about a specific order.

**Endpoint**: `GET /api/orders/{id}/`

**Authentication**: Required

**Response** (200 OK):

```json
{
  "id": 1,
  "order_date": "2024-01-15T10:30:00Z",
  "status": "confirmed",
  "delivery_address": 1,
  "notes": "Please deliver before 5 PM",
  "items": [
    {
      "id": 1,
      "variant_size": 1,
      "quantity": 2,
      "snapshot_unit_price": "1575.00",
      "variant_details": {
        "id": 1,
        "size_code": "M",
        "size_name": "Medium",
        "final_price": 1575.0
      }
    }
  ]
}
```

---

#### 3. Create Order

Create an order from the active cart.

**Endpoint**: `POST /api/orders/`

**Authentication**: Required

**Request Body**:

```json
{
  "delivery_address_id": 1,
  "notes": "Please deliver before 5 PM"
}
```

**Response** (201 Created):

```json
{
  "id": 1,
  "order_date": "2024-01-15T10:30:00Z",
  "status": "pending",
  "delivery_address": 1,
  "notes": "Please deliver before 5 PM",
  "items": [
    {
      "id": 1,
      "variant_size": 1,
      "quantity": 2,
      "snapshot_unit_price": "1575.00"
    }
  ]
}
```

**Business Rules**:

- Cart must not be empty
- Stock is reserved atomically for all items
- Prices are snapshotted at order creation time
- Cart status changes to 'checked_out'
- Returns 400 if insufficient stock for any item

---

#### 4. List All Orders (Admin Only)

Retrieve all orders in the system with filtering options.

**Endpoint**: `GET /api/admin/orders/`

**Authentication**: Required (Admin only)

**Query Parameters**:

- `status` (optional): Filter by order status
- `user` (optional): Filter by user ID
- `date_from` (optional): Filter orders from date
- `date_to` (optional): Filter orders to date

**Response** (200 OK):

```json
{
  "count": 50,
  "next": "http://example.com/api/admin/orders/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": {
        "id": 1,
        "email": "customer@example.com",
        "full_name": "John Doe"
      },
      "order_date": "2024-01-15T10:30:00Z",
      "status": "confirmed",
      "total_amount": "3150.00"
    }
  ]
}
```

---

#### 5. Update Order Status (Admin Only)

Update the status of an order.

**Endpoint**: `PUT /api/admin/orders/{order_id}/`

**Authentication**: Required (Admin only)

**Request Body**:

```json
{
  "status": "processing"
}
```

**Response** (200 OK):

```json
{
  "id": 1,
  "status": "processing",
  "message": "Order status updated successfully"
}
```

**Valid Status Transitions**:

- `pending` → `confirmed` (after advance payment)
- `confirmed` → `processing` (manufacturing started)
- `processing` → `ready_for_dispatch` (manufacturing complete)
- `ready_for_dispatch` → `dispatched` (after final payment)
- `dispatched` → `delivered` (delivery confirmed)
- Any status → `cancelled` (order cancelled)

---

#### 6. Get Order Material Requirements (Admin Only)

Get material requirements for manufacturing an order.

**Endpoint**: `GET /api/admin/orders/{order_id}/materials/`

**Authentication**: Required (Admin only)

**Response** (200 OK):

```json
{
  "order_id": 1,
  "materials": [
    {
      "material_id": 1,
      "material_name": "Cotton Fabric",
      "required_quantity": 10.5,
      "unit": "meters",
      "available_quantity": 500.0,
      "sufficient": true
    },
    {
      "material_id": 2,
      "material_name": "Thread",
      "required_quantity": 200.0,
      "unit": "meters",
      "available_quantity": 5000.0,
      "sufficient": true
    }
  ]
}
```

---

### Payments

#### 1. Create Payment

Create a Razorpay payment order for an order.

**Endpoint**: `POST /api/payments/create/`

**Authentication**: Required

**Request Body**:

```json
{
  "order_id": 1,
  "payment_type": "advance"
}
```

**Response** (201 Created):

```json
{
  "payment_id": 1,
  "razorpay_order_id": "order_MNOPqrstuvwxyz",
  "amount": 1575.0,
  "currency": "INR",
  "payment_type": "advance",
  "status": "pending"
}
```

**Payment Types**:

- `advance`: 50% of order total
- `final`: Remaining 50% of order total

---

#### 2. Verify Payment

Verify Razorpay payment signature after successful payment.

**Endpoint**: `POST /api/payments/verify/`

**Authentication**: Required

**Request Body**:

```json
{
  "razorpay_order_id": "order_MNOPqrstuvwxyz",
  "razorpay_payment_id": "pay_ABCDefghijklmn",
  "razorpay_signature": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
}
```

**Response** (200 OK):

```json
{
  "status": "success",
  "message": "Payment verified successfully",
  "payment_id": 1,
  "order_status": "confirmed"
}
```

**Business Rules**:

- Signature is verified using Razorpay secret key
- Payment and order status updated atomically
- Advance payment changes order status to 'confirmed'
- Final payment allows order to be dispatched

---

#### 3. Payment Failure

Record a failed payment attempt.

**Endpoint**: `POST /api/payments/failure/`

**Authentication**: Required

**Request Body**:

```json
{
  "razorpay_order_id": "order_MNOPqrstuvwxyz",
  "error_code": "BAD_REQUEST_ERROR",
  "error_description": "Payment failed due to insufficient funds"
}
```

**Response** (200 OK):

```json
{
  "status": "failed",
  "message": "Payment failure recorded",
  "payment_id": 1
}
```

---

#### 4. Retry Payment

Create a new payment attempt for a failed payment.

**Endpoint**: `POST /api/payments/retry/`

**Authentication**: Required

**Request Body**:

```json
{
  "order_id": 1,
  "payment_type": "advance"
}
```

**Response** (201 Created):

```json
{
  "payment_id": 2,
  "razorpay_order_id": "order_XYZabcdefghijk",
  "amount": 1575.0,
  "currency": "INR",
  "payment_type": "advance",
  "status": "pending"
}
```

---

#### 5. Get Payment History

Retrieve payment history for the authenticated user.

**Endpoint**: `GET /api/payments/history/`

**Authentication**: Required

**Response** (200 OK):

```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "order_id": 1,
      "razorpay_order_id": "order_MNOPqrstuvwxyz",
      "razorpay_payment_id": "pay_ABCDefghijklmn",
      "amount": 1575.0,
      "payment_type": "advance",
      "status": "success",
      "payment_date": "2024-01-15T10:35:00Z"
    }
  ]
}
```

---

#### 6. Get Payment Status

Get payment status for a specific order.

**Endpoint**: `GET /api/payments/status/{order_id}/`

**Authentication**: Required

**Response** (200 OK):

```json
{
  "order_id": 1,
  "advance_payment": {
    "id": 1,
    "status": "success",
    "amount": 1575.0,
    "payment_date": "2024-01-15T10:35:00Z"
  },
  "final_payment": {
    "id": 2,
    "status": "pending",
    "amount": 1575.0
  },
  "total_paid": 1575.0,
  "total_amount": 3150.0,
  "payment_complete": false
}
```

---

#### 7. Payment Webhook

Razorpay webhook endpoint for payment notifications.

**Endpoint**: `POST /api/payments/webhook/`

**Authentication**: Razorpay signature verification

**Request Body** (from Razorpay):

```json
{
  "event": "payment.captured",
  "payload": {
    "payment": {
      "entity": {
        "id": "pay_ABCDefghijklmn",
        "order_id": "order_MNOPqrstuvwxyz",
        "amount": 157500,
        "status": "captured"
      }
    }
  }
}
```

**Response** (200 OK):

```json
{
  "status": "processed"
}
```

---

### Invoices

#### 1. Get Invoice Details

Retrieve invoice details for an order.

**Endpoint**: `GET /api/invoices/{order_id}/`

**Authentication**: Required

**Response** (200 OK):

```json
{
  "id": 1,
  "invoice_number": "INV-2024-0001",
  "order": 1,
  "invoice_date": "2024-01-15T10:40:00Z",
  "subtotal": "3000.00",
  "tax_percentage": "5.00",
  "tax_amount": "150.00",
  "total_amount": "3150.00",
  "invoice_url": "https://example.com/media/invoices/INV-2024-0001.pdf"
}
```

---

#### 2. Download Invoice

Download invoice PDF for an order.

**Endpoint**: `GET /api/invoices/{order_id}/download/`

**Authentication**: Required

**Response** (200 OK):

- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename="INV-2024-0001.pdf"`
- Binary PDF data

**Invoice Contents**:

- Invoice number and date
- Customer details
- Order items with quantities and prices
- Subtotal, tax breakdown, and total
- Payment information
- Company details

---

### Dashboard & Analytics

#### 1. Get Dashboard Statistics

Retrieve key business metrics for the admin dashboard.

**Endpoint**: `GET /api/dashboard/stats/`

**Authentication**: Required (Admin only)

**Query Parameters**:

- `date_from` (optional): Start date for analytics (YYYY-MM-DD)
- `date_to` (optional): End date for analytics (YYYY-MM-DD)

**Response** (200 OK):

```json
{
  "total_sales": "150000.00",
  "total_orders": 45,
  "pending_orders": 5,
  "confirmed_orders": 10,
  "processing_orders": 8,
  "dispatched_orders": 12,
  "delivered_orders": 10,
  "low_stock_count": 3,
  "sales_trend": [
    {
      "date": "2024-01-09",
      "sales": "5000.00",
      "orders": 2
    },
    {
      "date": "2024-01-10",
      "sales": "8500.00",
      "orders": 3
    },
    {
      "date": "2024-01-11",
      "sales": "12000.00",
      "orders": 5
    },
    {
      "date": "2024-01-12",
      "sales": "7500.00",
      "orders": 3
    },
    {
      "date": "2024-01-13",
      "sales": "15000.00",
      "orders": 6
    },
    {
      "date": "2024-01-14",
      "sales": "9000.00",
      "orders": 4
    },
    {
      "date": "2024-01-15",
      "sales": "11000.00",
      "orders": 5
    }
  ],
  "low_stock_items": [
    {
      "product_name": "Classic Formal Shirt",
      "variant_sku": "SHIRT-001-ABC",
      "size": "M",
      "quantity_available": 5,
      "threshold": 10
    }
  ],
  "recent_orders": [
    {
      "id": 45,
      "customer_name": "John Doe",
      "order_date": "2024-01-15T10:30:00Z",
      "status": "confirmed",
      "total_amount": "3150.00"
    }
  ]
}
```

**Business Rules**:

- Sales trend shows last 7 days by default
- Low stock items have quantity_available below threshold (default: 10)
- Recent orders limited to last 10 orders

---

### Manufacturing

#### 1. List Raw Materials

Retrieve all raw materials in inventory.

**Endpoint**: `GET /api/manufacturing/materials/`

**Authentication**: Required (Admin/Operator)

**Response** (200 OK):

```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "material_name": "Cotton Fabric",
      "material_type": {
        "id": 1,
        "type_name": "Fabric"
      },
      "unit_price": "150.00",
      "current_quantity": 500.0,
      "unit": "meters",
      "last_updated": "2024-01-15T09:00:00Z"
    }
  ]
}
```

---

#### 2. Create Raw Material

Add a new raw material to inventory.

**Endpoint**: `POST /api/manufacturing/materials/`

**Authentication**: Required (Admin/Operator)

**Request Body**:

```json
{
  "material_name": "Polyester Thread",
  "material_type": 2,
  "unit_price": "5.00",
  "current_quantity": 10000.0,
  "unit": "meters"
}
```

**Response** (201 Created):

```json
{
  "id": 11,
  "material_name": "Polyester Thread",
  "material_type": {
    "id": 2,
    "type_name": "Thread"
  },
  "unit_price": "5.00",
  "current_quantity": 10000.0,
  "unit": "meters",
  "last_updated": "2024-01-15T11:00:00Z"
}
```

---

#### 3. Update Material Quantity

Update the quantity of a raw material.

**Endpoint**: `PUT /api/manufacturing/materials/{material_id}/quantity/`

**Authentication**: Required (Admin/Operator)

**Request Body**:

```json
{
  "quantity_change": 100.0,
  "operation": "add"
}
```

**Response** (200 OK):

```json
{
  "id": 1,
  "material_name": "Cotton Fabric",
  "current_quantity": 600.0,
  "last_updated": "2024-01-15T11:30:00Z"
}
```

**Operations**:

- `add`: Increase quantity (receiving stock)
- `subtract`: Decrease quantity (consumption)

---

#### 4. List Suppliers

Retrieve all suppliers.

**Endpoint**: `GET /api/manufacturing/suppliers/`

**Authentication**: Required (Admin/Operator)

**Response** (200 OK):

```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "supplier_name": "ABC Textiles",
      "contact_person": "Rajesh Kumar",
      "phone": "+919876543210",
      "email": "contact@abctextiles.com",
      "address": "123 Textile Market, Mumbai"
    }
  ]
}
```

---

#### 5. Create Supplier

Add a new supplier.

**Endpoint**: `POST /api/manufacturing/suppliers/`

**Authentication**: Required (Admin/Operator)

**Request Body**:

```json
{
  "supplier_name": "XYZ Fabrics",
  "contact_person": "Amit Sharma",
  "phone": "+919876543211",
  "email": "info@xyzfabrics.com",
  "address": "456 Fabric Street, Delhi"
}
```

**Response** (201 Created):

```json
{
  "id": 6,
  "supplier_name": "XYZ Fabrics",
  "contact_person": "Amit Sharma",
  "phone": "+919876543211",
  "email": "info@xyzfabrics.com",
  "address": "456 Fabric Street, Delhi"
}
```

---

#### 6. Associate Material with Supplier

Create a material-supplier association with pricing and reorder information.

**Endpoint**: `POST /api/manufacturing/material-suppliers/`

**Authentication**: Required (Admin/Operator)

**Request Body**:

```json
{
  "material": 1,
  "supplier": 1,
  "supplier_price": "145.00",
  "min_order_quantity": 100.0,
  "reorder_level": 50.0,
  "lead_time_days": 7
}
```

**Response** (201 Created):

```json
{
  "id": 1,
  "material": {
    "id": 1,
    "material_name": "Cotton Fabric"
  },
  "supplier": {
    "id": 1,
    "supplier_name": "ABC Textiles"
  },
  "supplier_price": "145.00",
  "min_order_quantity": 100.0,
  "reorder_level": 50.0,
  "lead_time_days": 7,
  "is_preferred": false
}
```

---

#### 7. Get Inventory View

Get comprehensive inventory view with reorder alerts.

**Endpoint**: `GET /api/manufacturing/inventory/`

**Authentication**: Required (Admin/Operator)

**Response** (200 OK):

```json
{
  "materials": [
    {
      "id": 1,
      "material_name": "Cotton Fabric",
      "material_type": "Fabric",
      "current_quantity": 45.0,
      "unit": "meters",
      "reorder_alert": true,
      "reorder_level": 50.0,
      "preferred_supplier": {
        "supplier_name": "ABC Textiles",
        "supplier_price": "145.00",
        "min_order_quantity": 100.0,
        "lead_time_days": 7
      }
    }
  ]
}
```

---

#### 8. Get Reorder Alerts

Get materials that need reordering.

**Endpoint**: `GET /api/manufacturing/inventory/alerts/`

**Authentication**: Required (Admin/Operator)

**Response** (200 OK):

```json
{
  "alerts": [
    {
      "material_id": 1,
      "material_name": "Cotton Fabric",
      "current_quantity": 45.0,
      "reorder_level": 50.0,
      "deficit": 5.0,
      "preferred_supplier": "ABC Textiles",
      "recommended_order_quantity": 100.0
    }
  ]
}
```

---

#### 9. List Manufacturing Specifications

Retrieve manufacturing specifications for variant sizes.

**Endpoint**: `GET /api/manufacturing/specifications/`

**Authentication**: Required (Admin/Operator)

**Response** (200 OK):

```json
{
  "count": 20,
  "results": [
    {
      "id": 1,
      "variant_size": {
        "id": 1,
        "product_name": "Classic Formal Shirt",
        "size": "M"
      },
      "material": {
        "id": 1,
        "material_name": "Cotton Fabric"
      },
      "quantity_required": 2.5,
      "unit": "meters"
    }
  ]
}
```

---

#### 10. Create Manufacturing Specification

Create a specification linking materials to a variant size.

**Endpoint**: `POST /api/manufacturing/specifications/`

**Authentication**: Required (Admin/Operator)

**Request Body**:

```json
{
  "variant_size": 1,
  "material": 1,
  "quantity_required": 2.5,
  "unit": "meters"
}
```

**Response** (201 Created):

```json
{
  "id": 21,
  "variant_size": 1,
  "material": 1,
  "quantity_required": 2.5,
  "unit": "meters"
}
```

---

### Support & Feedback

#### 1. List Inquiries

Retrieve inquiries for the authenticated user.

**Endpoint**: `GET /api/support/inquiries/`

**Authentication**: Required

**Response** (200 OK):

```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "description": "Need 500 custom shirts with company logo",
      "logo_file": "https://example.com/media/inquiries/logo1.png",
      "status": "pending",
      "created_at": "2024-01-15T09:00:00Z"
    }
  ]
}
```

---

#### 2. Create Inquiry

Submit a new inquiry for bulk orders or customization.

**Endpoint**: `POST /api/support/inquiries/`

**Authentication**: Required

**Content-Type**: `multipart/form-data`

**Request Body**:

```
description: "Need 500 custom shirts with company logo"
logo_file: [binary file data]
```

**Response** (201 Created):

```json
{
  "id": 1,
  "description": "Need 500 custom shirts with company logo",
  "logo_file": "https://example.com/media/inquiries/logo1.png",
  "status": "pending",
  "created_at": "2024-01-15T09:00:00Z"
}
```

---

#### 3. Get Inquiry Details

Retrieve detailed information about an inquiry including quotations.

**Endpoint**: `GET /api/support/inquiries/{id}/`

**Authentication**: Required

**Response** (200 OK):

```json
{
  "id": 1,
  "user": {
    "id": 1,
    "email": "customer@example.com",
    "full_name": "John Doe"
  },
  "description": "Need 500 custom shirts with company logo",
  "logo_file": "https://example.com/media/inquiries/logo1.png",
  "status": "quoted",
  "created_at": "2024-01-15T09:00:00Z",
  "quotation_requests": [
    {
      "id": 1,
      "variant_size": 1,
      "quantity": 500,
      "customization_details": "Company logo on pocket",
      "status": "quoted",
      "quotation_price": {
        "unit_price": "1200.00",
        "customization_charge_per_unit": "50.00",
        "total_price": "625000.00",
        "validity_days": 30,
        "valid_until": "2024-02-14T10:00:00Z"
      }
    }
  ]
}
```

---

#### 4. Create Quotation Request (Admin Only)

Create a quotation request for an inquiry.

**Endpoint**: `POST /api/support/admin/inquiries/{inquiry_id}/quotation-requests/`

**Authentication**: Required (Admin only)

**Request Body**:

```json
{
  "variant_size": 1,
  "quantity": 500,
  "customization_details": "Company logo on pocket"
}
```

**Response** (201 Created):

```json
{
  "id": 1,
  "inquiry": 1,
  "variant_size": 1,
  "quantity": 500,
  "customization_details": "Company logo on pocket",
  "status": "pending"
}
```

---

#### 5. Provide Quotation Price (Admin Only)

Provide pricing for a quotation request.

**Endpoint**: `POST /api/support/admin/quotation-requests/{quotation_request_id}/price/`

**Authentication**: Required (Admin only)

**Request Body**:

```json
{
  "unit_price": "1200.00",
  "customization_charge_per_unit": "50.00",
  "validity_days": 30,
  "notes": "Bulk discount applied"
}
```

**Response** (201 Created):

```json
{
  "id": 1,
  "quotation_request": 1,
  "unit_price": "1200.00",
  "customization_charge_per_unit": "50.00",
  "quoted_quantity": 500,
  "total_price": "625000.00",
  "validity_days": 30,
  "valid_until": "2024-02-14T10:00:00Z",
  "notes": "Bulk discount applied",
  "status": "pending"
}
```

---

#### 6. Send Quotation to Customer (Admin Only)

Send the quotation to the customer.

**Endpoint**: `POST /api/support/admin/quotation-prices/{quotation_price_id}/send/`

**Authentication**: Required (Admin only)

**Response** (200 OK):

```json
{
  "status": "sent",
  "message": "Quotation sent to customer successfully"
}
```

---

#### 7. Accept/Reject Quotation

Customer accepts or rejects a quotation.

**Endpoint**: `PUT /api/support/quotation-prices/{id}/respond/`

**Authentication**: Required

**Request Body**:

```json
{
  "action": "accept"
}
```

**Response** (200 OK):

```json
{
  "status": "accepted",
  "message": "Quotation accepted successfully"
}
```

**Actions**:

- `accept`: Accept the quotation
- `reject`: Reject the quotation

---

#### 8. List Complaints

Retrieve complaints for the authenticated user.

**Endpoint**: `GET /api/support/complaints/`

**Authentication**: Required

**Response** (200 OK):

```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "order": 1,
      "category": "quality",
      "description": "Shirt has stitching issues",
      "status": "open",
      "created_at": "2024-01-15T14:00:00Z"
    }
  ]
}
```

---

#### 9. Create Complaint

Submit a complaint about an order.

**Endpoint**: `POST /api/support/complaints/`

**Authentication**: Required

**Request Body**:

```json
{
  "order": 1,
  "category": "quality",
  "description": "Shirt has stitching issues"
}
```

**Response** (201 Created):

```json
{
  "id": 1,
  "order": 1,
  "category": "quality",
  "description": "Shirt has stitching issues",
  "status": "open",
  "created_at": "2024-01-15T14:00:00Z"
}
```

**Complaint Categories**:

- `quality`: Product quality issues
- `delivery`: Delivery problems
- `service`: Customer service issues
- `other`: Other complaints

---

#### 10. Resolve Complaint (Admin Only)

Resolve a complaint with resolution notes.

**Endpoint**: `POST /api/support/admin/complaints/{id}/resolve/`

**Authentication**: Required (Admin only)

**Request Body**:

```json
{
  "resolution_notes": "Replacement shirt sent to customer"
}
```

**Response** (200 OK):

```json
{
  "id": 1,
  "status": "resolved",
  "resolution_notes": "Replacement shirt sent to customer",
  "resolution_date": "2024-01-16T10:00:00Z"
}
```

---

#### 11. Create Feedback

Submit feedback for a delivered order.

**Endpoint**: `POST /api/support/feedback/`

**Authentication**: Required

**Request Body**:

```json
{
  "order": 1,
  "rating": 5,
  "description": "Excellent quality and fast delivery!"
}
```

**Response** (201 Created):

```json
{
  "id": 1,
  "order": 1,
  "rating": 5,
  "description": "Excellent quality and fast delivery!",
  "created_at": "2024-01-20T15:00:00Z"
}
```

**Rating Scale**: 1-5 (1 = Poor, 5 = Excellent)

---

#### 12. List Feedback (Admin Only)

Retrieve all customer feedback.

**Endpoint**: `GET /api/support/admin/feedback/`

**Authentication**: Required (Admin only)

**Response** (200 OK):

```json
{
  "count": 25,
  "results": [
    {
      "id": 1,
      "user": {
        "id": 1,
        "full_name": "John Doe"
      },
      "order": 1,
      "rating": 5,
      "description": "Excellent quality and fast delivery!",
      "created_at": "2024-01-20T15:00:00Z"
    }
  ]
}
```

---

## Razorpay Integration

### Overview

The platform integrates with Razorpay for secure payment processing. The payment flow follows a two-stage approach:

1. **Advance Payment**: 50% of order total paid at order confirmation
2. **Final Payment**: Remaining 50% paid before dispatch

### Integration Flow

```
┌─────────────┐
│   Customer  │
└──────┬──────┘
       │
       │ 1. Create Order
       ▼
┌─────────────────┐
│  Backend API    │
└──────┬──────────┘
       │
       │ 2. Create Payment
       ▼
┌─────────────────┐
│ POST /api/      │
│ payments/create/│
└──────┬──────────┘
       │
       │ 3. Create Razorpay Order
       ▼
┌─────────────────┐
│  Razorpay API   │
└──────┬──────────┘
       │
       │ 4. Return Order ID
       ▼
┌─────────────────┐
│   Frontend      │
│ (Razorpay SDK)  │
└──────┬──────────┘
       │
       │ 5. Customer Pays
       ▼
┌─────────────────┐
│  Razorpay       │
│  Checkout       │
└──────┬──────────┘
       │
       │ 6. Payment Success
       ▼
┌─────────────────┐
│   Frontend      │
└──────┬──────────┘
       │
       │ 7. Verify Payment
       ▼
┌─────────────────┐
│ POST /api/      │
│ payments/verify/│
└──────┬──────────┘
       │
       │ 8. Verify Signature
       ▼
┌─────────────────┐
│  Backend API    │
│ (Update Status) │
└─────────────────┘
```

### Step-by-Step Implementation

#### Step 1: Create Payment Order

When a customer creates an order, the backend creates a Razorpay payment order:

**Backend Request**:

```python
import razorpay

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

order_data = {
    'amount': 157500,  # Amount in paise (1575.00 INR)
    'currency': 'INR',
    'receipt': f'order_{order_id}',
    'payment_capture': 1
}

razorpay_order = client.order.create(data=order_data)
```

**Response from Razorpay**:

```json
{
  "id": "order_MNOPqrstuvwxyz",
  "entity": "order",
  "amount": 157500,
  "amount_paid": 0,
  "amount_due": 157500,
  "currency": "INR",
  "receipt": "order_1",
  "status": "created"
}
```

#### Step 2: Initialize Razorpay Checkout (Frontend)

Include Razorpay SDK in your HTML:

```html
<script src="https://checkout.razorpay.com/v1/checkout.js"></script>
```

Initialize checkout with the order details:

```javascript
const options = {
  key: "rzp_test_XXXXXXXXXXXXXXX", // Razorpay Key ID
  amount: 157500, // Amount in paise
  currency: "INR",
  name: "Vaitikan Shirts",
  description: "Order Payment",
  order_id: "order_MNOPqrstuvwxyz", // Razorpay Order ID
  handler: function (response) {
    // Payment successful
    verifyPayment(response);
  },
  prefill: {
    name: "John Doe",
    email: "customer@example.com",
    contact: "+919876543210",
  },
  theme: {
    color: "#3399cc",
  },
};

const rzp = new Razorpay(options);
rzp.open();
```

#### Step 3: Handle Payment Success

When payment succeeds, Razorpay returns payment details:

```javascript
function verifyPayment(response) {
  const data = {
    razorpay_order_id: response.razorpay_order_id,
    razorpay_payment_id: response.razorpay_payment_id,
    razorpay_signature: response.razorpay_signature,
  };

  fetch("/api/payments/verify/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(data),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        window.location.href = "/payments/success/";
      }
    });
}
```

#### Step 4: Verify Payment Signature (Backend)

The backend verifies the payment signature to ensure authenticity:

```python
import hmac
import hashlib

def verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    # Create signature string
    message = f"{razorpay_order_id}|{razorpay_payment_id}"

    # Generate expected signature
    expected_signature = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    # Compare signatures
    return hmac.compare_digest(expected_signature, razorpay_signature)
```

### Payment Failure Handling

If payment fails, handle the error:

```javascript
rzp.on("payment.failed", function (response) {
  const data = {
    razorpay_order_id: response.error.metadata.order_id,
    error_code: response.error.code,
    error_description: response.error.description,
  };

  fetch("/api/payments/failure/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(data),
  }).then(() => {
    window.location.href = "/payments/failure/";
  });
});
```

### Webhook Configuration

Configure webhooks in Razorpay Dashboard to receive payment notifications:

**Webhook URL**: `https://your-domain.com/api/payments/webhook/`

**Events to Subscribe**:

- `payment.captured`
- `payment.failed`
- `order.paid`

**Webhook Signature Verification**:

```python
def verify_webhook_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)
```

### Test Mode

For testing, use Razorpay test credentials:

**Test Key ID**: `rzp_test_XXXXXXXXXXXXXXX`
**Test Key Secret**: `XXXXXXXXXXXXXXXXXXXXXXXX`

**Test Card Details**:

- Card Number: `4111 1111 1111 1111`
- CVV: Any 3 digits
- Expiry: Any future date

### Production Checklist

Before going live:

1. ✅ Replace test keys with live keys
2. ✅ Enable webhook signature verification
3. ✅ Implement proper error logging
4. ✅ Test payment failure scenarios
5. ✅ Configure webhook URL in Razorpay Dashboard
6. ✅ Enable HTTPS for all payment endpoints
7. ✅ Implement rate limiting on payment endpoints
8. ✅ Set up payment reconciliation process

### Security Best Practices

1. **Never expose Key Secret**: Keep it server-side only
2. **Always verify signatures**: Both for payments and webhooks
3. **Use HTTPS**: All payment communication must be encrypted
4. **Implement idempotency**: Handle duplicate payment notifications
5. **Log all transactions**: Maintain audit trail for reconciliation
6. **Validate amounts**: Verify payment amount matches order total
7. **Handle timeouts**: Implement proper timeout handling
8. **Rate limiting**: Protect payment endpoints from abuse

### Common Error Codes

| Error Code        | Description                   | Action                |
| ----------------- | ----------------------------- | --------------------- |
| BAD_REQUEST_ERROR | Invalid request parameters    | Validate input data   |
| GATEWAY_ERROR     | Payment gateway error         | Retry payment         |
| SERVER_ERROR      | Razorpay server error         | Retry after some time |
| INVALID_SIGNATURE | Signature verification failed | Check secret key      |

---

## Appendix

### Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Authentication endpoints**: 5 requests per minute
- **Payment endpoints**: 10 requests per minute
- **General endpoints**: 100 requests per minute

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

### Pagination

List endpoints support pagination with the following parameters:

- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

Paginated responses include:

```json
{
  "count": 150,
  "next": "http://example.com/api/products/?page=2",
  "previous": null,
  "results": [...]
}
```

### Filtering and Sorting

Many list endpoints support filtering and sorting:

**Filtering**:

```
GET /api/products/?fabric=1&color=2
GET /api/orders/?status=confirmed
```

**Sorting**:

```
GET /api/products/?ordering=-created_at
GET /api/orders/?ordering=order_date
```

Use `-` prefix for descending order.

### Date Formats

All dates follow ISO 8601 format:

```
2024-01-15T10:30:00Z
```

### Currency

All monetary values are in Indian Rupees (INR) unless specified otherwise.

### Support

For API support, contact:

- Email: api-support@vaitikan.com
- Documentation: https://docs.vaitikan.com

---

**Document Version**: 1.0  
**Last Updated**: January 15, 2024  
**API Version**: 1.0
