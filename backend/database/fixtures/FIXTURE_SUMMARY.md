# Fixture Data Summary

## Overview

This document provides a detailed summary of all sample data included in the fixtures.

## 1. Location Data (01_locations.json)

### Countries

- India (IN)

### States

- Maharashtra (MH)
- Gujarat (GJ)
- Karnataka (KA)
- Delhi (DL)

### Cities

- Mumbai (Maharashtra)
- Pune (Maharashtra)
- Ahmedabad (Gujarat)
- Surat (Gujarat)
- Bangalore (Karnataka)
- New Delhi (Delhi)

### Postal Codes

- 400001 - Fort, Mumbai
- 400050 - Bandra, Mumbai
- 411001 - Shivajinagar, Pune
- 380001 - Lal Darwaja, Ahmedabad
- 395001 - Athwa, Surat
- 560001 - Bangalore GPO, Bangalore
- 110001 - Connaught Place, New Delhi

## 2. User Data (02_users.json)

### Admin User

- **Email**: admin@vaitikan.com
- **Name**: Admin User
- **Phone**: 9876543210
- **Type**: Admin
- **Permissions**: Full system access

### Operator User

- **Email**: operator@vaitikan.com
- **Name**: Manufacturing Operator
- **Phone**: 9876543211
- **Type**: Operator
- **Permissions**: Manufacturing and inventory management

### Customer Users

#### Customer 1

- **Email**: rajesh.kumar@example.com
- **Name**: Rajesh Kumar
- **Phone**: 9876543212
- **Address**: 123 MG Road, Near City Mall, Fort, Mumbai - 400001

#### Customer 2

- **Email**: priya.sharma@example.com
- **Name**: Priya Sharma
- **Phone**: 9876543213
- **Address**: 456 FC Road, Apartment 5B, Shivajinagar, Pune - 411001

#### Customer 3

- **Email**: amit.patel@example.com
- **Name**: Amit Patel
- **Phone**: 9876543214
- **Address**: 789 SG Highway, Lal Darwaja, Ahmedabad - 380001

## 3. Product Attributes (03_product_attributes.json)

### Fabrics (5)

- Cotton
- Linen
- Silk
- Polyester
- Cotton Blend

### Colors (6)

