import frappe
import re
import json
from frappe import _
from datetime import datetime, date
import pytz
import asyncio

from clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment import sync_shipment
from clickpost_erpnext_integration.clickpost_erpnext_integration.utils import download_and_attach_file
from frappe.utils import getdate


@frappe.whitelist()
def get_address_details(address_name):
    """
    Get address details from the Address doctype.
    
    Args:
        address_name (str): The name of the Address document
        
    Returns:
        dict: A dictionary containing address details
        
    Raises:
        Exception: If address is not found or there's an error fetching it
    """
    if not address_name:
        frappe.throw("Address name is required")
    
    try:
        address = frappe.db.get_value(
            "Address",
            address_name,
            [
                "city", 
                "state", 
                "pincode", 
                "country", 
                "address_line1", 
                "address_line2", 
                "county", 
                "custom_clickpost_location_id", 
                "gstin"
            ],
            as_dict=1
        )
        
        if not address:
            frappe.throw("Address not found")
        
        address_details = {
            "city": address.get("city") or "",
            "state": address.get("state") or "",
            "pincode": address.get("pincode") or "",
            "country": get_country_code(address.get("country") or "India"),
            "address": address.get("address_line1") + 
                      (f", {address.get('address_line2')}" if address.get("address_line2") else ""),
            "district": address.get("county") or address.get("city") or "",
            "location_code": address.get("custom_clickpost_location_id") or "",
            "gstin": address.get("gstin") or ""
        }
        
        return address_details
    
    except Exception as e:
        frappe.log_error(f"Error fetching address: {str(e)}", "ClickPost Address Error")
        frappe.throw(f"Error fetching address: {str(e)}")

@frappe.whitelist()
def format_address(address):
    """
    Format an address string by removing HTML tags and standardizing separators.
    
    Args:
        address (str): The address string that may contain HTML tags
        
    Returns:
        str: A clean, formatted address string
    """
    if not address:
        return ""
    
    # Replace <br> tags with commas or spaces
    formatted_address = address
    
    # Replace <br> tags with comma and space
    formatted_address = re.sub(r'<br\s*/?>', ', ', formatted_address)
    
    # Replace &nbsp; with space
    formatted_address = re.sub(r'&nbsp;', ' ', formatted_address)
    
    # Remove any other HTML tags
    formatted_address = re.sub(r'<[^>]*>', '', formatted_address)
    
    # Replace multiple commas with a single comma
    formatted_address = re.sub(r',\s*,', ',', formatted_address)
    
    # Replace multiple spaces with a single space
    formatted_address = re.sub(r'\s+', ' ', formatted_address)
    
    # Remove leading/trailing whitespace
    formatted_address = formatted_address.strip()
    
    # Remove trailing comma if exists
    if formatted_address.endswith(','):
        formatted_address = formatted_address[:-1].strip()
    
    return formatted_address


@frappe.whitelist()
def calculate_total_item_count(frm):
    """
    Calculate the total item count from all linked Sales Invoices.
    
    Args:
        frm (dict): The shipment document
        
    Returns:
        float: Total item count across all linked sales invoices
    """
    if isinstance(frm, str):
        frm = json.loads(frm)
    
    total_item_count = 0
    
    # Check if custom_sales_invoice exists and has items
    custom_sales_invoices = frm.get("custom_sales_invoice", [])
    if not custom_sales_invoices:
        return total_item_count
    
    # Iterate through each linked sales invoice
    for invoice in custom_sales_invoices:
        sales_invoice_name = invoice.get("sales_invoice")
        if not sales_invoice_name:
            continue
        
        # Get the sales invoice document
        try:
            sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_name)
            
            # Sum up quantities from all items in the invoice
            if sales_invoice and sales_invoice.get("items"):
                for item in sales_invoice.items:
                    total_item_count += item.qty
        except Exception as e:
            frappe.log_error(
                f"Error fetching Sales Invoice {sales_invoice_name}: {str(e)}",
                "ClickPost Item Count Error"
            )
    
    return total_item_count


