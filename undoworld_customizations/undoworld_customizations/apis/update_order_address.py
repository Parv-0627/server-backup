import frappe
from frappe.contacts.doctype.address.address import render_address

@frappe.whitelist(methods="POST")
def endpoint(sales_order, address):
    try:
        so = frappe.get_doc("Sales Order",sales_order)
        address_doc = create_addres(address, so.customer)
        frappe.db.set_value("Sales Order", sales_order, "customer_address", address_doc.name)
        frappe.db.set_value("Sales Order", sales_order, "address_display", render_address(address_doc, False))
        frappe.db.set_value("Sales Order", sales_order, "shipping_address_name", address_doc.name)
        frappe.db.set_value("Sales Order", sales_order, "shipping_address", render_address(address_doc, False))
        return "Updated"
    except frappe.DoesNotExistError:
        frappe.clear_messages()
        frappe.local.response.http_status_code = 404
        return "Invalid Sales Order Number"


def create_addres(address, customer):
    address_doc = frappe.new_doc("Address")
    address_doc.address_type= "Shipping"
    address_doc.address_title = customer
    address_doc.address_line1 = address.get("address_line1")
    address_doc.address_line2 = address.get("address_line2")
    address_doc.city = address.get("city")
    address_doc.state = address.get("state")
    address_doc.country = address.get("country")
    address_doc.pincode = address.get("pincode")
    
    address_doc.append("links",{
        "link_doctype": "Customer",
        "link_name": customer,
    })
    address_doc.insert(ignore_permissions=True)
    return address_doc