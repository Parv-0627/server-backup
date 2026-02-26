import requests, frappe
from frappe.utils import flt
import frappe

@frappe.whitelist()
def update_inventory():
    warehouse = frappe.db.get_single_value("Controlz Setup", "warehouse")
    bins = frappe.get_all("Bin",{"warehouse":warehouse}, ["name","item_code", "actual_qty", "reserved_qty"])
    print(len(bins))
    
    webhook_url = frappe.db.get_single_value("Controlz Setup", "stock_update_webhook")
    api_key = frappe.db.get_single_value("Controlz Setup", "api_key")
    
    headers = {
        "x-api-key":api_key
    }
    for bin in bins:
        data = {
            "itemCode": bin['item_code'],
            "inventory": flt(bin['actual_qty']) - flt(bin['reserved_qty'])
        }
        frappe.enqueue(
            requests.post,
            url=webhook_url,
            json=data,
            headers=headers,
            queue="long",
            enqueue_after_commit=True,
        )
        print("Stock Update for ",bin['item_code'])
    
    