@frappe.whitelist()
def calculate_total_weight(frm):
    """
    Calculate the total weight from all parcels in the shipment.
    
    Args:
        frm (dict): The shipment document
        
    Returns:
        float: Total weight of all parcels in the shipment
    """
    if isinstance(frm, str):
        frm = json.loads(frm)
    
    total_weight = 0
    
    # Get the shipment parcels
    shipment_parcels = frm.get("shipment_parcel", [])
    
    # Iterate through each parcel and calculate weight
    for item in shipment_parcels:
        weight = item.get("weight")
        count = item.get("count")
        
        if weight and count:
            total_weight += (weight * count)
    
    # Default to 0 if no weight is calculated
    return total_weight or 0

@frappe.whitelist()
def recommendation_box(frm):
    """
    Create a list of box dimensions from shipment parcels.
    
    Args:
        frm (dict): The shipment document
        
    Returns:
        list: List of dictionaries containing box dimensions
    """
    if isinstance(frm, str):
        frm = json.loads(frm)
    
    boxes = []
    
    # Get the shipment parcels
    shipment_parcels = frm.get("shipment_parcel", [])
    
    # Map each parcel to a box with dimensions
    for parcel in shipment_parcels:
        box = {
            "height": parcel.get("height") or 10,
            "length": parcel.get("length") or 10,
            "weight": parcel.get("weight") or 10,
            "breadth": parcel.get("width") or 10
        }
        boxes.append(box)
    
    return boxes


