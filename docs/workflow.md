# Vaitikan E-Commerce Platform - Workflow Documentation

---

## 1. Overview

This document describes the user journeys, data flows, and key algorithms implemented in the Vaitikan Shirt Manufacturing E-Commerce Platform.

---

## 2. User Journeys

### 2.1 Customer Journey

```mermaid
flowchart TD
    A[Visit Website] --> B{Registered?}
    B -->|No| C[Register Account]
    C --> D[Login]
    B -->|Yes| D
    D --> E[Browse Products]
    E --> F[View Product Details]
    F --> G[Select Variant & Size]
    G --> H[Add to Cart]
    H --> I{Continue Shopping?}
    I -->|Yes| E
    I -->|No| J[View Cart]
    J --> K[Proceed to Checkout]
    K --> L[Select/Add Address]
    L --> M[Place Order]
    M --> N[Pay Advance 50%]
    N --> O{Payment Success?}
    O -->|No| P[Retry Payment]
    P --> N
    O -->|Yes| Q[Order Confirmed]
    Q --> R[Manufacturing/Processing]
    R --> S[Ready for Dispatch]
    S --> T[Pay Final 50%]
    T --> U{Payment Success?}
    U -->|No| V[Retry Payment]
    V --> T
    U -->|Yes| W[Order Dispatched]
    W --> X[Order Delivered]
    X --> Y[Submit Feedback]
    Y --> Z[End]
```

#### Step-by-Step Customer Flow:

1. **Registration**
   - User provides: email, full_name, password
   - System creates User record with `user_type='customer'`
   - Password hashed using Django's PBKDF2 algorithm

2. **Login**
   - User submits email and password
   - System validates credentials
   - Returns JWT access token (15 min) and refresh token (7 days)

3. **Product Browsing**
   - User browses product catalog (no auth required)
   - Products displayed with primary image and price range
   - Filtering by fabric, color, pattern, size available

4. **Product Selection**
   - User views product details with all variants
   - Selects specific variant (fabric + color + pattern + sleeve + pocket)
   - Selects size (price adjusts based on size markup)
   - Checks stock availability

5. **Add to Cart**
   - System creates/retrieves active cart for user
   - CartItem created linking cart → variant_size
   - Stock validation performed (quantity ≤ available stock)

6. **Checkout**
   - User reviews cart contents
   - Selects delivery address (or adds new one)
   - Confirms order with optional notes

7. **Order Creation**
   - Cart status changed to 'checked_out'
   - Order record created with status 'pending'
   - OrderItems created with snapshot_unit_price (frozen)
   - Stock reserved: `Stock.quantity_reserved += quantity`

8. **Advance Payment (50%)**
   - Payment record created with `payment_type='advance'`
   - Razorpay order created for 50% of order total
   - User completes payment via Razorpay checkout
   - On success: Order status → 'confirmed'

9. **Manufacturing/Processing**
   - Operator views order material requirements
   - Raw materials consumed from inventory
   - Order status → 'processing'

10. **Final Payment (50%)**
    - When ready for dispatch, final payment triggered
    - Payment record created with `payment_type='final'`
    - User completes remaining 50% payment

11. **Dispatch & Delivery**
    - Order status → 'dispatched'
    - Expected delivery date set
    - Order status → 'delivered' on completion

12. **Feedback**
    - User can submit feedback with rating (1-5)
    - Feedback linked to order record

---

### 2.2 Admin Journey

```mermaid
flowchart TD
    A[Admin Login] --> B[View Dashboard]
    B --> C{Select Action}
    C --> D[Product Management]
    C --> E[Order Management]
    C --> F[User Management]
    C --> G[View Reports]
    C --> H[Support Module]
    
    D --> D1[Add Product]
    D --> D2[Add Variant]
    D --> D3[Upload Images]
    D --> D4[Manage Stock]
    
    E --> E1[View Orders]
    E --> E2[Update Status]
    E --> E3[View Materials]
    E --> E4[Generate Invoice]
    
    F --> F1[View Users]
    F --> F2[Create Operator]
    F --> F3[Manage Status]
    
    G --> G1[Sales Report]
    G --> G2[Order Report]
    G --> G3[Financial Report]
    
    H --> H1[View Inquiries]
    H --> H2[Create Quotation]
    H --> H3[Handle Complaints]
```

#### Admin Responsibilities:
1. **Dashboard Access**: View sales metrics, pending orders, low stock alerts
2. **Product Management**: Create products, variants, manage images and pricing
3. **Order Processing**: Update order status through the fulfillment pipeline
4. **User Management**: Create operator accounts, manage user statuses
5. **Reporting**: Generate sales, order, and financial reports
6. **Support**: Handle customer inquiries, create quotations, resolve complaints

