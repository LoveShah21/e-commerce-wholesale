---

# Vaitikan City – Database Design (Production-Ready)

## 1. Design Goals

- Support full shirt manufacturing workflow: catalog, inventory, manufacturing, orders, payments (50% advance + 50% before dispatch), customization, complaints.
- Be normalized enough to avoid anomalies, but aligned with real manufacturing behavior.
- Make pricing, payments, stock, and consumption logically correct and easy to extend.

Tech target: MySQL 8.x.

---

## 2. Core Domain Concepts

- **User \& Address**: Customers and admins, with normalized address lookup.
- **Product Catalog**: Product → Variant → VariantSize.
- **Inventory \& Manufacturing**: RawMaterial, MaterialType, ManufacturingSpecification.
- **Ordering**: Cart, CartItem, Order, OrderItem.
- **Payments \& Invoices**: Multiple payments per order, invoice per order.
- **Service**: Inquiry, Quotation, Complaint, Feedback.

---

## 3. Reference \& Configuration Tables

### 3.1 TaxConfiguration

Stores GST and future tax rules, time-bounded.

```sql
CREATE TABLE TaxConfiguration (
    tax_config_id INT PRIMARY KEY AUTO_INCREMENT,
    tax_name VARCHAR(50) NOT NULL,
    tax_percentage DECIMAL(5,2) NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_tax_period (tax_name, effective_from)
);
```

---

### 3.2 Geography: Country, State, City, PostalCode

Used by Address; can be simplified if overkill for your case.

```sql
CREATE TABLE Country (
    country_id INT PRIMARY KEY AUTO_INCREMENT,
    country_code VARCHAR(2) NOT NULL UNIQUE,
    country_name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE State (
    state_id INT PRIMARY KEY AUTO_INCREMENT,
    country_id INT NOT NULL,
    state_code VARCHAR(5),
    state_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_state (country_id, state_code),
    FOREIGN KEY (country_id) REFERENCES Country(country_id),
    INDEX idx_country_id (country_id)
);

CREATE TABLE City (
    city_id INT PRIMARY KEY AUTO_INCREMENT,
    state_id INT NOT NULL,
    city_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_city (state_id, city_name),
    FOREIGN KEY (state_id) REFERENCES State(state_id),
    INDEX idx_state_id (state_id)
);

CREATE TABLE PostalCode (
    postal_code_id INT PRIMARY KEY AUTO_INCREMENT,
    city_id INT NOT NULL,
    postal_code VARCHAR(10) NOT NULL,
    area_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_postal_code (postal_code),
    FOREIGN KEY (city_id) REFERENCES City(city_id),
    INDEX idx_city_id (city_id)
);
```

---

### 3.3 MaterialType \& Supplier

```sql
CREATE TABLE MaterialType (
    material_type_id INT PRIMARY KEY AUTO_INCREMENT,
    material_type_name VARCHAR(50) NOT NULL UNIQUE,
    unit_of_measurement VARCHAR(20) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Supplier (
    supplier_id INT PRIMARY KEY AUTO_INCREMENT,
    supplier_name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(15),
    city_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (city_id) REFERENCES City(city_id),
    INDEX idx_supplier_name (supplier_name)
);
```

---

## 4. User \& Address

### 4.1 User

```sql
CREATE TABLE User (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    user_type ENUM('customer', 'admin', 'operator') NOT NULL DEFAULT 'customer',
    account_status ENUM('active', 'inactive', 'suspended') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_email (email),
    INDEX idx_phone (phone),
    INDEX idx_user_type (user_type)
);
```

### 4.2 Address

```sql
CREATE TABLE Address (
    address_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    postal_code_id INT NOT NULL,
    address_type ENUM('home', 'office', 'other') DEFAULT 'other',
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (postal_code_id) REFERENCES PostalCode(postal_code_id),
    INDEX idx_user_id (user_id)
);

CREATE VIEW AddressDetail AS
SELECT
    a.address_id,
    a.user_id,
    a.address_line1,
    a.address_line2,
    c.city_name,
    s.state_name,
    co.country_name,
    pc.postal_code,
    a.is_default
FROM Address a
JOIN PostalCode pc ON a.postal_code_id = pc.postal_code_id
JOIN City c ON pc.city_id = c.city_id
JOIN State s ON c.state_id = s.state_id
JOIN Country co ON s.country_id = co.country_id;
```

---

## 5. Product Catalog

### 5.1 Attribute Dimension Tables