@frappe.whitelist()
def prepare_shipment_payload(frm):
    """
    Prepare the shipment payload for ClickPost API.
    
    Args:
        frm (dict): The shipment document
        
    Returns:
        dict: The formatted payload for ClickPost API
    """
    if isinstance(frm, str):
        frm = json.loads(frm)
    try:
        # Format pickup time to YYYY-MM-DDThh:mm:ss
        pickup_date = frm.get("pickup_date")
        pickup_time = frm.get("pickup_from")
        
        if pickup_date:
            if pickup_time:
                pickup_datetime = f"{pickup_date} {pickup_time}"
                formatted_pickup_time = format_datetime_with_timezone(pickup_datetime)
            else:
                formatted_pickup_time = format_datetime_with_timezone(pickup_date, date_only=True)
        else:
            formatted_pickup_time = format_datetime_with_timezone(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Get address details
        pickup_address_details = get_address_details(frm.get("pickup_address_name"))
        delivery_address_details = get_address_details(frm.get("delivery_address_name"))
        
        # Create pickup_info object
        pickup_info = {
            "name": frm.get("custom_pickup_contact_person_name"),
            "phone": frm.get("custom_pickup_contact_phone") or "0000000000",
            "organisation": frm.get("pickup_company") or frm.get("pickup_customer") or frm.get("pickup_supplier"),
            "email": frm.get("pickup_contact_email"),
            "vendor_code": "",
            "time": str(formatted_pickup_time),
            "district": pickup_address_details.get("district"),
            "city": pickup_address_details.get("city"),
            "landmark": "",
            "state": pickup_address_details.get("state"),
            "pincode": pickup_address_details.get("pincode"),
            "country": pickup_address_details.get("country") or "IN",
            "address_type": "",
            "address": format_address(frm.get("pickup_address"))
        }
        
        enterprise_gstin = pickup_address_details.get("gstin")
        
        # Create drop_info object
        delivery_contact_name = frm.get("delivery_contact_name", "")
        drop_info = {
            "name": delivery_contact_name.split("-")[0] if "-" in delivery_contact_name else frm.get("custom_delivery_contact_name"),
            "phone": frm.get("custom_delivery_contact_phone"),
            "email": str(frm.get("delivery_contact_email") or ""),
            "organisation": frm.get("delivery_customer"),
            "vendor_code": "",
            "district": delivery_address_details.get("district"),
            "address_type": "",
            "landmark": "",
            "city": delivery_address_details.get("city"),
            "state": delivery_address_details.get("state"),
            "pincode": delivery_address_details.get("pincode"),
            "country": delivery_address_details.get("country") or "IN",
            "address": format_address(frm.get("delivery_address"))
        }
        
        consignee_gstin = delivery_address_details.get("gstin")
        
        # Fetch purchase order info
        purchase_order_info = get_purchase_order_info(frm)
        
        # Build the complete payload
        return {
            "pickup_info": pickup_info,
            "drop_info": drop_info,
            "shipment_info": {
                "description": frm.get("description_of_content"),
                "reference_number": frm.get("name"),
                "courier_partner": frm.get("custom_carrier_partner_id"),
                "account_code": frm.get("custom_carrier_partner_name"),
                "cod_value": 0 if frm.get("custom_order_type") == "PREPAID" else frm.get("custom_cod_value"),
                "order_type": frm.get("custom_order_type"),
                "order_id": "",
                "delivery_type": frm.get("custom_delivery_type"),
                "weight": calculate_total_weight(frm),
                "invoice_info": get_invoice_info(frm),
                "purchase_order_info": purchase_order_info,
                "box_info": get_box_info(frm),
                "gst_info": {
                    "seller_gstin": "",
                    "enterprise_gstin": pickup_address_details.get("gstin"),
                    "taxable_value": 0,
                    "is_seller_registered_under_gst": "",
                    "place_of_supply": "",
                    "gst_discount": 0,
                    "gst_total_tax": 0,
                    "sgst_tax_rate": 0,
                    "sgst_amount": 0,
                    "igst_tax_rate": 0,
                    "igst_amount": 0,
                    "cgst_tax_rate": 0,
                    "cgst_amount": 0,
                    "consignee_gstin": delivery_address_details.get("gstin"),
                    "sgst_total_tax": 0
                },
                "products_in_shipment": products_in_shipment(frm)
            },
            "appointment_info": {
                "start_time": format_erpnext_datetime(frm.get("custom_start_time")),
                "end_time": format_erpnext_datetime(frm.get("custom_end_time")),
                "id": ""
            },
            "additional_info": {
                "return_info": pickup_info,
            }
        }
    except Exception as e:
        frappe.log_error(
            f"Error Preparing Payload: {str(e)}",
            "ClickPost Payload Error"
        )

# def format_datetime_with_timezone(dt_str, date_only=False):
#     """
#     Format datetime string to ISO format with timezone offset.
    
#     Args:
#         dt_str (str): Datetime string
#         date_only (bool): Whether the input is date only
        
#     Returns:
#         str: Formatted datetime string with timezone
#     """
#     india_tz = pytz.timezone('Asia/Kolkata')
    
#     if date_only:
#         dt = datetime.strptime(dt_str, "%Y-%m-%d")
#     else:
#         dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    
#     # Localize to India timezone
#     dt_with_tz = india_tz.localize(dt)
    
#     # Format with timezone offset
#     return dt_with_tz.strftime("%Y-%m-%dT%H:%M:%S+0530")

# def format_erpnext_datetime(erpnext_datetime):
#     """
#     Format ERPNext datetime to ISO format with timezone offset.
    
#     Args:
#         erpnext_datetime (str): ERPNext datetime string
        
#     Returns:
#         str: Formatted datetime string with timezone or None
#     """
#     if not erpnext_datetime:
#         return None
    
#     india_tz = pytz.timezone('Asia/Kolkata')
    
#     # Parse the ERPNext datetime
#     dt = datetime.strptime(erpnext_datetime, "%Y-%m-%d %H:%M:%S")
    
#     # Localize to India timezone
#     dt_with_tz = india_tz.localize(dt)
    
#     # Format with timezone offset
#     return dt_with_tz.strftime("%Y-%m-%dT%H:%M:%S+0530")



def format_datetime_with_timezone(dt_input, date_only=False):
    """
    Format datetime string or object to ISO format with timezone offset.
    Args:
        dt_input (str or datetime): Datetime string or object
        date_only (bool): Whether the input is date only
    Returns:
        str: Formatted datetime string with timezone
    """
    india_tz = pytz.timezone('Asia/Kolkata')
    if isinstance(dt_input, datetime):
        dt = dt_input
    elif date_only:
        dt = datetime.strptime(dt_input, "%Y-%m-%d")
    else:
        dt = datetime.strptime(dt_input, "%Y-%m-%d %H:%M:%S")
    dt_with_tz = india_tz.localize(dt)
    return dt_with_tz.strftime("%Y-%m-%dT%H:%M:%S+0530")

def format_erpnext_datetime(erpnext_datetime):
    """
    Format ERPNext datetime to ISO format with timezone offset.
    Args:
        erpnext_datetime (str or datetime): ERPNext datetime string or object
    Returns:
        str: Formatted datetime string with timezone or None
    """
    if not erpnext_datetime:
        return None
    india_tz = pytz.timezone('Asia/Kolkata')
    if isinstance(erpnext_datetime, datetime):
        dt = erpnext_datetime
    else:
        dt = datetime.strptime(erpnext_datetime, "%Y-%m-%d %H:%M:%S")
    dt_with_tz = india_tz.localize(dt)
    return dt_with_tz.strftime("%Y-%m-%dT%H:%M:%S+0530")

@frappe.whitelist()
def products_in_shipment(frm):
    """
    Get products information from linked sales invoices.
    
    Args:
        frm (dict): The shipment document
        
    Returns:
        list: List of products in the shipment
    """
    if isinstance(frm, str):
        frm = json.loads(frm)
    try:
        products = {}
        
        # Check if there are any attached sales invoices
        custom_sales_invoices = frm.get("custom_sales_invoice", [])
        if not custom_sales_invoices:
            return []
        
        # Iterate through each attached sales invoice
        for invoice in custom_sales_invoices:
            sales_invoice_name = invoice.get("sales_invoice")
            if not sales_invoice_name:
                continue
            
            try:
                # Fetch items from the sales invoice
                sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_name)
                
                if not sales_invoice or not sales_invoice.get("items"):
                    continue
                
                # Add each item from the sales invoice to the products dictionary
                for item in sales_invoice.items:
                    item_code = item.item_code
                    hsn_code = get_hsn_code(item_code)
                    itemAttr = frappe.get_doc("Item", item_code)
                    
                    if item_code in products:
                        # If the product already exists, update the quantity
                        products[item_code]["sku_count"] += item.qty
                    else:
                        # Otherwise, create a new entry for the product
                        products[item_code] = {
                            "sku": item_code,
                            "sku_count": item.qty,
                            "description": item.description or "",
                            "product_category": item.item_group or "",
                            "manufacturer_country": itemAttr.country_of_origin or "",
                            "manufacturer_country_code": get_country_code(itemAttr.country_of_origin or "India") or "",
                            "hsn_code": hsn_code,
                            "price": item.rate or 0
                        }
            
            except Exception as e:
                frappe.log_error(
                    f"Error fetching Sales Invoice {sales_invoice_name}: {str(e)}",
                    "ClickPost Products Error"
                )
        
        # Convert the products dictionary to a list
        return list(products.values())
    except Exception as e:
        frappe.log_error(
            f"Error Preparing Payload: {str(e)}",
            "ClickPost Payload Error"
        )

