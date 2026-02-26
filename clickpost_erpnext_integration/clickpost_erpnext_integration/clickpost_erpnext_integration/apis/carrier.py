import frappe
from frappe import _
from .base import ClickpostBase
import json

class ClickpostCarrier(ClickpostBase):
    BASE_PATH = "api/v1/enterprise-courier-account-details/"

    def get_carrier(self):
       
        params = {
            "key": self.api_key,
        }
        return self.get("", params=params)
    

    
@frappe.whitelist()
def get_carrier():
    clickpost = ClickpostCarrier()
    try:
        response = clickpost.get_carrier()

        return {
            "status": "success" if response else "failed",
            "response": response
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": str(e).replace(clickpost.api_key, "****")
        }

# @frappe.whitelist()
# def update_carrier_partners(carriers):
#     """Update or create Carrier Partner records based on Clickpost carriers data"""
#     if isinstance(carriers, str):
#         carriers = json.loads(carriers)
    
#     created_count = 0
#     updated_count = 0
    
#     try:
#         for carrier in carriers:
#             carrier_id = carrier.get("partner_id")
#             carrier_name = carrier.get("account_code")
            
#             if not carrier_id or not carrier_name:
#                 continue

#             doc_carrier_name = f"{carrier_id}-{carrier_name}"
                
#             # Check if carrier already exists
#             existing_carrier = frappe.db.exists("Carrier Partner", {"name": doc_carrier_name})

#             frappe.msgprint(carrier.get("partner_id"))
            
#             if existing_carrier:
#                 # Update existing carrier
#                 doc = frappe.get_doc("Carrier Partner", existing_carrier)
#                 doc.clickpost_partner_name = carrier_name or ""
#                 doc.account_name = carrier.get("courier_partenr_name") or ""
#                 doc.active = 1 if carrier.get("active", 'true') else 0
#                 doc.is_rvp = 1 if carrier.get("is_rvp", 'true') else 0
#                 doc.account_id = carrier.get("account_id") or ""
#                 doc.reference_number = carrier.get("courier_partner_pk") or ""
#                 doc.save()
#                 updated_count += 1
#             else:
#                 # Create new carrier
#                 doc = frappe.new_doc("Carrier Partner")
#                 doc.clickpost_partner_id = carrier_id
#                 doc.clickpost_partner_name = carrier_name or ""
#                 doc.account_name = carrier.get("account_code") or ""
#                 doc.active = 1 if carrier.get("active", 'true') else 0
#                 doc.is_rvp = 1 if carrier.get("is_rvp", 'true') else 0
#                 doc.account_id = carrier.get("account_id") or ""
#                 doc.reference_number = carrier.get("courier_partner_pk") or ""
#                 doc.insert()
#                 created_count += 1
        
#         frappe.db.commit()
#         return {
#             "status": "success",
#             "created": created_count,
#             "updated": updated_count,
#             "message": _("{0} carriers created, {1} carriers updated").format(created_count, updated_count)
#         }
    
#     except Exception as e:
#         frappe.db.rollback()
#         frappe.log_error(frappe.get_traceback(), _("Clickpost Update Carriers Error"))
#         return {
#             "status": "error",
#             "message": str(e)
#         }

@frappe.whitelist()
def update_carrier_partners(carriers):
    """Update or create Carrier Partner records based on Clickpost carriers data"""
    if isinstance(carriers, str):
        carriers = json.loads(carriers)
    
    created_count = 0
    updated_count = 0
    
    try:
        # Get all existing carrier partners for efficient lookup
        existing_carriers = frappe.get_all(
            "Carrier Partner", 
            fields=["name", "clickpost_partner_id", "clickpost_partner_name"],
            as_list=0
        )
        
        # Create a dictionary for faster lookup
        existing_carrier_dict = {carrier.name: carrier for carrier in existing_carriers}
        
        # Process carriers in batches
        for carrier in carriers:
            carrier_id = carrier.get("partner_id")
            carrier_name = carrier.get("account_code")
            
            if not carrier_id or not carrier_name:
                continue

            doc_carrier_name = f"{carrier_id}-{carrier_name}"
            
            # Check if carrier already exists
            if doc_carrier_name in existing_carrier_dict:
                # Update existing carrier
                doc = frappe.get_doc("Carrier Partner", doc_carrier_name)
                doc.clickpost_partner_name = carrier_name or ""
                doc.account_name = carrier.get("courier_partenr_name") or ""
                doc.active = 1 if carrier.get("active", 'true') else 0
                doc.is_rvp = 1 if carrier.get("is_rvp", 'true') else 0
                doc.account_id = carrier.get("account_id") or ""
                doc.reference_number = carrier.get("courier_partner_pk") or ""
                doc.save()
                updated_count += 1
            else:
                # Create new carrier
                doc = frappe.new_doc("Carrier Partner")
                doc.clickpost_partner_id = carrier_id
                doc.clickpost_partner_name = carrier_name or ""
                doc.account_name = carrier.get("account_code") or ""
                doc.active = 1 if carrier.get("active", 'true') else 0
                doc.is_rvp = 1 if carrier.get("is_rvp", 'true') else 0
                doc.account_id = carrier.get("account_id") or ""
                doc.reference_number = carrier.get("courier_partner_pk") or ""
                doc.insert()
                created_count += 1
        
        frappe.db.commit()
                
        return {
            "status": "success",
            "created": created_count or 0,
            "updated": updated_count or 0,
            "message": f"{created_count} carriers created, {updated_count} carriers updated"
        }
    
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), _("Clickpost Update Carriers Error"))
        return {
            "status": "error",
            "message": str(e)
        }
