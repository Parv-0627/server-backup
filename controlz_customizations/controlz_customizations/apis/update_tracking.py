import frappe

@frappe.whitelist()
def endpoint(**kwargs):
    frappe.log_error("API Webhook", kwargs)
    frappe.db.commit()