@frappe.whitelist()
def get_hsn_code(item):
    """
    Get HSN code for an item.
    
    Args:
        item (str): Item code
        
    Returns:
        str: HSN code
    """
    try:
        data = frappe.db.get_value("Item", item, "gst_hsn_code", as_dict=1)
        return data.get("gst_hsn_code") or ""
    except Exception as e:
        frappe.log_error(f"Error fetching HSN code for {item}: {str(e)}", "ClickPost HSN Error")
        return ""

@frappe.whitelist()
def get_clickpost_config():
    """
    Get ClickPost configuration settings.
    
    Returns:
        dict: ClickPost configuration
    """
    try:
        config = frappe.db.get_value(
            "ClickPost Configuration", 
            None, 
            ["use_location_code_if_available"],
            as_dict=1
        )
        return config or {"use_location_code_if_available": 0}
    except Exception as e:
        frappe.log_error(f"Error fetching ClickPost settings: {str(e)}", "ClickPost Config Error")
        return {"use_location_code_if_available": 0}

@frappe.whitelist()
def get_purchase_order_info(frm):
    """
    Get purchase order information from linked sales invoices.
    
    Args:
        frm (dict): The shipment document
        
    Returns:
        list: List of purchase order information
    """
    if isinstance(frm, str):
        frm = json.loads(frm)
    try:
        custom_sales_invoices = frm.get("custom_sales_invoice", [])
        if not custom_sales_invoices:
            return []
        
        purchase_order_info = []
        
        for invoice in custom_sales_invoices:
            sales_invoice_name = invoice.get("sales_invoice")
            if not sales_invoice_name:
                continue
            
            try:
                invoice_data = frappe.db.get_value(
                    "Sales Invoice",
                    sales_invoice_name,
                    ["po_no", "po_date"],
                    as_dict=1
                )
                po_date = invoice_data.get("po_date")
                if isinstance(po_date, datetime):
                    po_date = po_date.date()
                if isinstance(po_date, date):
                    po_date = po_date.strftime("%Y-%m-%d")
                purchase_order_info.append({
                    "number": invoice_data.get("po_no") or "",
                    # "expiry_date": invoice_data.get("po_date")
                })
            
            except Exception as e:
                frappe.log_error(
                    f"Error fetching purchase order info for {sales_invoice_name}: {str(e)}",
                    "ClickPost PO Error"
                )
                purchase_order_info.append({
                    "number": "",
                    "expiry_date": None
                })
        
        return purchase_order_info
    except Exception as e:
        frappe.log_error(
            f"Error Preparing Payload1: {str(e)}",
            "ClickPost Payload Error"
        )

