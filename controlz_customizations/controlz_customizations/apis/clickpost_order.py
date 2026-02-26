import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.utils import now
import requests

@frappe.whitelist()
def make_clickpost_doc_from_sales_order_to_customer(source_name,target_doc=None):
    def set_missing_values(source, target):
        so = frappe.get_doc("Sales Order", source_name)
        target.sales_order = so.name
        target.pickup_type = "To Customer"
        
        address = frappe.get_doc("Address", so.shipping_address_name)
        customer = frappe.get_doc("Customer", so.customer)
        address_att = [address.address_line1, address.address_line2, address.city, address.state, address.pincode,]
        target.pickup_address = " ".join([data  for data in address_att if data])
        target.pickup_state = address.state
        target.pickup_city = address.city
        target.pickup_pincode = address.pincode
        target.pickup_email = customer.cu_email
        target.pickup_phone = customer.cu_mobile_number
        target.pickup_name = so.customer_name
        target.pickup_time= now()
        try:
            target.pickup_district= get_district_from_pincode_and_address(so.customer_address)
        except:
            pass
        target.invoice_number=so.name
        target.reference_number=so.name
        target.order_type=so.custom_order_payment_type
        if so.items:
            first_item = so.items[0]
            target.append("clickpost_shipment_item", {
                "sku": first_item.item_code,
                "quantity": first_item.qty,
                "description": first_item.item_code,
                "price": first_item.price_list_rate,
            })

    doclist = get_mapped_doc("Sales Order", source_name,
    {
        "Sales Order": {
            "doctype": "Clickpost Order",
            "field_map": {
            }
        },
        

    }, target_doc,set_missing_values)

    return doclist

def get_district_from_pincode_and_address(customer_address):
    address=frappe.get_doc("Address",customer_address)
    pincode=address.pincode
    response = requests.get(f"https://api.postalpincode.in/pincode/{pincode}")
    data = response.json()
    if data[0]['Status'] == 'Success':
        return data[0]['PostOffice'][0]['District']
    return None
