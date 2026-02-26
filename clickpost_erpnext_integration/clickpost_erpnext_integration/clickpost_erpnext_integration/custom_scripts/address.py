import frappe
from clickpost_erpnext_integration.clickpost_erpnext_integration.apis.location import delete_clickpost_location

def before_delete_address(doc, method):
    if doc.custom_clickpost_location_id:
        response = delete_clickpost_location(doc.name)
        if response.get("status") != "success":
            frappe.throw("Failed to delete ClickPost location. Address deletion aborted.")