@frappe.whitelist()
def get_invoice_info(frm):
    """
    Get invoice information from linked sales invoices.
    
    Args:
        frm (dict): The shipment document
        
    Returns:
        list: List of invoice information
    """
    if isinstance(frm, str):
        frm = json.loads(frm)
    try:
        custom_sales_invoices = frm.get("custom_sales_invoice", [])
        if not custom_sales_invoices:
            return []
        
        invoice_info = []
        
        for invoice in custom_sales_invoices:
            raw = invoice.get("e_waybill_expiry_date")
            
            # # Convert to correct format or set to None
            e_waybill_expiry_date = None
            if raw:
                try:
                    # Case A: It’s already a Python datetime.datetime
                    if isinstance(raw, datetime):
                        dt = raw.date()

                    # Case B: It’s already a Python date
                    elif isinstance(raw, date):
                        dt = raw

                    # Case C: It’s a string (e.g. "2025-06-03")
                    elif isinstance(raw, str):
                        # If your string is guaranteed to be "YYYY-mm-dd"
                        dt = datetime.strptime(raw, "%Y-%m-%d").date()
                        # If you’re not sure of the format, you could also do:
                        # dt = getdate(raw)

                    # Case D: Some other truthy value (e.g. a Timestamp, etc.)
                    else:
                        # Let Frappe’s getdate() try to coerce it to a date
                        dt = getdate(raw)

                    # Finally, convert the date object to a string. If you really need a string:
                    e_waybill_expiry_date = dt.strftime("%Y-%m-%d")

                except Exception:
                    # Log whatever went wrong, and leave e_waybill_expiry_date = None
                    frappe.log_error(
                        title=f"Error parsing e_waybill_expiry_date: {raw!r}",
                        message=frappe.get_traceback()
                    )
                    e_waybill_expiry_date = None
            else:
                # raw was falsy (None/empty), so keep it as None
                e_waybill_expiry_date = None

            invoice_info.append({
                "number": invoice.get("sales_invoice"),
                "value": invoice.get("grand_total"),
                "date": str(invoice.get("posting_date")),
                "base64": "",
                "ewaybill_serial_number": invoice.get("e_waybill_number") or None,
                "ewaybill_expiry_date": e_waybill_expiry_date or None,
                "description": ""
            })
        
        return invoice_info
    except Exception as e:
        frappe.log_error(f"Error getting invoice info: {str(e)}", "Invoice Error")

@frappe.whitelist()
def get_box_info(frm):
    """
    Get box information from shipment parcels.
    
    Args:
        frm (dict): The shipment document
        
    Returns:
        list: List of box information
    """
    if isinstance(frm, str):
        frm = json.loads(frm)
    try:
        shipment_parcels = frm.get("shipment_parcel", [])
        item_box_mapping = frm.get("custom_item_box_mapping", [])
        
        if not shipment_parcels:
            return []
        
        box_info = []
        
        for idx, parcel in enumerate(shipment_parcels):
            box_identifier = f"{parcel.get('custom_parcel')}-{(idx + 1)}"
            
            product_info = get_product_info(parcel, box_identifier, item_box_mapping)
            invoice_info = get_invoice_info_for_box(box_identifier, item_box_mapping)
            purchase_order_info = get_purchase_order_info_for_box(box_identifier, item_box_mapping)
        
            box_info.append({
                "count": parcel.get("count") or 1,
                "reference_number_prefix": "",
                "box_master_code": "",#parcel.get("custom_parcel") or "",
                "height": parcel.get("height") or 10,
                "length": parcel.get("length") or 10,
                "weight": parcel.get("weight") or 10,
                "breadth": parcel.get("width") or 10,
                "description": "",
                "purchase_order_info": purchase_order_info,
                "invoice_info": invoice_info,
                "product_info": product_info
            })
        
        return box_info
    except Exception as e:
        frappe.log_error(
            f"Error Preparing box info: {str(e)}",
            "ClickPost Box Info Error"
        )

