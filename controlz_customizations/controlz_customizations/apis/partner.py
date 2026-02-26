import frappe
from frappe import _
@frappe.whitelist(allow_guest=True)
def authenticate():
    data = frappe.request.get_json()
    retailer_code = data.get("retailer_code")
    serial_no = data.get("product_identification_number")
    short_code = data.get("product_sku_code")
    distributor_code = data.get("Distributor_Code")

    if not retailer_code or not serial_no or not short_code or not distributor_code:
        frappe.throw(_("Missing required parameters"))

    retailer_code_exists = frappe.db.exists("Customer", {"retailer_code": retailer_code})

    if not retailer_code_exists:
        return {"responsecode": "2", "message": "Retailer Mismatch/ Invalid Channel"}

    distributor_code_exists = frappe.db.exists("Customer", {"distributor_code": distributor_code})

    if not distributor_code_exists:
        return {"responsecode": "5", "message": "Incorrect Distributor Code"}

    serial_no = frappe.db.get_value("Serial No", serial_no, ["item_code", "sr_status", "custom_imei1", "custom_imei2"], as_dict=True)

    if not serial_no:
        return {"responsecode": "4", "message": "This is not a OEM Serial Number"}

    product = frappe.db.get_value("Item", serial_no.item_code, ["short_code"], as_dict=True)

    if not product:
        return {"responsecode": "1", "message": "Model Mismatch"}

    response = {}
    response['responsecode'] = str(serial_no.sr_status or 0)

    if product.short_code == short_code:
        if serial_no.custom_imei1:
            response['imei1'] = serial_no.custom_imei1

        if serial_no.custom_imei2:
            response['imei2'] = serial_no.custom_imei2

        response['message'] = 'Success'
    else:
        response['responsecode'] = '1'
        response['message'] = 'Model Mismatch'
    return response
