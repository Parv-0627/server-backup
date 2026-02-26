# clickpost_erpnext_integration/clickpost_erpnext_integration/utils.py
import frappe
import requests
import os
from frappe.utils import get_files_path
from frappe.utils.file_manager import save_file

import frappe
import datetime
from frappe import _
from clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment import get_proof_of_delivery

@frappe.whitelist()
def track_shipment_scheduler():
    """
    Track shipment in ClickPost
    """
    try:
        # Get all shipments with ClickPost status
        shipments = frappe.get_all("Shipment", 
                                   filters={
                                       "awb_number": ["!=", ""],
                                       "docstatus": 1,
                                       "shipment_id": ["!=", ""],
                                       "custom_clickpost_status": ["!=", "Cancelled"]
                                       })
        
        for shipment in shipments:
            # Get the shipment document
            shipment_doc = frappe.get_doc("Shipment", shipment.name)
            
            # Call the track_shipment method
            response = frappe.call(
                "clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment.track_shipment",
                waybill=shipment_doc.awb_number,
                cp_id=shipment_doc.custom_carrier_partner_id
            )
            
            # Process the response
            if response and response.get("status") == "success":
                result = response.get("response", {}).get("result", {})
                awb_number = shipment_doc.awb_number
                shipment_data = result.get(awb_number)
                
                if shipment_data:
                    # Update the shipment tracking data
                    update_response = frappe.call(
                        "clickpost_erpnext_integration.clickpost_erpnext_integration.utils.update_shipment_tracking",
                        shipment_name=shipment_doc.name,
                        tracking_data=shipment_data
                    )
                    
                    if update_response and update_response.get("success"):
                        # Reload the document to show updated data
                        updated_doc = frappe.get_doc("Shipment", shipment_doc.name)
                        updated_doc.reload()
                        # Log success message
                        message = f"{response.get('response', {}).get('meta', {}).get('message', '')}, shipment tracked successfully"
                        frappe.msgprint(message, title="Success", indicator="green")
                    else:
                        error_message = update_response.get("error", "Failed to update shipment tracking data")
                        frappe.msgprint(error_message, title="Error", indicator="red")
                        frappe.log_error(error_message, f"ClickPost Track Shipment Update Error - {shipment_doc.name}")
            else:
                error_message = response.get("message", "Failed to track shipment")
                frappe.log_error(error_message, f"ClickPost Track Shipment Error - {shipment.name}")
    except Exception as e:
        frappe.log_error(f"Error tracking ClickPost shipment: {str(e)}", "ClickPost Shipment Tracking")

@frappe.whitelist()
def track_awb_scheduler():
    """
    Track shipment in ClickPost
    """
    try:
        # Get all shipments with ClickPost status
        shipments = frappe.get_all("AWB Registration", 
                                   filters={
                                       "awb_number": ["!=", ""],
                                       "docstatus": 1,
                                       "shipment_id": ["!=", ""],
                                       "clickpost_status": ["!=", "Cancelled"]
                                       })
        
        for shipment in shipments:
            # Get the shipment document
            shipment_doc = frappe.get_doc("AWB Registration", shipment.name)
            
            # Call the track_shipment method
            response = frappe.call(
                "clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment.track_shipment",
                waybill=shipment_doc.awb_number,
                cp_id=shipment_doc.carrier_partner_id
            )
            
            # Process the response
            if response and response.get("status") == "success":
                result = response.get("result", {})
                awb_number = shipment_doc.awb_number
                shipment_data = result.get(awb_number)
                
                if shipment_data:
                    # Update the shipment tracking data
                    update_response = frappe.call(
                        "clickpost_erpnext_integration.clickpost_erpnext_integration.utils.update_awb_tracking",
                        shipment_name=shipment_doc.name,
                        tracking_data=shipment_data
                    )
                    
                    if update_response:
                        # Reload the document to show updated data
                        updated_doc = frappe.get_doc("AWB Registration", shipment_doc.name)
                        updated_doc.reload()
                        # Log success message
                        message = f"AWB Registration tracked successfully"
                        frappe.msgprint(message, title="Success", indicator="green")
                    else:
                        error_message = "Failed to update AWB Registration tracking data"
                        # frappe.msgprint(error_message, title="Error", indicator="red")
                        frappe.log_error(error_message, f"ClickPost Track AWB Registration Update Error - {shipment_doc.name}")
            else:
                error_message = "Failed to track AWB Registration"
                frappe.log_error(error_message, f"ClickPost Track AWB Registration Error - {shipment.name}")
    except Exception as e:
        frappe.log_error("ClickPost AWB Registration Tracking", f"Error tracking ClickPost AWB Registration: {str(e)}")


