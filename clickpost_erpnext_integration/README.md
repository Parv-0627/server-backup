# ClickPost B2B Shipping & Logistics Intelligence for ERPNext

ClickPost provides a single source of truth for B2B logistics. This ERPNext integration adds a centralized intelligence layer that brings automation, visibility, and control to every stage of your B2B shipping journey. From shipment creation and carrier allocation to POD capture and invoice reconciliation, manage it all within ERPNext, seamlessly.

---

## Features

* **Shipment Creation**
  Generate shipments directly from Sales Invoices or Delivery Notes.

* **AWB Registration**
  Register your AWB to track shipments in real-time.

* **Carrier Allocation & Rate Shopping**
  Automatically select the best carrier based on cost, delivery speed, and service level agreements.

* **Multi-Carrier Support**
  Integrate with all major carriers (e.g., FedEx, DHL, Blue Dart) through a unified interface.

* **Real-Time Tracking**
  Track shipments end-to-end and receive status updates.

* **Proof of Delivery (POD) Capture**
  Collect and store POD documents or images against each shipment.

---

## Requirements

* **ERPNext** v14,v15
* **Frappe Framework** v14,v15
* **ClickPost account with API Key and Secret**

---

## Installation

1. **Download the App**

   ```
   bench get-app https://github.com/clickpost/clickpost_erpnext_integration
   ```

2. **Install the App on Your Site**

   ```bash
   bench --site your-site install-app clickpost_erpnext_integration
   ```

---

## Configuration

1. **Add API Credentials**
   Enter your ClickPost API Key, Secret, and URL.

2. **Fetch Carriers**
   Fetch all available carriers and their services from ClickPost.

5. **Set Webhook in Clickpost**
    Set up a webhook in your ClickPost account to receive real-time updates on shipment status changes.

## Ideal For

Logistics leaders and teams in **Retail**, **eCommerce**, and **Manufacturing** using ERPNext who need to:

* Scale B2B shipping operations while maintaining end-to-end visibility
* Optimize shipping costs through smart carrier allocation
* Automate manual shipping tasks and reduce errors

---

## Integration Developed by [Akhilaminc](https://akhilaminc.com/)
