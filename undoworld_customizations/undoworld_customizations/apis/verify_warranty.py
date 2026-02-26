import frappe
from frappe.utils import getdate,nowdate

@frappe.whitelist()
def endpoint(serial_number):
    try:
        #test
        srn = get_srn(serial_number)
        if srn:
            serial_number = srn
        serial_number_doc = frappe.get_doc("Serial No", serial_number)
        frappe.local.response["status"] = set_maintenance_status(serial_number_doc)
        frappe.local.response["warranty_expiry_date"] = serial_number_doc.warranty_expiry_date
        frappe.local.response["product_code"] = serial_number_doc.item_code
        frappe.local.response["product_name"] = serial_number_doc.item_name
        img_url = frappe.db.get_value("Item", serial_number_doc.item_code, "image")
        frappe.local.response["product_image"] = frappe.utils.get_url(img_url) if img_url else ""
        parent = get_dn(serial_number)
        frappe.local.response["customer_name"] = ""
        frappe.local.response["email"] = ""
        frappe.local.response["mobile_number"] = ""
        frappe.local.response["history"] = get_history(serial_number)
        if parent:
            dn = frappe.db.get_value("Delivery Note", parent, "name")
            dn_doc = frappe.get_doc("Delivery Note", dn)
            customer = dn_doc.customer
            delivery_date = dn_doc.posting_date
            frappe.local.response["order_id"] = ""
            frappe.local.response["order_date"] = ""
            frappe.local.response["delivery_id"] = dn_doc.name
            for row in dn_doc.items:
                if row.against_sales_order:
                    frappe.local.response["order_id"] = row.against_sales_order
                    frappe.local.response["order_date"] = frappe.db.get_value("Sales Order", row.against_sales_order, "transaction_date")
            customer_doc = frappe.get_doc("Customer", customer)
            frappe.local.response["customer_name"] = customer_doc.customer_name
            frappe.local.response["mobile_number"] = customer_doc.cu_mobile_number
            frappe.local.response["email"] = customer_doc.cu_email
            frappe.local.response["delivery_date"] = delivery_date
        frappe.local.response["other_items"] = get_other_items(serial_number_doc)

    except frappe.DoesNotExistError:
        frappe.log_error()
        frappe.clear_messages()
        frappe.local.response["data"] = ""
        frappe.local.response.http_status_code = 404
        return "Invalid Serial Number"
def get_srn(imei):
    args = {
        "custom_imei1": "%s" % imei,
        "custom_imei2": "%s" % imei,
    }

    parent = frappe.db.sql(
        """
        select srn.name
        from
            `tabSerial No` as srn
        where
            srn.custom_imei1 = %(custom_imei1)s
            or 
            srn.custom_imei2 = %(custom_imei2)s
        order by srn.creation DESC
        """,
        args,
    )
    print("Helllooo")
    try:
        return parent[0][0]
    except:
        return None
def set_maintenance_status(serial_number_doc):

    if serial_number_doc.warranty_expiry_date and getdate(serial_number_doc.warranty_expiry_date) < getdate(nowdate()):
        return "Out of Warranty"

    if serial_number_doc.warranty_expiry_date and getdate(serial_number_doc.warranty_expiry_date) >= getdate(nowdate()):
        return "Under Warranty"


def get_history(sr):
    dn = get_dn(sr)
    if not dn:
        return
    customer = frappe.db.get_value("Delivery Note", dn, "customer")
    if not customer:
        return
    tickets = frappe.get_all("Support Ticket", {"customer":customer }, ["name as support_ticket","CAST( creation AS DATE) as created","status" ])
    return tickets

def get_dn(srn):
    args = {
        "serial_no": "%%%s%%" % srn,
    }

    parent = frappe.db.sql(
        """select dni.parent
        from
            `tabDelivery Note Item` dni,
            `tabDelivery Note` as dn
        where
            dn.name = dni.parent and
            dni.docstatus <> "2" and 
            dni.serial_no like %(serial_no)s
        order by dn.posting_date DESC
        """,
        args,
    )
    try:
        return parent[0][0]
    except: 
        return None

def get_other_items(serial_number_doc):
    final_data = []
    parent = get_dn(serial_number_doc.name)
    if not parent:
        return ""
    customer = frappe.db.get_value("Delivery Note", parent, "customer")
    if customer:
        dns = frappe.get_all("Delivery Note", {"customer": customer})
        for dn in dns:
            dn_doc = frappe.get_doc("Delivery Note", dn)
            for item in dn_doc.items:
                order_id = ""
                order_date = ""

                if item.against_sales_order:
                    order_id = item.against_sales_order
                    order_date = frappe.db.get_value("Sales Order", item.against_sales_order, "transaction_date")
                if item.serial_no:
                    for sn in item.serial_no.split("\n"):
                        try:
                            serial_number_doc = frappe.get_doc("Serial No", sn)
                            img_url = frappe.db.get_value("Item", serial_number_doc.item_code, "image")
                            final_data.append({
                                "sn": sn,
                                "warranty_expiry_date": serial_number_doc.warranty_expiry_date,
                                "product_name": serial_number_doc.item_name,
                                "product_code": serial_number_doc.item_code,
                                "product_image" : frappe.utils.get_url(img_url) if img_url else "",
                                "delivery_date": dn_doc.posting_date,
                                "order_id": order_id,
                                "order_date": order_date
                            })
                        except:
                            pass
    return final_data