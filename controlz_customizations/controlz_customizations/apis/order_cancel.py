import frappe


@frappe.whitelist()
def endpoint(order_number):
    so = frappe.get_doc("Sales Order",order_number)
    if so.docstatus == 2:
        return "Already Canceled"
    so.flags.ignore_permissions = 1
    so.cancel()
    frappe.db.commit()

    return "Sales Order Canceled."