def get_purchase_order_info_for_box(box_identifier, item_box_mapping):
    """
    Return unique purchase order info associated with a box from item_box_mapping.
    Args:
        box_identifier (str): The box identifier string
        item_box_mapping (list): List of item-to-box mappings
    Returns:
        list: List of dicts with 'number' key for purchase order numbers
    """
    po_numbers = []
    seen = set()
    for row in item_box_mapping:
        if row.get("box") == box_identifier:
            invoice_no = row.get("sales_invoice")
            if invoice_no and invoice_no not in seen:
                # Fetch PO number from Sales Invoice
                try:
                    invoice_data = frappe.db.get_value(
                        "Sales Invoice",
                        invoice_no,
                        ["po_no", "po_date"],
                        as_dict=1
                    )
                    po_number = invoice_data.get("po_no") if invoice_data else ""
                    po_date = invoice_data.get("po_date") if invoice_data else None
                    if isinstance(po_date, datetime):
                        po_date = po_date.date()
                    if isinstance(po_date, date):
                        po_date = po_date.strftime("%Y-%m-%d")
                except Exception as e:
                    frappe.log_error(
                        f"Error fetching PO for invoice {invoice_no}: {str(e)}",
                        "ClickPost Box PO Error"
                    )
                    po_number = ""
                    po_date = None
                po_numbers.append({
                    "number": po_number or "",
                    # "expiry_date": po_date
                })
                seen.add(invoice_no)
    return po_numbers

def get_invoice_info_for_box(box_identifier, item_box_mapping):
    """
    Return unique sales invoice info associated with a box from item_box_mapping.
    Args:
        box_identifier (str): The box identifier string
        item_box_mapping (list): List of item-to-box mappings
    Returns:
        list: List of dicts with 'number' key for sales invoice numbers
    """
    invoices = []
    seen = set()
    for row in item_box_mapping:
        if row.get("box") == box_identifier:
            invoice_no = row.get("sales_invoice")
            if invoice_no and invoice_no not in seen:
                invoices.append({"number": invoice_no})
                seen.add(invoice_no)
    return invoices

def get_product_info(parcel, box_identifier, item_box_mapping):
    """
    Generate product information for a specific parcel.
    
    Args:
        parcel (dict): The parcel data
        box_identifier (str): The box identifier string
        item_box_mapping (list): List of item-to-box mappings
        
    Returns:
        list: List of product information dictionaries
    """
    matching_rows = [
        row for row in item_box_mapping
        if row.get("box") == box_identifier
    ]
    
    # Build product_info from matching rows
    product_info = []
    for row in matching_rows:
        item_attr = frappe.get_doc("Item", row.get("sku"))
        country_of_origin = item_attr.country_of_origin or "India"
        
        product_info.append({
            "sku": row.get("sku") or "",
            "sku_count": row.get("sku_count") or 1,
            "description": row.get("description") or "",
            "product_category": row.get("product_category") or "",
            "manufacturer_country": country_of_origin,
            "manufacturer_country_code": get_country_code(country_of_origin) or "",
            "hsn_code": row.get("hsn_code") or "",
            "price": row.get("price") or None
        })
    
    # Default product info if none found
    if not product_info:
        product_info = [{
            "sku": "",
            "sku_count": 0,
            "description": "",
            "product_category": "",
            "manufacturer_country": "",
            "manufacturer_country_code": "",
            "hsn_code": "",
            "price": None
        }]
    
    return product_info

