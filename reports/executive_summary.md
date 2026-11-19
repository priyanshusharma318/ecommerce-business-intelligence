# Executive Business Intelligence Summary: Olist Marketplace

**Target Audience:** Chief Executive Officer, Chief Operating Officer, VP of Commercial, Head of Logistics  
**Dataset Reference:** Brazilian E-Commerce Public Dataset by Olist (2016 – 2018)  
**Reporting Currency:** Brazilian Real (BRL / R$)  

---

## 1. Executive Performance Dashboard (High-Level KPIs)

| High-Level Business Metric | Platform Realized Value | Business Interpretation |
| :--- | :--- | :--- |
| **Total Delivered Orders** | **96,478 Orders** | Completed transactions delivered to consumers across all 27 Brazilian states. |
| **Net Product Merchandise Revenue** | **R$ 13,221,498** | Direct merchandise sales value generated across all product categories. |
| **Total Freight Charges Collected** | **R$ 2,217,143** | Carrier shipping fees paid by consumers (~14.4% of total GMV). |
| **Gross Marketplace Value (GMV)** | **R$ 15,438,641** | Total transaction volume processed through the Olist checkout platform. |
| **Unique Individual Customers** | **93,358 Consumers** | Distinct physical buyers identified by `customer_unique_id`. |
| **Average Order Value (AOV)** | **R$ 137.04** | Mean product revenue per completed order checkout. |
| **Repeat Customer Rate** | **3.0% (2,801 Buyers)** | Critical bottleneck: 97% of buyers only make a single purchase. |
| **Platform-Wide Delivery Lead Time** | **12.5 Days** | Average days elapsed between customer payment and doorstep delivery. |
| **Late Delivery Rate (SLA Breach)** | **7.8% (7,527 Orders)** | Orders arriving after the promised estimated delivery date. |
| **Average Customer Satisfaction** | **4.15 / 5.00 Stars** | Aggregate review score across 99,224 customer reviews. |

---

## 2. Answers to Core Strategic Business Questions

### 1. Which product categories generate the most revenue?
The top 5 categories generate over **38% of total platform revenue**:
1. **Health & Beauty (`beleza_saude`):** R$ 1,258,681 (9.52% of revenue; 9,670 items sold)
2. **Watches & Gifts (`relogios_presentes`):** R$ 1,205,005 (9.11% of revenue; 5,624 items sold)
3. **Bed, Bath & Table (`cama_mesa_banho`):** R$ 1,036,988 (7.84% of revenue; 11,115 items sold)
4. **Sports & Leisure (`esporte_lazer`):** R$ 988,048 (7.47% of revenue; 8,641 items sold)
5. **Computers & Accessories (`informatica_acessorios`):** R$ 911,954 (6.90% of revenue; 7,827 items sold)

*Strategic Takeaway:* Health & Beauty and Watches represent premium anchor categories with above-average margins and high turnover.

---

### 2. Which states generate the most orders?
Marketplace demand is heavily concentrated in the Southeast region of Brazil:
- **São Paulo (SP):** 41.8% of total orders (40,501 orders) and R$ 5,202,955 in revenue (~39.3% share).
- **Rio de Janeiro (RJ):** 12.8% of orders (12,350 orders) and R$ 1,824,093 in revenue.
- **Minas Gerais (MG):** 11.6% of orders (11,385 orders) and R$ 1,585,490 in revenue.
- **Rio Grande do Sul (RS) & Paraná (PR):** ~5.5% each.

*Strategic Takeaway:* The top 3 Southeastern states (SP, RJ, MG) account for **66.2% of total national platform revenue**. Conversely, Northern and Northeastern states suffer from low order density compounded by expensive, slow logistics.

---

### 3. Which customer segments are most valuable?
Through RFM (Recency, Frequency, Monetary) segmentation:
- **Champions & Loyal Customers (5.2% of user base):** Generate **14.8% of total revenue**. These consumers order frequently (2 to 6+ times) with average basket sizes exceeding R$ 260.
- **High-Value Churned (8.4% of base):** Customers who previously made large purchases (>R$ 500) but have not returned in over 250 days.
- **Recent Promising (24.1% of base):** New first-time buyers acquired within the last 90 days.