---

### 2.3 Operator Journey

```mermaid
flowchart TD
    A[Operator Login] --> B[View Dashboard]
    B --> C{Select Action}
    C --> D[Inventory Management]
    C --> E[Order Management]
    C --> F[Manufacturing Specs]
    
    D --> D1[View Materials]
    D --> D2[Update Quantities]
    D --> D3[Check Reorder Alerts]
    D --> D4[Manage Suppliers]
    
    E --> E1[View Orders]
    E --> E2[View Material Requirements]
    E --> E3[Consume Materials]
    E --> E4[Update Order Status]
    
    F --> F1[View Specifications]
    F --> F2[Create Specification]
    F --> F3[Edit Specification]
```

#### Operator Responsibilities:
1. **Inventory Tracking**: Monitor raw material quantities, update stock levels
2. **Reorder Management**: Identify materials below reorder level, place orders with suppliers
3. **Material Consumption**: Deduct materials based on order manufacturing requirements
4. **Manufacturing Specs**: Define material requirements per product variant-size

---

## 3. Data Flow Diagrams

### 3.1 Order Creation Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API/Views
    participant OS as OrderService
    participant CS as CartService
    participant DB as Database
    
    U->>F: Click "Place Order"
    F->>A: POST /api/orders/
    A->>CS: get_cart_for_user(user)
    CS->>DB: SELECT Cart, CartItems
    DB-->>CS: Cart with items
    CS-->>A: Cart data
    
    A->>OS: create_order(user, address, cart)
    
    Note over OS,DB: Transaction Start
    OS->>DB: INSERT Order
    DB-->>OS: Order created
    
    loop For each CartItem
        OS->>DB: INSERT OrderItem (snapshot_unit_price)
        OS->>DB: UPDATE Stock (quantity_reserved += quantity)
    end
    
    OS->>DB: UPDATE Cart (status='checked_out')
    Note over OS,DB: Transaction Commit
    
    OS-->>A: Order object
    A-->>F: Order response JSON
    F-->>U: Order confirmation page
```

### 3.2 Payment Processing Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API/Views
    participant PS as PaymentService
    participant RP as Razorpay
    participant DB as Database
    
    U->>F: Click "Pay Now"
    F->>A: POST /api/payments/create/
    A->>PS: create_payment(order_id, payment_type)
    
    PS->>DB: Get Order with total
    DB-->>PS: Order data
    
    PS->>PS: Calculate amount (50% or remaining)
    
    PS->>RP: Create Razorpay Order
    RP-->>PS: razorpay_order_id
    
    PS->>DB: INSERT Payment (status='initiated')
    DB-->>PS: Payment created
    
    PS-->>A: Payment + Razorpay details
    A-->>F: {razorpay_order_id, key_id, amount}
    
    F->>RP: Open Razorpay Checkout
    U->>RP: Complete Payment
    RP->>F: Payment Success Callback
    
    F->>A: POST /api/payments/verify/
    A->>PS: verify_payment(razorpay_payment_id, signature)
    
    PS->>RP: Verify Signature
    RP-->>PS: Verification result
    
    alt Success
        PS->>DB: UPDATE Payment (status='success', paid_at)
        PS->>DB: UPDATE Order status if applicable
        PS-->>A: Success response
    else Failure
        PS->>DB: UPDATE Payment (status='failed', reason)
        PS-->>A: Failure response
    end
    
    A-->>F: Payment result
    F-->>U: Success/Failure page
```

### 3.3 Material Consumption Data Flow

```mermaid
sequenceDiagram
    participant O as Operator
    participant F as Frontend
    participant A as API/Views
    participant DB as Database
    
    O->>F: View Order Material Requirements
    F->>A: GET /admin/orders/{id}/materials/
    A->>DB: SELECT OrderItems with ManufacturingSpecs
    
    Note over A,DB: Calculate Requirements
    loop For each OrderItem
        A->>DB: SELECT ManufacturingSpecification WHERE variant_size_id
        A->>A: total_required = spec.quantity_required * order_item.quantity
    end
    
    DB-->>A: Material requirements
    A-->>F: Requirements list
    F-->>O: Display material requirements
    
    O->>F: Click "Consume Materials"
    F->>A: POST /consume-materials/
    
    Note over A,DB: Transaction Start
    loop For each material
        A->>DB: UPDATE RawMaterial SET current_quantity -= consumed
    end
    Note over A,DB: Transaction Commit
    
    A-->>F: Success response
    F-->>O: Materials consumed confirmation
```

---

## 4. Key Algorithms

### 4.1 Price Calculation Algorithm

The final price for a product variant-size is calculated using size-based markups:

```python
# Algorithm: Calculate Final Price

def calculate_final_price(variant_size):
    """
    Calculate the final price for a variant-size combination.
    
    Formula: final_price = base_price * (1 + size_markup_percentage / 100)
    
    Args:
        variant_size: VariantSize object containing variant and size references
        
    Returns:
        Decimal: Final price rounded to 2 decimal places
    """
    base_price = variant_size.variant.base_price  # From ProductVariant
    size_markup = variant_size.size.size_markup_percentage  # From Size table
    
    # Apply markup
    markup_multiplier = Decimal('1') + (size_markup / Decimal('100'))
    final_price = base_price * markup_multiplier
    
    return final_price.quantize(Decimal('0.01'))

# Example:
# Base Price: ₹1500.00
# Size: XL with 5% markup
# Final Price: ₹1500 * 1.05 = ₹1575.00
```

### 4.2 Stock Availability Algorithm

```python
# Algorithm: Check and Reserve Stock

def check_and_reserve_stock(variant_size_id, quantity):
    """
    Check stock availability and reserve if sufficient.
    
    Process:
    1. Get stock record for variant_size
    2. Calculate available = in_stock - reserved
    3. If quantity <= available, reserve stock
    4. Else, raise InsufficientStockError
    
    Returns:
        bool: True if reservation successful
    """
    stock = Stock.objects.select_for_update().get(
        variant_size_id=variant_size_id
    )
    
    available = stock.quantity_in_stock - stock.quantity_reserved
    
    if quantity > available:
        raise InsufficientStockError(
            f"Requested {quantity}, only {available} available"
        )
    
    # Reserve stock
    stock.quantity_reserved += quantity
    stock.save()
    
    return True
```

### 4.3 Material Requirements Calculation

```python
# Algorithm: Calculate Order Material Requirements

def calculate_material_requirements(order):
    """
    Calculate total raw material requirements for an order.
    
    Process:
    1. For each order item, get the variant_size
    2. Look up ManufacturingSpecification for that variant_size
    3. Multiply spec.quantity_required by order_item.quantity
    4. Aggregate by material across all items
    
    Returns:
        Dict[material_id, Decimal]: Total quantity required per material
    """
    requirements = defaultdict(Decimal)
    
    for item in order.items.all():
        specifications = ManufacturingSpecification.objects.filter(
            variant_size=item.variant_size
        ).select_related('material', 'material__material_type')
        
        for spec in specifications:
            total_needed = spec.quantity_required * item.quantity
            requirements[spec.material.id] += total_needed
    
    return dict(requirements)

# Example:
# Order: 10 units of "Blue Cotton Shirt - Size M"
# Manufacturing Spec: 
#   - Cotton Fabric: 1.5 meters per unit
#   - Thread: 50 meters per unit
#   - Buttons: 7 per unit
# 
# Result:
#   - Cotton Fabric: 15 meters
#   - Thread: 500 meters
#   - Buttons: 70 units
```

### 4.4 Two-Stage Payment Algorithm

```python
# Algorithm: Payment Staging Logic

def calculate_payment_amount(order, payment_type):
    """
    Calculate payment amount based on payment type and order history.
    
    Business Rule:
    - 'advance': 50% of order total (required at order confirmation)
    - 'final': Remaining 50% (required before dispatch)
    - 'full': 100% (for orders without staged payments)
    
    Args:
        order: Order object
        payment_type: 'advance', 'final', or 'full'
        
    Returns:
        Decimal: Amount to be charged
    """
    total_amount = order.total_amount
    
    # Get successful payments for this order
    paid_amount = Payment.objects.filter(
        order=order,
        payment_status='success'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    if payment_type == 'advance':
        # 50% of total
        return (total_amount * Decimal('0.50')).quantize(Decimal('0.01'))
    
    elif payment_type == 'final':
        # Remaining amount (should be ~50%)
        return (total_amount - paid_amount).quantize(Decimal('0.01'))
    
    elif payment_type == 'full':
        return total_amount
```

### 4.5 Invoice Generation Algorithm