@frappe.whitelist()
def sync_shipment(shipment_name):
    """
    Python version of the sync_shipment function for cron job use
    
    Args:
        shipment_name (str): The name of the Shipment document to sync
    """
    try:
        # Get the shipment document
        shipment_doc = frappe.get_doc("Shipment", shipment_name)
        
        # Call the sync_shipment method
        response = frappe.call(
            "clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment.sync_shipment",
            reference_number=shipment_doc.name,
            courier_partner=shipment_doc.custom_carrier_partner_id,
            account_code=shipment_doc.custom_carrier_partner_name
        )
        
        # Process the response
        if not response.get("response", {}).get("meta", {}).get("success", True):
            error_message = response.get("response", {}).get("meta", {}).get("message")
            frappe.log_error(error_message, f"ClickPost Sync Shipment Error - {shipment_name}")
            return
        
        if response and response.get("status") == "success":
            shipment = response.get("response", {}).get("result", {})
            tracking_id = response.get("response", {}).get("tracking_id")
            
            # Add shipment update entry
            if shipment:
                shipment_doc.append("custom_shipment_update", {
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "tracking_id": tracking_id
                })
            
            # Update waybill number
            waybill_number = response.get("response", {}).get("result", {}).get("waybill")
            if waybill_number:
                shipment_doc.custom_waybill_number = waybill_number
                
            # Save the document
            shipment_doc.save()
            
            # Check if label exists in the response
            if shipment and shipment.get("label"):
                # Download and attach the file
                attach_result = frappe.call(
                    "clickpost_erpnext_integration.clickpost_erpnext_integration.utils.download_and_attach_file",
                    url=shipment["label"],
                    doctype="Shipment",
                    docname=shipment_doc.name,
                    filename=f"{shipment_doc.name}_label.pdf"
                )
                
                if not attach_result.get("success"):
                    error_message = attach_result.get("error", "Unknown error")
                    frappe.log_error(f"Failed to attach label: {error_message}", f"ClickPost Label Attachment Error - {shipment_name}")
            frappe.db.commit()
        else:
            error_message = response.get("message", "Failed to sync shipment")
            frappe.log_error(error_message, f"ClickPost Sync Shipment Error - {shipment_name}")
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"ClickPost Sync Shipment Error - {shipment_name}")

@frappe.whitelist()
def sync_all_pending_shipments():
    """
    Function to be called by cron job to sync all pending shipments
    """
    # Get all submitted shipments that have a ClickPost ID but no waybill number
    shipments = frappe.get_all(
        "Shipment",
        filters={
            "docstatus": 1,
            "shipment_id": ["!=", ""],
            "awb_number": ["in", ["", None]],
            "custom_clickpost_status": ["!=", "Cancelled"]
        },
        fields=["name"]
    )
    
    for shipment in shipments:
       return sync_shipment(shipment.name)
  

