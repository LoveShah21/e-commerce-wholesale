# Vaitikan Shirt Manufacturing E-Commerce Platform

## Project Overview Document

---

## 1. Abstract

### Problem Statement

The traditional wholesale shirt manufacturing industry faces significant operational challenges including manual order processing, lack of real-time inventory visibility, complex pricing calculations for bulk orders, and fragmented customer communication channels. These inefficiencies lead to delayed order fulfillment, stock-outs, pricing errors, and poor customer experience.

### Solution

The **Vaitikan Shirt Manufacturing E-Commerce Platform** is a comprehensive, production-grade B2B e-commerce solution specifically designed for wholesale shirt manufacturing businesses. The platform provides:

- **End-to-End Order Management**: From product browsing and cart management to order placement, payment processing, and delivery tracking
- **Multi-Variant Product Catalog**: Support for complex shirt configurations (fabric, color, pattern, sleeve type, pocket style, and size) with dynamic pricing
- **Manufacturing-Integrated Inventory System**: Raw material tracking, manufacturing specifications, and automated material requirement calculations
- **Two-Stage Payment Processing**: 50% advance payment at order confirmation, 50% final payment before dispatch via Razorpay integration
- **Role-Based Access Control**: Distinct portals for Customers, Operators (inventory/manufacturing staff), and Administrators
- **Customer Service Module**: Inquiry management, bulk quotation requests, complaint handling, and feedback collection
- **Analytics Dashboard**: Real-time sales metrics, low stock alerts, and order statistics for business intelligence

The platform bridges the gap between traditional manufacturing operations and modern e-commerce expectations, enabling businesses to serve wholesale customers efficiently while maintaining precise control over inventory and manufacturing workflows.

---

## 2. Tech Stack

### 2.1 Core Framework

| Component | Technology | Version |
|-----------|------------|---------|
| **Language** | Python | 3.11+ |
| **Web Framework** | Django | 5.2 |
| **API Framework** | Django REST Framework | Latest |
| **ASGI/WSGI Server** | Django (Development) | - |

### 2.2 Database

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Primary Database** | MySQL | 8.4+ | Main data storage |
| **ORM** | Django ORM | Database abstraction |
| **URL Parser** | dj-database-url | Database URL configuration |
| **MySQL Client** | mysqlclient | MySQL Python connector |

### 2.3 Authentication & Security

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Authentication** | djangorestframework-simplejwt | JWT token management |
| **Token Blacklisting** | rest_framework_simplejwt.token_blacklist | Secure logout |
| **Password Validation** | Django Auth Validators | Password strength enforcement |
| **Rate Limiting** | django-ratelimit | API abuse prevention |
| **Input Sanitization** | bleach | XSS prevention |
| **File Validation** | python-magic | MIME type verification |

### 2.4 Payment Gateway

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Payment Processor** | Razorpay | Payment handling (UPI, Cards, NetBanking, Wallets) |
| **Payment SDK** | razorpay (Python) | Server-side integration |

### 2.5 Storage & Media

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Cloud Storage** | Cloudinary | Product images, inquiry logos |
| **Storage Integration** | django-cloudinary-storage | Django file storage backend |
| **Image Processing** | Pillow | Image manipulation |

### 2.6 Caching & Performance

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Cache Backend** | Redis (Production) | Distributed caching |
| **Cache Client** | django-redis | Django Redis integration |
| **Fallback Cache** | LocMemCache | Development local cache |

### 2.7 Utilities

| Component | Technology | Purpose |
|-----------|------------|---------|
| **PDF Generation** | ReportLab | Invoice PDF creation |
| **CORS Handling** | django-cors-headers | Cross-origin request support |
| **Filtering** | django-filter | API filter backends |
| **Environment Config** | python-decouple | Environment variable management |
| **Email** | Django SMTP Backend (Gmail) | Email notifications |

### 2.8 Development & Testing

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Testing Framework** | pytest / Django Test | Unit and integration tests |
| **Property-Based Testing** | hypothesis | Automated test case generation |
| **Logging** | Python logging | Application and security logging |

### 2.9 Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND CLIENTS                          │
│  (Web Browser - Django Templates / Mobile App / Third-Party)    │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DJANGO APPLICATION                          │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │   Web Views     │  │   REST API       │  │   Admin Panel  │  │
│  │   (Templates)   │  │   (DRF)          │  │   (Django)     │  │
│  └─────────────────┘  └──────────────────┘  └────────────────┘  │
│                               │                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    BUSINESS LOGIC LAYER                      │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐│ │
│  │  │Cart Svc  │ │Order Svc │ │Payment   │ │Invoice/Email Svc ││ │
│  │  └──────────┘ └──────────┘ │Service   │ └──────────────────┘│ │
│  │                            └──────────┘                      │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                               │                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                       DJANGO ORM                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────┐        ┌──────────────┐        ┌──────────────┐
│   MySQL     │        │   Redis      │        │  Cloudinary  │
│   Database  │        │   Cache      │        │  (Media)     │
└─────────────┘        └──────────────┘        └──────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │    Razorpay      │
                    │  Payment Gateway │
                    └──────────────────┘