@frappe.whitelist()
def sync_shipment_api(frm):
    """
    Sync shipment details with ClickPost and update the Shipment document.
    """
    if isinstance(frm, str):
        frm = json.loads(frm)
    
    try:
        sync_response = sync_shipment(
            reference_number=frm.get("name"),
            courier_partner=frm.get("custom_carrier_partner_id"),
            account_code=frm.get("custom_carrier_partner_name")
        )
        
        meta = sync_response.get("response", {}).get("meta", {})
        shipment = sync_response.get("response", {}).get("result", {})
        
        if not meta or not meta.get("success"):
            return {
                "success": False,
                "message": meta.get("message") if meta else "Failed to sync shipment"
            }
        
        frappe.db.set_value(
            "Shipment",
            frm.get("name"),
            "awb_number",
            shipment.get("waybill")
        )
        
        # Handle file attachments (label + box stickers)
        attachment_results = []
        
        if shipment.get("label"):
            try:
                result = attach_file(
                    shipment.get("label"),
                    frm.get("name"),
                    f"label_{frm.get('name')}.pdf",
                    "shipping label"
                )
                attachment_results.append(result)
            except Exception as e:
                attachment_results.append(str(e))
        
        box_stickers = shipment.get("box_stickers", {})
        if box_stickers and isinstance(box_stickers, dict):
            for format_type, url in box_stickers.items():
                if url:
                    try:
                        result = attach_file(
                            url,
                            frm.get("name"),
                            f"{format_type}_box_sticker_{frm.get('name')}.pdf",
                            f"box sticker {format_type}"
                        )
                        attachment_results.append(result)
                    except Exception as e:
                        attachment_results.append(str(e))
        
        # Show messages for attachments
        for result in attachment_results:
            frappe.msgprint(
                msg=result,
                indicator="green" if "successfully" in result else "red",
                alert=True
            )
        
        return {
            "success": True,
            'status': meta.get("status"),
            "message": meta.get("message") or "Order Placed Successfully",
            "waybill": frm.get("name") or "",
        }
    
    except Exception as e:
        frappe.log_error(f"Error syncing shipment: {str(e)}", "ClickPost Sync Error")
        return {
            "success": False,
            "message": str(e) or "Unexpected sync error"
        }


def attach_file(url, docname, filename, filetype):
    """
    Download and attach a file to a document.
    
    Args:
        url (str): URL of the file to download
        docname (str): Name of the document to attach to
        filename (str): Name to save the file as
        filetype (str): Type of file for display purposes
        
    Returns:
        str: Success message
        
    Raises:
        Exception: If file attachment fails
    """
    # frappe.publish_realtime("freeze", {"message": _(f"Attaching {filetype}...")})
    
    try:
        result = download_and_attach_file(
            url=url,
            doctype="Shipment",
            docname=docname,
            filename=filename
        )
        
        if result and result.get("success"):
            return f"{filetype} attached successfully"
        else:
            raise Exception(f"Failed to attach {filetype}")
    
    except Exception as e:
        frappe.log_error(f"Error attaching {filetype}: {str(e)}", "ClickPost File Attachment Error")
        raise Exception(f"Failed to attach {filetype}: {str(e)}")

def get_country_code(country_name):
    """
    Get the country code for a given country name.
    If country name is not provided or not found, defaults to 'IN' (India).
    
    Args:
        country_name (str): The name of the country
        
    Returns:
        str: The country code
    """
    if not country_name:
        # Default to India if no country name provided
        return "IN"
    
    try:
        country = frappe.db.get_value("Country", country_name, "code")
        if country:
            return country
        else:
            # If country code not found, default to India
            frappe.msgprint(f"Country code not found for {country_name}, defaulting to IN")
            return "IN"
    except Exception as e:
        frappe.log_error(f"Error fetching country code: {e}")
        return "IN"  # Default to India in case of error


#create function for logging
@frappe.whitelist()
def shipment_auto_log(response):
    """Create log entry for connection test"""
    try:
        log = frappe.get_doc({
            "doctype": "Auto Shipment Creation Logs",
            # "status": str(status),
            "shipment_reference": response.get("shipment_reference") or "",
            "awb_number": response.get("awb_number") or "",
            "recommendation_status": response.get("recommendation_status") or "False",
            "recommendation_message": response.get("recommendation_message") or "",
            "order_creation_status": response.get("order_creation_status") or "Error",
            "account_name": response.get("account_name") or "",
            "allocated_carrier": response.get("allocated_carrier") or "",
            "shipment_creation_time": response.get("shipment_creation_time") or "",
            "recommandation_reference": response.get("recommendation_reference") or "",
        })
        for ref in response.get("recommandation_reference", []):
            log.append("recommandation_reference", {
                "carrier_name": ref.get("carrier_name"),
                "status": ref.get("status"),
                "message": ref.get("message"),
            })
        # if self.enable_api_log:
        log.insert(ignore_permissions=True)
        return log.name
        
    except Exception as e:
        frappe.log_error(message=str(e), title="Shipment auto creation Log")
        return None