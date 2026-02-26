import frappe

@frappe.whitelist(methods="POST")
def endpoint(sales_order, status):
    if status not in ["Pending", "Approved", "Cancelled"]:
        frappe.local.response.http_status_code = 400
        return "Invalid Status"
    try:
        so = frappe.get_doc("Sales Order",sales_order)
        so.so_status = status
        so.save(ignore_permissions=True)
        return "Updated"
    except frappe.DoesNotExistError:
        frappe.clear_messages()
        frappe.local.response.http_status_code = 404
        return "Invalid Sales Order Number"