```python
# Algorithm: Invoice Generation

def generate_invoice(order):
    """
    Generate PDF invoice for an order.
    
    Process:
    1. Generate unique invoice number (format: INV-YYYYMMDD-XXXX)
    2. Calculate line items with GST
    3. Generate PDF using ReportLab
    4. Store PDF (Cloudinary/Local)
    5. Create Invoice record
    
    Returns:
        Invoice: Created invoice object
    """
    # Generate unique invoice number
    date_prefix = datetime.now().strftime('%Y%m%d')
    sequence = Invoice.objects.filter(
        invoice_number__startswith=f'INV-{date_prefix}'
    ).count() + 1
    invoice_number = f'INV-{date_prefix}-{sequence:04d}'
    
    # Calculate totals with tax
    subtotal = order.total_amount
    tax_config = TaxConfiguration.objects.filter(
        is_active=True,
        effective_from__lte=date.today()
    ).first()
    
    tax_amount = Decimal('0')
    if tax_config:
        tax_amount = subtotal * (tax_config.tax_percentage / 100)
    
    total_with_tax = subtotal + tax_amount
    
    # Generate PDF
    pdf_buffer = create_invoice_pdf(
        order=order,
        invoice_number=invoice_number,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total=total_with_tax
    )
    
    # Store and create record
    invoice = Invoice.objects.create(
        order=order,
        invoice_number=invoice_number,
        total_amount=total_with_tax,
        invoice_url=store_pdf(pdf_buffer)
    )
    
    return invoice
```

### 4.6 Quotation Pricing Algorithm

```python
# Algorithm: Bulk Quotation Pricing

def calculate_quotation_price(variant_size, quantity, customization_type=None):
    """
    Calculate bulk pricing with quantity discounts and customization charges.
    
    Discount Tiers:
    - 100-499 units: 5% discount
    - 500-999 units: 10% discount
    - 1000+ units: 15% discount
    
    Customization Charges:
    - Logo printing: ₹25 per unit
    - Custom label: ₹15 per unit
    - Embroidery: ₹50 per unit
    """
    base_price = calculate_final_price(variant_size)
    
    # Apply quantity discount
    if quantity >= 1000:
        discount = Decimal('0.15')
    elif quantity >= 500:
        discount = Decimal('0.10')
    elif quantity >= 100:
        discount = Decimal('0.05')
    else:
        discount = Decimal('0')
    
    discounted_price = base_price * (1 - discount)
    
    # Add customization charge
    customization_charges = {
        'logo_printing': Decimal('25.00'),
        'custom_label': Decimal('15.00'),
        'embroidery': Decimal('50.00'),
    }
    
    customization_charge = customization_charges.get(
        customization_type, Decimal('0')
    )
    
    final_unit_price = discounted_price + customization_charge
    
    return {
        'unit_price': final_unit_price,
        'quantity': quantity,
        'customization_charge': customization_charge,
        'total_amount': final_unit_price * quantity
    }
```

---

## 5. State Machines

### 5.1 Order Status State Machine

```mermaid
stateDiagram-v2
    [*] --> pending: Order Created
    
    pending --> confirmed: Advance Payment Success
    pending --> cancelled: User Cancel / Payment Failed
    
    confirmed --> processing: Manufacturing Started
    confirmed --> cancelled: Admin Cancel
    
    processing --> dispatched: Final Payment + Shipping
    processing --> cancelled: Manufacturing Issue
    
    dispatched --> delivered: Delivery Confirmed
    
    delivered --> [*]
    cancelled --> [*]
```

### 5.2 Payment Status State Machine

```mermaid
stateDiagram-v2
    [*] --> initiated: Payment Created
    
    initiated --> pending: Razorpay Order Created
    
    pending --> success: Payment Verified
    pending --> failed: Verification Failed
    
    failed --> pending: Retry Payment
    
    success --> [*]
```

### 5.3 Inquiry Status State Machine

```mermaid
stateDiagram-v2
    [*] --> pending: Inquiry Submitted
    
    pending --> reviewed: Admin Reviews
    
    reviewed --> quoted: Quotation Created
    
    quoted --> accepted: Customer Accepts
    quoted --> pending: Customer Requests Changes
    
    accepted --> [*]
```

---

## 6. Background Processes

### 6.1 Abandoned Cart Cleanup

```python
# Scheduled Task: Clean up abandoned carts

def cleanup_abandoned_carts():
    """
    Mark old inactive carts as abandoned.
    Run daily via cron/celery.
    
    Logic:
    - Carts with status='active'
    - Last updated > 7 days ago
    - Mark as 'abandoned'
    """
    cutoff_date = timezone.now() - timedelta(days=7)
    
    Cart.objects.filter(
        status='active',
        updated_at__lt=cutoff_date
    ).update(status='abandoned')
```

### 6.2 Low Stock Alert

```python
# Scheduled Task: Check for low stock

def check_low_stock_alerts():
    """
    Identify materials below reorder level.
    Send notifications to admin/operators.
    
    Logic:
    - Check RawMaterial.current_quantity vs default_reorder_level
    - Check MaterialSupplier.reorder_level for supplier-specific alerts
    """
    low_stock_materials = RawMaterial.objects.filter(
        current_quantity__lte=F('default_reorder_level')
    )
    
    for material in low_stock_materials:
        send_low_stock_alert(material)
```

---

**Document Version**: 1.0  
**Last Updated**: December 2024  
**Author**: Final Year Project Team