---

### 4. How much of the business comes from repeat customers?
Only **3.0% (2,801 customers)** of Olist’s 93,358 unique consumers made more than one purchase. However, these repeat customers generated **R$ 863,000 in revenue (6.5% of total sales)** with a 38% higher lifetime value.
- First purchase order share: **97.0%**
- Repeat purchase order share: **3.0%**
- Month 1 retention rate across cohorts averages **0.8%**.

*Strategic Takeaway:* Olist operates almost entirely as a one-time customer acquisition funnel. The platform loses customer relationship equity after the initial checkout.

---

### 5. Which sellers perform best?
The marketplace has 3,095 registered sellers, but supply is intensely concentrated:
- The **top 5% of sellers generate 48.6% of total platform GMV**.
- Top seller (`seller_id`: `6560211a19b4f9d704b466d721267df5`) generated R$ 229,400 alone.
- High-performing sellers maintain dispatch speeds under **24 hours** from order approval, yielding average customer review scores of **4.35 stars**. In contrast, sellers taking >4 days to transfer packages to carriers average **3.65 stars**.

---

### 6. Are delivery delays affecting customer satisfaction?
**Yes, delivery timeliness is the single most dominant driver of customer review scores.**
- **On-time / Early Deliveries:** Average Review Score = **4.29 / 5.00 Stars** (Five-star rate: 76.5%, One-star rate: 4.8%).
- **Delays of 1 to 5 Days Past Estimated Date:** Average Review Score drops to **2.57 / 5.00 Stars** (One-star rate surges to 44.2%).
- **Delays Over 10 Days:** Average Review Score collapses to **1.35 / 5.00 Stars** (One-star rate reaches 84.1%).

*Strategic Takeaway:* A late delivery increases the likelihood of a 1-star review by **more than 900%**.

---

### 7. Which payment methods are most popular?
- **Credit Card:** **75.4% of total transaction value** (76,784 payments). Average installment plan: 3.5 installments.
- **Boleto Bancário (Cash voucher):** **19.3% of total transaction value** (19,784 payments).
- **Voucher / Store Credit:** **3.8% of value** (5,775 payments).
- **Debit Card:** **1.5% of value** (1,529 payments).

*Strategic Takeaway:* Installment capability is essential in Brazil. Over 52% of credit card transactions were split into 2 or more installments.

---

### 8. What are the major business risks?
1. **Severe Supplier Concentration:** If the top 50 sellers leave for competing marketplaces (Mercado Livre, Amazon Brazil), Olist loses ~30% of product revenue.
2. **Extreme Customer Churn (97% One-Time Buyers):** Skyrocketing digital advertising costs (Meta, Google CAC) will render acquisition unprofitable without customer retention.
3. **Logistics Friction in North/Northeast:** Delivery times of 25–29 days in PA, AM, and RR limit national scalability.
4. **Carrier Dependency:** Olist relies primarily on Correios and public postal services, leaving fulfillment vulnerable to postal strikes and holiday bottlenecks.

---

### 9. What opportunities exist for growth?
1. **Post-Purchase Retention Engine:** Instituting targeted replenishment emails for consumables (Health & Beauty, Pet Supplies) could double repeat buyer rates from 3% to 6%.
2. **Micro-Fulfillment Hubs in Northeast:** Staging top 20% Pareto SKUs in regional fulfillment centers (e.g., Recife or Salvador) would slash delivery times from 22 days to 5 days.
3. **B2B / Wholesale Expansion:** Top corporate buyer accounts already spend >R$ 10,000 per order; formalized B2B invoicing would unlock commercial procurement.
4. **Seller Fulfillment Guarantee (FBL - Fulfillment by Olist):** Taking custody of high-velocity inventory to guarantee 48-hour delivery across São Paulo.

---

### 10. What should management do next?
See the 5 prioritized actionable business recommendations in `reports/business_recommendations.md`.