@frappe.whitelist()
def download_and_attach_file(url, doctype, docname, filename):
    try:
        # Download the file from the URL
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Create a temporary file
        temp_file_path = os.path.join(get_files_path(), filename)
        
        # Write the content to the file
        with open(temp_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Save and attach the file to the document
        file_doc = save_file(
            filename,
            open(temp_file_path, 'rb').read(),
            doctype,
            docname,
            is_private=0
        )
        
        # Clean up the temporary file
        os.remove(temp_file_path)
        
        return {"success": True, "file_url": file_doc.file_url}
    
    except Exception as e:
        frappe.log_error(f"Error downloading and attaching file: {str(e)}", "ClickPost Label Attachment")
        return {"success": False, "error": str(e)}
    

@frappe.whitelist()
def get_unshipped_sales_invoices(doctype, txt, searchfield, start, page_len, filters):
    """
    Returns a list of Sales Invoices that are not linked to any Shipment
    """
    # Query to find sales invoices that don't have a shipment reference
    # or are not in any existing shipment's custom_sales_invoice child table
    
    # First, get all sales invoices that are already in shipments
    shipped_invoices = frappe.db.sql("""
        SELECT DISTINCT si.sales_invoice 
        FROM `tabSales Invoice Shipment` si
        WHERE si.parenttype = 'Shipment'
    """)
    
    # Convert to a list of invoice names
    shipped_invoice_names = [x[0] for x in shipped_invoices]
    
    # Add condition for text search if provided
    search_condition = ""
    if txt:
        search_condition = f"AND (si.name LIKE '%{txt}%' OR si.customer_name LIKE '%{txt}%')"
    
    # Query to get unshipped invoices
    unshipped_invoices = frappe.db.sql("""
        SELECT si.name, si.customer_name, si.posting_date, si.grand_total
        FROM `tabSales Invoice` si
        WHERE si.docstatus = 1
        AND (si.custom_shipment_reference IS NULL OR si.custom_shipment_reference = '')
        AND si.name NOT IN ({shipped_list})
        {search_cond}
        ORDER BY si.posting_date DESC
        LIMIT {start}, {page_len}
    """.format(
        shipped_list=", ".join(["'%s'" % d for d in shipped_invoice_names]) if shipped_invoice_names else "''",
        search_cond=search_condition,
        start=start,
        page_len=page_len
    ), as_list=1)
    
    return unshipped_invoices


@frappe.whitelist()
def update_shipment_tracking(shipment_name, tracking_data):
    try:
        # Convert tracking_data from string to dict if needed
        if isinstance(tracking_data, str):
            import json
            tracking_data = json.loads(tracking_data)
        
        # Get the shipment document
        shipment = frappe.get_doc("Shipment", shipment_name)
        
        # Handle latest status
        if tracking_data.get("latest_status"):
            latest = tracking_data["latest_status"]
            latest_status = latest.get("status")
            
            # First, set all existing is_latest to 0
            for update in shipment.custom_shipment_update:
                if update.is_latest == 1:
                    update.is_latest = 0
            
            # Check if we already have an entry with this status
            existing_status_idx = None
            for i, update in enumerate(shipment.custom_shipment_update):
                if update.status == latest_status:
                    existing_status_idx = i
                    break
            
            if existing_status_idx is not None:
                # Update the existing entry with this status
                update_entry = shipment.custom_shipment_update[existing_status_idx]
                update_entry.timestamp = latest.get("timestamp")
                update_entry.location = latest.get("location")
                update_entry.remark = latest.get("remark")
                update_entry.remark_copy = latest.get("remark")
                update_entry.clickpost_status_code = latest.get("clickpost_status_code")
                update_entry.clickpost_status_description = latest.get("clickpost_status_description")
                # update_entry.clickpost_status_bucket = int(latest.get("clickpost_status_bucket"))
                # update_entry.clickpost_status_bucket_description = latest.get("clickpost_status_bucket_description")
                update_entry.created_at = latest.get("created_at")
                update_entry.is_latest = 1
            else:
                # Add a new entry for this status
                shipment.append("custom_shipment_update", {
                    "timestamp": latest.get("timestamp"),
                    "location": latest.get("location"),
                    "remark": latest.get("remark"),
                    "remark_copy": latest.get("clickpost_status_description"),
                    "status": latest_status,
                    "clickpost_status_code": latest.get("clickpost_status_code"),
                    "clickpost_status_description": latest.get("clickpost_status_description"),
                    # "clickpost_status_bucket": latest.get("clickpost_status_bucket"),
                    # "clickpost_status_bucket_description": latest.get("clickpost_status_bucket_description"),
                    "created_at": latest.get("created_at"),
                    "is_latest": 1
                })
            
            # Update the main document tracking status
            shipment.tracking_status = latest.get("clickpost_status_description")
            shipment.tracking_status_info = latest.get("remark")
        
        # Handle scans
        if tracking_data.get("scans"):
            # Create a dictionary to track existing statuses
            existing_statuses = {}
            
            # First, map all existing statuses to their row indices
            for i, update in enumerate(shipment.custom_shipment_update):
                if update.status:
                    existing_statuses[update.status] = i
            
            for scan in tracking_data["scans"]:
                scan_status = scan.get("status")
                
                # Skip if no status
                if not scan_status:
                    continue
                
                # Check if we already have an entry with this status
                if scan_status in existing_statuses:
                    # Update existing entry with this status
                    idx = existing_statuses[scan_status]
                    update_entry = shipment.custom_shipment_update[idx]
                    # Always update with the latest scan data
                    # No timestamp comparison needed - we're just keeping one entry per status
                    update_entry.timestamp = scan.get("timestamp")
                    update_entry.location = scan.get("location")
                    update_entry.remark = scan.get("remark")
                    update_entry.remark_copy = scan.get("clickpost_status_description")
                    update_entry.clickpost_status_code = scan.get("clickpost_status_code")
                    update_entry.clickpost_status_description = scan.get("clickpost_status_description")
                    # update_entry.clickpost_status_bucket = int(scan.get("clickpost_status_bucket"))
                    # update_entry.clickpost_status_bucket_description = scan.get("clickpost_status_bucket_description")
                    update_entry.created_at = scan.get("created_at")
                    update_entry.checkpoint_id = scan.get("checkpoint_id")
                    update_entry.tracking_id = scan.get("tracking_id")
                else:
                    # Add a new entry for this status
                    new_idx = len(shipment.custom_shipment_update)
                    shipment.append("custom_shipment_update", {
                        "timestamp": scan.get("timestamp"),
                        "location": scan.get("location"),
                        "remark": scan.get("remark"),
                        "remark_copy": scan.get("clickpost_status_description"),
                        "status": scan_status,
                        "clickpost_status_code": scan.get("clickpost_status_code"),
                        "clickpost_status_description": scan.get("clickpost_status_description"),
                        # "clickpost_status_bucket": int(scan.get("clickpost_status_bucket")),
                        # "clickpost_status_bucket_description": scan.get("clickpost_status_bucket_description"),
                        "created_at": scan.get("created_at"),
                        "checkpoint_id": scan.get("checkpoint_id"),
                        "tracking_id": scan.get("tracking_id"),
                        "is_latest": 0  # Set to 0 since this is not the latest status
                    })
                    
                    # Add to our tracking dictionary
                    existing_statuses[scan_status] = new_idx
        
        updates_list = list(shipment.custom_shipment_update)
        
        def get_timestamp_key(update):
            if not update.timestamp:
                return ""
            
            # If it's already a datetime object, return it
            if isinstance(update.timestamp, datetime.datetime):
                return update.timestamp
            
            # Try to parse the timestamp string to a datetime object
            try:
                # Try different formats
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"]:
                    try:
                        return datetime.datetime.strptime(update.timestamp, fmt)
                    except ValueError:
                        continue
            except Exception:
                # If parsing fails, return the original string
                return update.timestamp
            
            # If all parsing attempts fail, return the original string
            return update.timestamp
        
        # Sort by timestamp in descending order (newest first)
        sorted_updates = sorted(updates_list, key=get_timestamp_key, reverse=True)
        # Clear the existing table and add sorted entries
        shipment.custom_shipment_update = []
        for update in sorted_updates:
            shipment.append("custom_shipment_update", {
                "timestamp": update.timestamp,
                "location": update.location,
                "remark": update.remark,
                "remark_copy": update.clickpost_status_description,
                "status": update.status,
                "clickpost_status_code": update.clickpost_status_code,
                "clickpost_status_description": update.clickpost_status_description,
                # "clickpost_status_bucket": update.clickpost_status_bucket,
                # "clickpost_status_bucket_description": update.clickpost_status_bucket_description,
                "created_at": update.created_at,
                "checkpoint_id": getattr(update, "checkpoint_id", None),
                "tracking_id": getattr(update, "tracking_id", None),
                "is_latest": update.is_latest
            })
        
        # # Save the document
        shipment.save()
       
        return {"success": True}
    except Exception as e:
        frappe.log_error(f"Error updating shipment tracking: {str(e)}", "Clickpost Shipment Tracking Update")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def update_awb_tracking(shipment_name, tracking_data):
    try:
        # Convert tracking_data from string to dict if needed
        if isinstance(tracking_data, str):
            import json
            tracking_data = json.loads(tracking_data)
        
        # Get the shipment document
        shipment = frappe.get_doc("AWB Registration", shipment_name)
        
        # Handle latest status
        if tracking_data.get("latest_status"):
            latest = tracking_data["latest_status"]
            latest_status = latest.get("status")
            
            # First, set all existing is_latest to 0
            for update in shipment.shipment_update:
                if update.is_latest == 1:
                    update.is_latest = 0
            
            # Check if we already have an entry with this status
            existing_status_idx = None
            for i, update in enumerate(shipment.shipment_update):
                if update.status == latest_status:
                    existing_status_idx = i
                    break
            
            if existing_status_idx is not None:
                # Update the existing entry with this status
                update_entry = shipment.shipment_update[existing_status_idx]
                update_entry.timestamp = latest.get("timestamp")
                update_entry.location = latest.get("location")
                update_entry.remark = latest.get("remark")
                update_entry.remark_copy = latest.get("remark")
                update_entry.clickpost_status_code = latest.get("clickpost_status_code")
                update_entry.clickpost_status_description = latest.get("clickpost_status_description")
                # update_entry.clickpost_status_bucket = int(latest.get("clickpost_status_bucket"))
                # update_entry.clickpost_status_bucket_description = latest.get("clickpost_status_bucket_description")
                update_entry.created_at = latest.get("created_at")
                update_entry.is_latest = 1
            else:
                # Add a new entry for this status
                shipment.append("shipment_update", {
                    "timestamp": latest.get("timestamp"),
                    "location": latest.get("location"),
                    "remark": latest.get("remark"),
                    "remark_copy": latest.get("clickpost_status_description"),
                    "status": latest_status,
                    "clickpost_status_code": latest.get("clickpost_status_code"),
                    "clickpost_status_description": latest.get("clickpost_status_description"),
                    # "clickpost_status_bucket": latest.get("clickpost_status_bucket"),
                    # "clickpost_status_bucket_description": latest.get("clickpost_status_bucket_description"),
                    "created_at": latest.get("created_at"),
                    "is_latest": 1
                })
            
            # Update the main document tracking status
            shipment.tracking_status = latest.get("clickpost_status_description")
            shipment.tracking_status_info = latest.get("remark")
        
        # Handle scans
        if tracking_data.get("scans"):
            # Create a dictionary to track existing statuses
            existing_statuses = {}
            
            # First, map all existing statuses to their row indices
            for i, update in enumerate(shipment.shipment_update):
                if update.status:
                    existing_statuses[update.status] = i
            
            for scan in tracking_data["scans"]:
                scan_status = scan.get("status")
                
                # Skip if no status
                if not scan_status:
                    continue
                
                # Check if we already have an entry with this status
                if scan_status in existing_statuses:
                    # Update existing entry with this status
                    idx = existing_statuses[scan_status]
                    update_entry = shipment.shipment_update[idx]
                    # Always update with the latest scan data
                    # No timestamp comparison needed - we're just keeping one entry per status
                    update_entry.timestamp = scan.get("timestamp")
                    update_entry.location = scan.get("location")
                    update_entry.remark = scan.get("remark")
                    update_entry.remark_copy = scan.get("clickpost_status_description")
                    update_entry.clickpost_status_code = scan.get("clickpost_status_code")
                    update_entry.clickpost_status_description = scan.get("clickpost_status_description")
                    # update_entry.clickpost_status_bucket = int(scan.get("clickpost_status_bucket"))
                    # update_entry.clickpost_status_bucket_description = scan.get("clickpost_status_bucket_description")
                    update_entry.created_at = scan.get("created_at")
                    update_entry.checkpoint_id = scan.get("checkpoint_id")
                    update_entry.tracking_id = scan.get("tracking_id")
                else:
                    # Add a new entry for this status
                    new_idx = len(shipment.shipment_update)
                    shipment.append("shipment_update", {
                        "timestamp": scan.get("timestamp"),
                        "location": scan.get("location"),
                        "remark": scan.get("remark"),
                        "remark_copy": scan.get("clickpost_status_description"),
                        "status": scan_status,
                        "clickpost_status_code": scan.get("clickpost_status_code"),
                        "clickpost_status_description": scan.get("clickpost_status_description"),
                        # "clickpost_status_bucket": int(scan.get("clickpost_status_bucket")),
                        # "clickpost_status_bucket_description": scan.get("clickpost_status_bucket_description"),
                        "created_at": scan.get("created_at"),
                        "checkpoint_id": scan.get("checkpoint_id"),
                        "tracking_id": scan.get("tracking_id"),
                        "is_latest": 0  # Set to 0 since this is not the latest status
                    })
                    
                    # Add to our tracking dictionary
                    existing_statuses[scan_status] = new_idx
        
        updates_list = list(shipment.shipment_update)
        
        def get_timestamp_key(update):
            if not update.timestamp:
                return ""
            
            # If it's already a datetime object, return it
            if isinstance(update.timestamp, datetime.datetime):
                return update.timestamp
            
            # Try to parse the timestamp string to a datetime object
            try:
                # Try different formats
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"]:
                    try:
                        return datetime.datetime.strptime(update.timestamp, fmt)
                    except ValueError:
                        continue
            except Exception:
                # If parsing fails, return the original string
                return update.timestamp
            
            # If all parsing attempts fail, return the original string
            return update.timestamp
        
        # Sort by timestamp in descending order (newest first)
        sorted_updates = sorted(updates_list, key=get_timestamp_key, reverse=True)
        # Clear the existing table and add sorted entries
        shipment.shipment_update = []
        for update in sorted_updates:
            shipment.append("shipment_update", {
                "timestamp": update.timestamp,
                "location": update.location,
                "remark": update.remark,
                "remark_copy": update.clickpost_status_description,
                "status": update.status,
                "clickpost_status_code": update.clickpost_status_code,
                "clickpost_status_description": update.clickpost_status_description,
                # "clickpost_status_bucket": update.clickpost_status_bucket,
                # "clickpost_status_bucket_description": update.clickpost_status_bucket_description,
                "created_at": update.created_at,
                "checkpoint_id": getattr(update, "checkpoint_id", None),
                "tracking_id": getattr(update, "tracking_id", None),
                "is_latest": update.is_latest
            })
        
        # # Save the document
        shipment.save()
       
        return {"success": True}
    except Exception as e:
        frappe.log_error("Clickpost AWB Tracking Update", f"Error updating AWB tracking: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def sync_proof_of_delivery():
    """
    Function to be called by cron job to fetch and attach proof of delivery for shipments
    that have AWB numbers but don't have proof of delivery attachments
    """
    try:
        # Get all submitted shipments that have a waybill number but no POD attachment
        shipments = frappe.get_all(
            "Shipment",
            filters={
                "docstatus": 1,
                "awb_number": ["!=", ""],
                "custom_clickpost_status": ["!=", "Cancelled"],  # Only get delivered shipments
            },
            fields=["name", "awb_number", "custom_carrier_partner_id", "custom_carrier_partner_name", "custom_pod_file"]
        )
        
        count = 0
        for shipment in shipments:
            # Check if POD is already attached
            has_delivered_status = frappe.db.exists(
                "Shipment Update",
                {
                    "parent": shipment.name,
                    "status": "DELIVERED",
                    "parenttype": "Shipment"
                }
            )
            
            # If no POD attachment exists, fetch it
            if not shipment.custom_pod_file and has_delivered_status:
                response = get_proof_of_delivery(
                    waybill=shipment.awb_number,
                    cp_id=shipment.custom_carrier_partner_id,
                )
                
                if response and response.get("status") == "success":
                    pod_url = response.get("response", {}).get("result", {}).get("pod_url")
                    
                    if pod_url:
                        # Download and attach the POD
                        attach_result = download_and_attach_file(
                            url=pod_url,
                            doctype="Shipment",
                            docname=shipment.name,
                            filename=f"pod_{shipment.name}.pdf"
                        )
                        frappe.db.set_value(
                            "Shipment", 
                            shipment.name,
                            "custom_pod_file", 
                            attach_result.get("file_url")
                        )
                        
                        if attach_result.get("success"):
                            count += 1
                            frappe.db.commit()
                        else:
                            error_message = attach_result.get("error", "Unknown error")
                            frappe.log_error(
                                f"Failed to attach POD: {error_message}", 
                                f"ClickPost POD Attachment Error - {shipment.name}"
                            )
                else:
                    error_message = response.get("message", "Failed to fetch proof of delivery")
                    frappe.log_error(
                        error_message, 
                        f"ClickPost POD Fetch Error - {shipment.name}"
                    )
        
        return {"success": True, "message": f"Attached POD for {count} shipments"}
    
    except Exception as e:
        frappe.log_error(
            frappe.get_traceback(), 
            "ClickPost Sync Proof of Delivery Error"
        )
        return {"success": False, "error": str(e)}