```

---

## 3. System Architecture

### 3.1 High-Level Architecture

The application follows a **Layered Architecture** pattern with clear separation of concerns:

1. **Presentation Layer**: Django Templates (server-side rendering) + REST API endpoints
2. **Business Logic Layer**: Service classes handling complex operations
3. **Data Access Layer**: Django ORM with model definitions
4. **External Services Layer**: Razorpay, Cloudinary, Gmail SMTP

### 3.2 Application Modules

The backend is organized into **7 Django applications**:

| App | Purpose | Key Models |
|-----|---------|------------|
| **users** | User authentication, address management | User, Address, Country, State, City, PostalCode |
| **products** | Product catalog, variants, stock | Product, ProductVariant, VariantSize, Stock, Fabric, Color, Pattern, Sleeve, Pocket, Size |
| **orders** | Shopping cart, order processing | Cart, CartItem, Order, OrderItem |
| **finance** | Payments, invoices, taxes | Payment, Invoice, TaxConfiguration |
| **manufacturing** | Raw materials, suppliers, specifications | RawMaterial, MaterialType, Supplier, ManufacturingSpecification, MaterialSupplier |
| **support** | Inquiries, quotations, complaints, feedback | Inquiry, QuotationRequest, QuotationPrice, Complaint, Feedback |
| **dashboard** | Analytics and reporting | (Views only - aggregates data from other models) |

### 3.3 Frontend-Backend Interaction

#### Web Interface (Django Templates)
- Server-side rendered HTML pages
- Session-based authentication for web users
- Form submissions handled via POST requests
- CSRF protection enabled

#### REST API (Django REST Framework)
- Stateless authentication via JWT tokens
- JSON request/response format
- Paginated responses (20 items per page default)
- Filter, search, and ordering support
- Rate limiting on sensitive endpoints

### 3.4 Database Interaction

```
┌──────────────────────────────────────────────────────────────────┐
│                     DJANGO ORM LAYER                              │
├──────────────────────────────────────────────────────────────────┤
│  Views/Serializers  →  Service Layer  →  Django Models  →  MySQL │
│                                                                   │
│  QuerySets provide:                                               │
│  • Lazy evaluation                                                │
│  • Automatic SQL generation                                       │
│  • Connection pooling (conn_max_age=600)                         │
│  • Transaction management                                         │
└──────────────────────────────────────────────────────────────────┘
```

**Key Database Design Decisions:**
- **Normalized schema** with foreign key relationships
- **Composite unique constraints** (e.g., ProductVariant: product + fabric + color + pattern + sleeve + pocket)
- **Computed properties** via Python (e.g., `Stock.quantity_available`)
- **Price snapshots** in OrderItem to preserve historical pricing
- **Soft foreign keys** using `on_delete=RESTRICT` for referential integrity

### 3.5 External Service Integration

| Service | Integration Point | Purpose |
|---------|-------------------|---------|
| **Razorpay** | Payment Service | Create orders, verify payments, handle webhooks |
| **Cloudinary** | CloudinaryField (Model) | Upload/serve product images, inquiry logos |
| **Gmail SMTP** | Email Service | Order confirmations, password resets |
| **Redis** | Cache Middleware | Session caching, rate limiting counters |

### 3.6 Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SECURITY LAYERS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. TRANSPORT SECURITY                                           │
│     └── HTTPS enforcement (production)                           │
│     └── HTTP → HTTPS redirect                                    │
│                                                                   │
│  2. AUTHENTICATION                                                │
│     └── JWT tokens (15 min access, 7 day refresh)                │
│     └── Session auth for web views                               │
│     └── Token blacklisting on logout                             │
│                                                                   │
│  3. AUTHORIZATION                                                 │
│     └── Role-based: Customer, Operator, Admin                    │
│     └── Permission classes per view                              │
│                                                                   │
│  4. INPUT VALIDATION                                              │
│     └── DRF Serializer validation                                │
│     └── Django form validation                                   │
│     └── bleach sanitization for XSS                              │
│                                                                   │
│  5. RATE LIMITING                                                │
│     └── 5 req/min on auth endpoints                              │
│     └── 10 req/min on payment endpoints                          │
│     └── 100 req/min general endpoints                            │
│                                                                   │
│  6. SECURITY HEADERS                                              │
│     └── X-Frame-Options: DENY                                    │
│     └── X-Content-Type-Options: nosniff                          │
│     └── Content-Security-Policy                                  │
│     └── HSTS (production)                                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Key Features Summary

| Feature Category | Capabilities |
|------------------|--------------|
| **Product Management** | Multi-variant products, size-based pricing, stock tracking, image galleries |
| **Order Processing** | Cart management, checkout, status tracking (pending → confirmed → processing → dispatched → delivered) |
| **Payment Handling** | Two-stage payments (50/50 split), Razorpay integration, payment verification |
| **Invoice Generation** | PDF invoices with GST, automatic invoice numbering |
| **Inventory Control** | Raw material tracking, reorder alerts, supplier management |
| **Manufacturing** | Material specifications per variant-size, consumption calculation |
| **Customer Support** | Inquiry system, bulk quotations, complaint management, feedback |
| **Analytics** | Sales trends, order statistics, low stock alerts |
| **User Management** | Registration, authentication, profile management, address book |

---

## 5. Conclusion

The Vaitikan Shirt Manufacturing E-Commerce Platform represents a comprehensive solution for modernizing wholesale shirt manufacturing operations. By leveraging Django's robust ecosystem and integrating with industry-standard services like Razorpay and Cloudinary, the platform delivers a scalable, secure, and feature-rich e-commerce experience tailored to the unique requirements of the manufacturing industry.

---

**Document Version**: 1.0  
**Last Updated**: December 2024  
**Author**: Final Year Project Team
