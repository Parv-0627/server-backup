import frappe
import requests
from frappe.utils import flt
import json
import random
import string
from frappe.model.naming import make_autoname

CODE_LENGTH = 15
MAX_RETRIES = 20  # safety limit

def sales_order_on_submit_cancel(doc, method):
    for row in doc.items:
        update_stock(row.item_code, row.warehouse)

def delivery_note_on_submit_cancel(doc,method):
    if method == "on_submit":
        update_retailer_code_distributor_code_sr_status_on_serial_no(doc, method)

    for row in doc.items:
        update_stock(row.item_code, row.warehouse)

def purchase_receipt_on_submit_cancel(doc, method):
    if doc.rejected_serial_no and method == "on_submit":
        rejected_serial_nos = set(
            s.strip()
            for s in doc.rejected_serial_no.split("\n")
            if s.strip()
        )

        for serial_no in rejected_serial_nos:
            serial_no_doc = frappe.get_doc("Serial No", serial_no)
            if serial_no_doc.name:
                serial_no_doc.delete()

    for row in doc.items:
        update_stock(row.item_code, row.warehouse)

def update_stock(item_code, warehouse):    
    stock_warehouse = frappe.db.get_single_value("Controlz Setup", "warehouse")
    if warehouse != stock_warehouse:
        return
    webhook_url = frappe.db.get_single_value("Controlz Setup", "stock_update_webhook")
    api_key = frappe.db.get_single_value("Controlz Setup", "api_key")
    if webhook_url:
        projected_qty = frappe.db.get_value("Bin", {
            "item_code":item_code,
            "warehouse": warehouse
        }, ["actual_qty", "reserved_qty"])
        if projected_qty:
            data = {
                "itemCode": item_code,
                "inventory": flt(projected_qty[0])- flt(projected_qty[1])
            }
            headers = {
                "x-api-key":api_key
            }
            frappe.enqueue(
                requests.post,
                url=webhook_url,
                json=data,
                headers=headers,
                queue="long",
                enqueue_after_commit=True,
            )
            # response = requests.post(url=webhook_url, json=data, headers=headers)

def update_retailer_code_distributor_code_sr_status_on_serial_no(doc, method):
    customer = frappe.get_doc("Customer", doc.customer)

    for item in doc.items:
        if item.use_serial_batch_fields and item.serial_no:
            serials = item.serial_no or ""
            serial_list = [s.strip() for s in serials.split("\n") if s.strip()]

            for serial_no in serial_list:
                serial = frappe.get_doc("Serial No", serial_no)
                if serial:
                    frappe.db.set_value("Serial No", serial_no, "retailer_code", customer.retailer_code, update_modified=False)
                    frappe.db.set_value("Serial No", serial_no, "distributor_code", customer.distributor_code, update_modified=False)
                    frappe.db.set_value("Serial No", serial_no, "sr_status", True, update_modified=False)

        elif item.serial_and_batch_bundle:
            serial_and_batch_bundle = frappe.get_doc("Serial and Batch Bundle", item.serial_and_batch_bundle)
            if serial_and_batch_bundle.entries:
                for row in serial_and_batch_bundle.entries:
                    serial_no = frappe.get_doc("Serial No", row.serial_no)

                    if serial_no:
                        frappe.db.set_value("Serial No", row.serial_no, "retailer_code", customer.retailer_code, update_modified=False)
                        frappe.db.set_value("Serial No", row.serial_no, "distributor_code", customer.distributor_code, update_modified=False)
                        frappe.db.set_value("Serial No", row.serial_no, "sr_status", True, update_modified=False)

def validate(doc, method):
    if doc.customer_group == 'Dealer':
        if not doc.distributor_code:
            for attempt in range(MAX_RETRIES):
                code = generate_code()
                if not frappe.db.exists("Customer", {"distributor_code": code}):
                    doc.distributor_code = code
            
        if not doc.retailer_code:
            for attempt in range(MAX_RETRIES):
                code = generate_code()
                if not frappe.db.exists("Customer", {"retailer_code": code}):
                    doc.retailer_code = code

def generate_code():
    """Generate a random 15-character alphanumeric code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=CODE_LENGTH))

@frappe.whitelist()
def create_serial_numbers(pr_name):
    pr = frappe.get_doc("Purchase Receipt", pr_name)

    for item in pr.items:
        if item.serial_no:
            continue

        item_details = frappe.get_cached_value(
            "Item", item.item_code, ["has_serial_no", "serial_no_series"], as_dict=1
        )

        if not item_details.has_serial_no:
            continue

        serial_series = item_details.serial_no_series

        if not serial_series:
            frappe.throw(
                f"Serial No Series not defined for Item {item.item_code}"
            )

        serial_nos = []
        received_qty = int(item.received_qty)

        for _ in range(received_qty):
            serial_no = make_autoname(serial_series)
            serial_doc = frappe.get_doc({
                "doctype": "Serial No",
                "serial_no": serial_no,
                "item_code": item.item_code,
                "company": pr.company
            })
    
            serial_doc.insert(ignore_permissions=True)
            serial_nos.append(serial_no)

        item.serial_no = "\n".join(serial_nos)

    pr.save(ignore_permissions=True)
    frappe.db.commit()