- White (#FFFFFF)
- Blue (#0000FF)
- Black (#000000)
- Pink (#FFC0CB)
- Grey (#808080)
- Navy Blue (#000080)

### Patterns (5)

- Solid
- Striped
- Checked
- Printed
- Dotted

### Sleeve Types (4)

- Full Sleeve
- Half Sleeve
- Sleeveless
- Three Quarter

### Pocket Types (3)

- No Pocket
- Single Pocket
- Double Pocket

### Sizes (5)

- S (Small) - 0% markup
- M (Medium) - 0% markup
- L (Large) - 5% markup
- XL (Extra Large) - 10% markup
- XXL (Double Extra Large) - 15% markup

## 4. Products (04_products.json)

### Product 1: Classic Formal Shirt

**Description**: Premium quality formal shirt perfect for office and business meetings

**Variants**:

1. Cotton, White, Solid, Full Sleeve, Single Pocket - ₹899 (SKU: VAIT-FORM-COT-WHT-SOL-FS-SP)
2. Cotton, Blue, Solid, Full Sleeve, Single Pocket - ₹899 (SKU: VAIT-FORM-COT-BLU-SOL-FS-SP)
3. Cotton, Black, Solid, Full Sleeve, Single Pocket - ₹899 (SKU: VAIT-FORM-COT-BLK-SOL-FS-SP)
4. Cotton, White, Striped, Full Sleeve, Single Pocket - ₹949 (SKU: VAIT-FORM-COT-WHT-STR-FS-SP)

### Product 2: Casual Cotton Shirt

**Description**: Comfortable casual shirt for everyday wear

**Variants**:

1. Cotton, Blue, Checked, Half Sleeve, No Pocket - ₹699 (SKU: VAIT-CASU-COT-BLU-CHK-HS-NP)
2. Cotton Blend, Grey, Solid, Half Sleeve, Single Pocket - ₹749 (SKU: VAIT-CASU-CBL-GRY-SOL-HS-SP)

### Product 3: Designer Party Shirt

**Description**: Stylish party wear shirt with modern design

**Variants**:

1. Silk, Black, Printed, Full Sleeve, No Pocket - ₹1499 (SKU: VAIT-PART-SIL-BLK-PRT-FS-NP)
2. Silk, Navy Blue, Printed, Full Sleeve, No Pocket - ₹1499 (SKU: VAIT-PART-SIL-NAV-PRT-FS-NP)

## 5. Stock Levels (05_variant_sizes_stock.json)

Total variant sizes: 19
Stock ranges from 15 to 70 units per variant size
All stock is available (no reservations in initial data)

## 6. Orders & Payments (06_orders_payments.json)

### Tax Configuration

- GST: 18% (effective from 2024-01-01)

### Order 1 (Rajesh Kumar)

- **Status**: Confirmed
- **Items**:
  - 2x Classic Formal Shirt (White, M) @ ₹899
  - 1x Classic Formal Shirt (Blue, L) @ ₹943.95
- **Total**: ₹2741.95
- **Advance Payment**: ₹1370.98 (Paid via UPI)
- **Invoice**: INV-2024-001

### Order 2 (Amit Patel)

- **Status**: Processing
- **Items**:
  - 3x Casual Cotton Shirt (Blue Checked, S) @ ₹699
  - 2x Casual Cotton Shirt (Grey, M) @ ₹749
- **Total**: ₹3197.00
- **Advance Payment**: ₹1598.50 (Paid via Card)

### Order 3 (Priya Sharma)

- **Status**: Delivered
- **Items**:
  - 1x Designer Party Shirt (Black, M) @ ₹1499
- **Total**: ₹1769.82
- **Advance Payment**: ₹884.91 (Paid via UPI)
- **Final Payment**: ₹884.91 (Paid via UPI)
- **Invoice**: INV-2024-002

### Active Cart (Priya Sharma)

- 2x Classic Formal Shirt (Blue, M)
- 1x Casual Cotton Shirt (Blue Checked, M)

## 7. Manufacturing Data (07_manufacturing.json)

### Material Types (4)

- Fabric (meters)
- Thread (spools)
- Button (pieces)
- Packaging (pieces)

### Suppliers (3)

1. Mumbai Textiles Ltd (Mumbai) - Contact: Ramesh Gupta
2. Gujarat Fabrics Co (Ahmedabad) - Contact: Kiran Shah
3. Surat Thread Suppliers (Surat) - Contact: Vijay Patel

### Raw Materials (10)

1. Cotton Fabric - White: 500m @ ₹150/m
2. Cotton Fabric - Blue: 450m @ ₹150/m
3. Cotton Fabric - Black: 300m @ ₹155/m
4. Silk Fabric - Black: 150m @ ₹450/m
5. Polyester Thread - White: 200 spools @ ₹25/spool
6. Polyester Thread - Blue: 180 spools @ ₹25/spool
7. Polyester Thread - Black: 150 spools @ ₹25/spool
8. Standard Buttons - White: 5000 pcs @ ₹2/pc
9. Standard Buttons - Black: 4000 pcs @ ₹2/pc
10. Poly Bags: 1000 pcs @ ₹5/pc

### Manufacturing Specifications (13)

Sample specifications for key variant sizes showing material requirements per unit

## 8. Support Data (08_support.json)

### Inquiries (2)

1. **Amit Patel**: Bulk order inquiry for 100 custom shirts with logo

   - Status: Quoted
   - Quotation: ₹850/unit + ₹50/unit customization
   - Valid until: 2024-12-25

2. **Rajesh Kumar**: Bulk order for 50 formal shirts
   - Status: Pending

### Complaints (2)

1. **Priya Sharma** (Order #3): Loose button issue

   - Status: Resolved
   - Resolution: Replacement shirt sent

2. **Rajesh Kumar** (Order #1): Delivery delay
   - Status: In Progress

### Feedback (2)

1. **Priya Sharma** (Order #3): 4/5 stars - Good quality, minor issue resolved
2. **Amit Patel** (Order #2): 5/5 stars - Excellent quality and fit

## Data Relationships

The fixtures demonstrate complete data relationships:

- Users have addresses linked to postal codes, cities, states, and countries
- Products have variants with multiple sizes and stock records
- Orders reference users, addresses, and variant sizes
- Payments are linked to orders with Razorpay integration
- Manufacturing specs connect variant sizes to raw materials
- Support data (inquiries, complaints, feedback) reference users and orders

## Use Cases Covered

1. **Customer Journey**: Browse products → Add to cart → Place order → Make payment → Track delivery → Provide feedback
2. **Admin Operations**: Manage products → Process orders → Handle complaints → Generate invoices
3. **Manufacturing**: View material requirements → Track inventory → Manage suppliers
4. **Bulk Orders**: Submit inquiry → Receive quotation → Accept/reject quote

## Testing Scenarios

The fixture data supports testing:

- User authentication and authorization (3 user types)
- Product catalog browsing and filtering
- Shopping cart operations
- Order placement and payment processing
- Stock management and reservation
- Manufacturing workflow
- Customer support operations
- Invoice generation
- Multi-step payment process (advance + final)