```sql
CREATE TABLE Fabric (
    fabric_id INT PRIMARY KEY AUTO_INCREMENT,
    fabric_name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Color (
    color_id INT PRIMARY KEY AUTO_INCREMENT,
    color_name VARCHAR(50) NOT NULL UNIQUE,
    hex_code VARCHAR(7),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Pattern (
    pattern_id INT PRIMARY KEY AUTO_INCREMENT,
    pattern_name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Sleeve (
    sleeve_id INT PRIMARY KEY AUTO_INCREMENT,
    sleeve_type VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Pocket (
    pocket_id INT PRIMARY KEY AUTO_INCREMENT,
    pocket_type VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.2 Size

```sql
CREATE TABLE Size (
    size_id INT PRIMARY KEY AUTO_INCREMENT,
    size_code VARCHAR(10) NOT NULL UNIQUE,
    size_name VARCHAR(50) NOT NULL,
    size_markup_percentage DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.3 Product \& ProductImage

```sql
CREATE TABLE Product (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_product_name (product_name)
);

CREATE TABLE ProductImage (
    image_id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    alt_text VARCHAR(200),
    is_primary BOOLEAN DEFAULT FALSE,
    display_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE CASCADE,
    INDEX idx_product_id (product_id)
);
```

### 5.4 ProductVariant (source of price truth)

```sql
CREATE TABLE ProductVariant (
    variant_id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL,
    fabric_id INT NOT NULL,
    color_id INT NOT NULL,
    pattern_id INT NOT NULL,
    sleeve_id INT NOT NULL,
    pocket_id INT NOT NULL,
    base_price DECIMAL(10,2) NOT NULL,
    sku VARCHAR(50) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE CASCADE,
    FOREIGN KEY (fabric_id) REFERENCES Fabric(fabric_id),
    FOREIGN KEY (color_id) REFERENCES Color(color_id),
    FOREIGN KEY (pattern_id) REFERENCES Pattern(pattern_id),
    FOREIGN KEY (sleeve_id) REFERENCES Sleeve(sleeve_id),
    FOREIGN KEY (pocket_id) REFERENCES Pocket(pocket_id),
    UNIQUE KEY uk_variant (product_id, fabric_id, color_id, pattern_id, sleeve_id, pocket_id),
    INDEX idx_product_id (product_id)
);
```

### 5.5 VariantSize

```sql
CREATE TABLE VariantSize (
    variant_size_id INT PRIMARY KEY AUTO_INCREMENT,
    variant_id INT NOT NULL,
    size_id INT NOT NULL,
    stock_quantity INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_variant_size (variant_id, size_id),
    FOREIGN KEY (variant_id) REFERENCES ProductVariant(variant_id) ON DELETE CASCADE,
    FOREIGN KEY (size_id) REFERENCES Size(size_id),
    INDEX idx_variant_id (variant_id)
);

CREATE VIEW VariantSizePrice AS
SELECT
    vs.variant_size_id,
    vs.variant_id,
    vs.size_id,
    pv.base_price,
    s.size_markup_percentage,
    (pv.base_price * (1 + s.size_markup_percentage / 100)) AS final_price,
    vs.stock_quantity
FROM VariantSize vs
JOIN ProductVariant pv ON vs.variant_id = pv.variant_id
JOIN Size s ON vs.size_id = s.size_id;
```

### 5.6 Stock

```sql
CREATE TABLE Stock (
    stock_id INT PRIMARY KEY AUTO_INCREMENT,
    variant_size_id INT NOT NULL,
    quantity_in_stock INT DEFAULT 0,
    quantity_reserved INT DEFAULT 0,
    quantity_available INT GENERATED ALWAYS AS (quantity_in_stock - quantity_reserved) STORED,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (variant_size_id) REFERENCES VariantSize(variant_size_id) ON DELETE CASCADE,
    UNIQUE KEY uk_variant_size (variant_size_id),
    INDEX idx_quantity_available (quantity_available)
);
```

---

## 6. Inventory \& Manufacturing

### 6.1 RawMaterial \& MaterialSupplier

```sql
CREATE TABLE RawMaterial (
    material_id INT PRIMARY KEY AUTO_INCREMENT,
    material_name VARCHAR(100) NOT NULL,
    material_type_id INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    current_quantity DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_material_type (material_name, material_type_id),
    FOREIGN KEY (material_type_id) REFERENCES MaterialType(material_type_id),
    INDEX idx_material_type_id (material_type_id)
);

CREATE TABLE MaterialSupplier (
    material_supplier_id INT PRIMARY KEY AUTO_INCREMENT,
    material_id INT NOT NULL,
    supplier_id INT NOT NULL,
    supplier_price DECIMAL(10,2),
    min_order_quantity DECIMAL(10,2),
    reorder_level DECIMAL(10,2),
    lead_time_days INT,
    is_preferred BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_material_supplier (material_id, supplier_id),
    FOREIGN KEY (material_id) REFERENCES RawMaterial(material_id) ON DELETE CASCADE,
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id),
    INDEX idx_material_id (material_id)
);
```

### 6.2 ManufacturingSpecification (fixed)

```sql
CREATE TABLE ManufacturingSpecification (
    spec_id INT PRIMARY KEY AUTO_INCREMENT,
    variant_size_id INT NOT NULL,
    material_id INT NOT NULL,
    quantity_required DECIMAL(8,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_variant_material (variant_size_id, material_id),
    FOREIGN KEY (variant_size_id) REFERENCES VariantSize(variant_size_id),
    FOREIGN KEY (material_id) REFERENCES RawMaterial(material_id),
    INDEX idx_variant_size_id (variant_size_id)
);
```

---

## 7. Cart \& Orders

### 7.1 Cart (fixed)

```sql
CREATE TABLE Cart (
    cart_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,  -- nullable for guest carts
    status ENUM('active', 'checked_out', 'abandoned') DEFAULT 'active',
    guest_email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);
```

### 7.2 CartItem

```sql
CREATE TABLE CartItem (
    cart_item_id INT PRIMARY KEY AUTO_INCREMENT,
    cart_id INT NOT NULL,
    variant_size_id INT NOT NULL,
    quantity INT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cart_id) REFERENCES Cart(cart_id) ON DELETE CASCADE,
    FOREIGN KEY (variant_size_id) REFERENCES VariantSize(variant_size_id),
    UNIQUE KEY uk_cart_variant_size (cart_id, variant_size_id),
    INDEX idx_cart_id (cart_id)
);
```

### 7.3 Order \& OrderItem

```sql
CREATE TABLE `Order` (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    delivery_address_id INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expected_delivery_date DATETIME,
    status ENUM('pending', 'confirmed', 'processing', 'dispatched', 'delivered', 'cancelled') DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE RESTRICT,
    FOREIGN KEY (delivery_address_id) REFERENCES Address(address_id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);

CREATE TABLE OrderItem (
    order_item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    variant_size_id INT NOT NULL,
    quantity INT NOT NULL,
    snapshot_unit_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES `Order`(order_id) ON DELETE CASCADE,
    FOREIGN KEY (variant_size_id) REFERENCES VariantSize(variant_size_id),
    INDEX idx_order_id (order_id)
);

CREATE VIEW OrderItemDetail AS
SELECT
    oi.order_item_id,
    oi.order_id,
    oi.variant_size_id,
    oi.quantity,
    oi.snapshot_unit_price,
    (oi.quantity * oi.snapshot_unit_price) AS item_total
FROM OrderItem oi;
```

---

## 8. Payments \& Invoices

### 8.1 Payment (fixed, multi-payment)

```sql
CREATE TABLE Payment (
    payment_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    payment_type ENUM('advance', 'final', 'full') NOT NULL,
    payment_method ENUM('upi', 'card', 'netbanking', 'wallet') NOT NULL,
    payment_status ENUM('initiated', 'pending', 'success', 'failed', 'retry') DEFAULT 'initiated',
    razorpay_order_id VARCHAR(100),
    razorpay_payment_id VARCHAR(100),
    razorpay_signature VARCHAR(255),
    failure_reason VARCHAR(255),
    paid_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES `Order`(order_id) ON DELETE RESTRICT,
    INDEX idx_order_id (order_id),
    INDEX idx_payment_status (payment_status),
    INDEX idx_razorpay_order_id (razorpay_order_id)
);
```

You can derive per-order totals with a view or queries.

### 8.2 Invoice (reference order, not payment)

```sql
CREATE TABLE Invoice (
    invoice_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    invoice_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    invoice_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES `Order`(order_id) ON DELETE RESTRICT,
    INDEX idx_invoice_number (invoice_number),
    INDEX idx_order_id (order_id)
);
```

---

## 9. Customer Service: Inquiry, Quotation, Complaint, Feedback

### 9.1 Inquiry

```sql
CREATE TABLE Inquiry (
    inquiry_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    inquiry_description TEXT NOT NULL,
    logo_file_url VARCHAR(500),
    inquiry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'reviewed', 'quoted') DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);
```

### 9.2 QuotationRequest \& QuotationPrice

```sql
CREATE TABLE QuotationRequest (
    quotation_id INT PRIMARY KEY AUTO_INCREMENT,
    inquiry_id INT NOT NULL,
    variant_size_id INT NOT NULL,
    requested_quantity INT NOT NULL,
    customization_type VARCHAR(100),
    customization_details TEXT,
    requested_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'quoted', 'accepted', 'rejected') DEFAULT 'pending',
    FOREIGN KEY (inquiry_id) REFERENCES Inquiry(inquiry_id) ON DELETE CASCADE,
    FOREIGN KEY (variant_size_id) REFERENCES VariantSize(variant_size_id),
    INDEX idx_inquiry_id (inquiry_id)
);

CREATE TABLE QuotationPrice (
    quotation_price_id INT PRIMARY KEY AUTO_INCREMENT,
    quotation_id INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    customization_charge_per_unit DECIMAL(10,2) DEFAULT 0,
    quoted_quantity INT NOT NULL,
    valid_from DATETIME NOT NULL,
    valid_until DATETIME NOT NULL,
    quoted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'sent', 'accepted', 'rejected') DEFAULT 'pending',
    FOREIGN KEY (quotation_id) REFERENCES QuotationRequest(quotation_id) ON DELETE CASCADE,
    INDEX idx_quotation_id (quotation_id)
);

CREATE VIEW QuotationDetail AS
SELECT
    qr.quotation_id,
    qr.inquiry_id,
    qr.variant_size_id,
    qp.unit_price,
    qp.customization_charge_per_unit,
    qp.quoted_quantity,
    (qp.unit_price * qp.quoted_quantity) AS product_total,
    (qp.customization_charge_per_unit * qp.quoted_quantity) AS customization_total,
    ((qp.unit_price + qp.customization_charge_per_unit) * qp.quoted_quantity) AS grand_total,
    qp.valid_until,
    qp.status
FROM QuotationRequest qr
JOIN QuotationPrice qp ON qr.quotation_id = qp.quotation_id;
```

### 9.3 Complaint \& Feedback

```sql
CREATE TABLE Complaint (
    complaint_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    order_id INT,
    complaint_description TEXT NOT NULL,
    complaint_category VARCHAR(50) NOT NULL,
    complaint_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('open', 'in_progress', 'resolved', 'closed') DEFAULT 'open',
    resolution_date TIMESTAMP NULL,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES `Order`(order_id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);

CREATE TABLE Feedback (
    feedback_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    order_id INT NOT NULL,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    feedback_description TEXT,
    feedback_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES `Order`(order_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_rating (rating)
);
```

---

## 10. Operational Views (Optional)

### 10.1 OrderPaymentStatus (example)

```sql
CREATE VIEW OrderPaymentStatus AS
SELECT
    o.order_id,
    o.user_id,
    COUNT(p.payment_id) AS total_payments,
    SUM(CASE WHEN p.payment_type = 'advance' AND p.payment_status = 'success' THEN p.amount ELSE 0 END) AS advance_paid,
    SUM(CASE WHEN p.payment_type = 'final'   AND p.payment_status = 'success' THEN p.amount ELSE 0 END) AS final_paid,
    SUM(CASE WHEN p.payment_status = 'success' THEN p.amount ELSE 0 END) AS total_paid
FROM `Order` o
LEFT JOIN Payment p ON o.order_id = p.order_id
GROUP BY o.order_id, o.user_id;
```

### 10.2 OrderMaterialRequirements (example)

```sql
CREATE VIEW OrderMaterialRequirements AS
SELECT
    o.order_id,
    oi.order_item_id,
    oi.variant_size_id,
    oi.quantity AS order_quantity,
    rm.material_id,
    rm.material_name,
    mt.material_type_name,
    mt.unit_of_measurement,
    ms.quantity_required AS qty_per_unit,
    (ms.quantity_required * oi.quantity) AS total_required,
    rm.current_quantity AS stock_available
FROM `Order` o
JOIN OrderItem oi ON o.order_id = oi.order_id
JOIN ManufacturingSpecification ms ON oi.variant_size_id = ms.variant_size_id
JOIN RawMaterial rm ON ms.material_id = rm.material_id
JOIN MaterialType mt ON rm.material_type_id = mt.material_type_id;
```

---

## 11. Notes for Implementation

- Enforce “one active cart per user” in application logic, not DB constraint.
- Payment flow:
  - Insert `Payment` rows with `payment_type='advance'` and `'final'`.
  - Use `OrderPaymentStatus` or equivalent logic to gate dispatch.
- Stock deduction:
  - Use `OrderMaterialRequirements` to compute material consumption before updating `RawMaterial.current_quantity`.
- Taxes:
  - Pick active `TaxConfiguration` record when generating invoices.
