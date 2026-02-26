import frappe
import json 
from frappe import _
import asyncio
import time

# Import helper functions
from clickpost_erpnext_integration.clickpost_erpnext_integration.helpers import (
    get_address_details,
    format_address,
    calculate_total_item_count,
    calculate_total_weight,
    recommendation_box,
    prepare_shipment_payload,
    sync_shipment_api,
    shipment_auto_log
)

# Import API functions directly
from clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment import (
    cancel_clickpost_awb,
    fetch_recommendation,
    create_clickpost_shipment
)

@frappe.whitelist()
def on_cancel(doc, method):
    # Find related sales invoice with this shipment ID
    sales_invoices = frappe.get_all(
        "Sales Invoice",
        filters={"custom_shipment_reference": doc.name},
        fields=["name"]
    )

    
    
    # Update each sales invoice to remove the shipment ID
    for invoice in sales_invoices:
        frappe.db.set_value("Sales Invoice", invoice.name, "custom_shipment_reference", None)
        frappe.msgprint(f"Removed shipment reference from Sales Invoice {invoice.name}")

    config = frappe.get_single("Clickpost Configuration")
    # Call the ClickPost API to cancel the AWB
    manual_update_status = config.manual_update_status == 1
    # Cancel the shipment in ClickPost
    if hasattr(doc, 'custom_carrier_partner_id') and hasattr(doc, 'custom_carrier_partner_name') and hasattr(doc, 'awb_number'):
        try:
            # Call the ClickPost API to cancel the shipment
            response = cancel_clickpost_awb(
                cp_id=doc.custom_carrier_partner_id,
                account_code=doc.custom_carrier_partner_name,
                waybill=doc.awb_number or doc.custom_awb_order,
                manual_update_status=manual_update_status,
            )
            
            response_json = json.loads(response) if isinstance(response, str) else response

            # Process the response
            if response:
                # Update the shipment status
                
                success = response.get("response", {}).get("meta", {}).get("success")

                if success:
                    frappe.db.set_value("Shipment", doc.name, "custom_clickpost_status", "Cancelled")

                    frappe.msgprint(
                        msg="ClickPost shipment cancelled successfully",
                        title="Success",
                        indicator="green"
                    )
                else:
                    error_message = response.get("response", {}).get("meta", {}).get("message")
                    frappe.throw(f"Shipment not created in clickpost, will only be cancelled in ERPNext")
            else:
                error_message = response.get("response", {}).get("meta", {}).get("message", "Unknown error occurred.")
                frappe.throw(f"Shipment not created in clickpost, will only be cancelled in ERPNext")

        except Exception as e:
            frappe.log_error("ClickPost Shipment Cancellation", f"Error cancelling ClickPost shipment: {str(e)}")
            frappe.msgprint(
                msg=f"Error cancelling ClickPost shipment: {str(e)}",
                title="Error",
                indicator="red"
            )
    
    frappe.db.commit()

@frappe.whitelist()
def get_last_clickpost_log_for_carrier(carrier_account_code):
    """Get the latest Clickpost Log for a specific carrier and create-b2b-order API."""
    # Adjust the field names if your doctype uses different ones
    logs = frappe.get_all(
        "Clickpost Log",
        filters={
            "api_url": "api/v1/create-b2b-order/",
            "payload": ["like", f"%{carrier_account_code}%"]
        },
        fields=["name"],
        order_by="creation desc",
        limit=1
    )
    return logs[0].name if logs else None

@frappe.whitelist()
def create_clickpost_shipment_api(name):
    """
    Create a ClickPost shipment with automatic carrier selection or using a predefined carrier.
    
    Args:
        name (str): The shipment document name
        
    Returns:
        dict: Result of the shipment creation
    """
    frm = frappe.get_doc("Shipment", name)
    
    # Check if a log already exists for this shipment
    existing_log = frappe.get_all(
        "Auto Shipment Creation Logs", 
        filters={"shipment_reference": frm.get("name")},
        order_by="creation desc",
        limit=1
    )
    
    log_id = existing_log[0].name if existing_log else None
    
    # Initialize log data
    log_data = {
        "shipment_reference": frm.get("name"),
        "awb_number": "",
        "recommendation_status": "False",
        "recommendation_message": "Starting shipment creation process",
        "order_creation_status": "Pending",
        "account_name": "",
        "allocated_carrier": "",
        "shipment_creation_time": frappe.utils.now_datetime(),
        "recommendation_reference": []
    }
    
    # Create or update the log
    log_id = update_shipment_log(log_id, log_data)
    
    # If no carrier partner is selected, go through recommendation flow
    if not frm.get("custom_carrier_partner"):
        pickup_address = get_address_details(frm.get("pickup_address_name"))
        delivery_address = get_address_details(frm.get("delivery_address_name"))
        
        # Prepare recommendation payload
        payload = [{
            "reference_number": frm.get("name"),
            "pickup_location_code": frm.get("pickup_address_name"),
            "pickup_name": frm.get("custom_pickup_contact_person_name"),
            "drop_location_code": frm.get("delivery_address_name"),
            "pickup_city": pickup_address.get("city"),
            "is_restricted": "false",
            "drop_city": delivery_address.get("city"),
            "pickup_state": pickup_address.get("state"),
            "drop_state": delivery_address.get("state"),
            "pickup_address": format_address(frm.get("pickup_address")),
            "drop_address": format_address(frm.get("delivery_address")),
            "zone": "WEST",
            "box_code": "Small-Box-01",
            "item_count": calculate_total_item_count(frm),
            "pickup_pincode": pickup_address.get("pincode"),
            "drop_pincode": delivery_address.get("pincode"),
            "invoice_value": frm.get("value_of_goods"),
            "weight": calculate_total_weight(frm),
            "delivery_type": frm.get("custom_delivery_type"),
            "order_type": frm.get("custom_order_type"),
            "boxes": recommendation_box(frm)
        }]
        
        # Get carrier recommendations
        recommendations = []
        recommendations_error = {}
        
        try:
            # Call fetch_recommendation directly
            result = fetch_recommendation(payload=payload)
            
            if result and result.get("status") == "success":
                recommendations = result.get("response", {}).get("result", [{}])[0].get("preference_array", [])
                recommendations_error = result.get("response", {}).get("result", [{}])[0]
                
                # Update log with recommendation success
                log_data["recommendation_status"] = "True"
                log_data["recommendation_message"] = "Successfully fetched recommendations"
                log_id = update_shipment_log(log_id, log_data)
        except Exception as e:
            # Update log with recommendation failure
            log_data["recommendation_status"] = "False"
            log_data["recommendation_message"] = f"Error while calling the recommendation API: {str(e)}"
            log_data["order_creation_status"] = "Error"
            log_id = update_shipment_log(log_id, log_data)
            frappe.log_error(f"Error fetching recommendations: {str(e)}", "ClickPost Recommendation Error")
            return {"success": False, "message": f"Error fetching recommendations: {str(e)}"}
        
        if not recommendations:
            log_data["recommendation_message"] = f"No carriers available: {str(recommendations_error)}"
            log_data["order_creation_status"] = "Error"
            log_id = update_shipment_log(log_id, log_data)
            return {"success": False, "message": "No carriers available"}
        
        success = False
        successful_carrier = None
        attempts = []
        recommendation_reference = []
        
        # Try up to 3 carriers
        for i in range(min(3, len(recommendations))):
            rec = recommendations[i]
            
            # Update the shipment with the current carrier
            frappe.db.set_value("Shipment", frm.get("name"), {
                "custom_carrier_partner": f"{rec.get('cp_id')}-{rec.get('account_code')}",
                "custom_carrier_partner_id": rec.get("cp_id"),
                "custom_carrier_partner_name": rec.get("account_code")
            })
            
            # Reload the document to get updated values
            frm = frappe.get_doc("Shipment", frm.get("name"))
            
            # Prepare shipment payload with the selected carrier
            shipment_data = prepare_shipment_payload(frm)
            
            attempt = {"carrier": rec.get("account_code"), "error": None}
            
            current_recommendation = {
                "carrier_name": rec.get("account_code"),
                "status": "Pending",
                "message": "Attempting to create shipment",
                # "clickpost_log": None  # Will set after API call

            }
            recommendation_reference.append(current_recommendation)
            
            # Update log with current attempt
            log_data["recommendation_reference"] = recommendation_reference
            log_data["recommendation_message"] = f"Attempting carrier: {rec.get('account_code')}"
            log_id = update_shipment_log(log_id, log_data)
            
            try:
                # Call create_clickpost_shipment directly
                result = create_clickpost_shipment(shipment_data=json.dumps(shipment_data))
                
                if (result.get("status") == "success" and 
                    result.get("response", {}).get("meta", {}).get("success")):
                    
                    # Update shipment ID
                    frappe.db.set_value("Shipment", frm.get("name"), {
                        "shipment_id": result.get("response", {}).get("meta", {}).get("b2b_shipment_id")
                    })
                    
                    # Reload the document
                    frm = frappe.get_doc("Shipment", frm.get("name"))
                    
                    # Update log with shipment creation success
                    current_recommendation["status"] = "Processing"
                    current_recommendation["message"] = "Shipment created, syncing..."
                    log_name = get_last_clickpost_log_for_carrier(rec.get("account_code"))
                    # frappe.log_error(f"ClickPost Log: {log_name}", "ClickPost Log")
                    current_recommendation["clickpost_log"] = log_name
                    log_data["recommendation_reference"] = recommendation_reference
                    log_data["recommendation_message"] = "Shipment created, syncing..."
                    log_id = update_shipment_log(log_id, log_data)

                    while True:
                        try:
                            time.sleep(5)  # Wait for a few seconds before syncing
                            # Sync the shipment
                            sync_result = sync_shipment_api(frm)
                            sync_message = sync_result.get("message")
                            status_code = str(sync_result.get("status"))
                            
                            if str(status_code) == "200" and sync_result.get("success"):
                                frappe.log_error(title="condition 1")
                                success = True
                                successful_carrier = rec
                                
                                # Update log data for successful shipment
                                current_recommendation["status"] = "Success"
                                current_recommendation["message"] = sync_result.get("message")
                                log_name = get_last_clickpost_log_for_carrier(rec.get("account_code"))
                                current_recommendation["clickpost_log"] = log_name
                                # recommendation_reference.append(current_recommendation)
                                log_data["order_creation_status"] = "Success"
                                log_data["account_name"] = rec.get("account_code")
                                log_data["allocated_carrier"] = rec.get("account_code")
                                log_data["awb_number"] = sync_result.get("waybill") or ""
                                log_data["recommendation_reference"] = recommendation_reference
                                log_data["recommendation_message"] = "Shipment created and synced successfully"
                                
                                log_id = update_shipment_log(log_id, log_data)
                                break
                                
                            elif str(status_code) in ["103", "102"]:
                                frappe.log_error(title="condition 2")
                                # Continue retrying for processing status codes
                                current_recommendation["message"] = sync_message
                                log_name = get_last_clickpost_log_for_carrier(rec.get("account_code"))
                                current_recommendation["clickpost_log"] = log_name
                                log_data["recommendation_reference"] = recommendation_reference
                                log_data["recommendation_message"] = "Processing order"
                                
                                log_id = update_shipment_log(log_id, log_data)
                                continue  # retry
                                
                            elif str(status_code) in ["354", "500", "400","420"] or not sync_result.get("success"):
                                frappe.log_error(title="condition 3")
                                # Break on error status codes
                                current_recommendation["status"] = "Failed"
                                current_recommendation["message"] = sync_message
                                log_name = get_last_clickpost_log_for_carrier(rec.get("account_code"))
                                current_recommendation["clickpost_log"] = log_name
                                log_data["recommendation_reference"] = recommendation_reference
                                log_data["recommendation_message"] = f"Error status {status_code}: {sync_message}"
                                
                                log_id = update_shipment_log(log_id, log_data)
                                break  # Move to next carrier
                                
                            else:
                                frappe.log_error(title="condition 4")
                                # Handle any other status codes
                                current_recommendation["message"] = sync_message
                                log_name = get_last_clickpost_log_for_carrier(rec.get("account_code"))
                                current_recommendation["clickpost_log"] = log_name
                                log_data["recommendation_reference"] = recommendation_reference
                                log_data["recommendation_message"] = f"Unknown status {status_code}"
                                
                                log_id = update_shipment_log(log_id, log_data)
                                continue  # retry
                                
                        except Exception as sync_error:
                            attempt["error"] = f"Sync exception: {str(sync_error)}"
                            
                            current_recommendation["status"] = "Sync Failed"
                            current_recommendation["message"] = str(sync_error)
                            log_name = get_last_clickpost_log_for_carrier(rec.get("account_code"))
                            current_recommendation["clickpost_log"] = log_name
                            log_data["recommendation_reference"] = recommendation_reference
                            log_data["recommendation_message"] = f"Sync exception: {str(sync_error)}"
                            
                            log_id = update_shipment_log(log_id, log_data)
                            
                            # Reset carrier if sync failed
                            frappe.db.set_value("Shipment", frm.get("name"), {
                                "shipment_id": "",
                                "custom_carrier_partner": "",
                                "custom_carrier_partner_id": "",
                                "custom_carrier_partner_name": ""
                            })
                            
                            # Reload the document
                            frm = frappe.get_doc("Shipment", frm.get("name"))
                            break  # Break on exception and move to next carrier
                            
                else:
                    error_msg = (result.get("response", {}).get("meta", {}).get("message") or
                                "Unknown shipment creation error")
                    attempt["error"] = error_msg
                    
                    current_recommendation["status"] = "Shipment Failed"
                    current_recommendation["message"] = error_msg
                    log_name = get_last_clickpost_log_for_carrier(rec.get("account_code"))
                    current_recommendation["clickpost_log"] = log_name
                    log_data["recommendation_reference"] = recommendation_reference
                    log_data["recommendation_message"] = f"Shipment creation failed: {error_msg}"
                    
                    log_id = update_shipment_log(log_id, log_data)
                    
                    # Reset carrier if creation failed
                    frappe.db.set_value("Shipment", frm.get("name"), {
                        "shipment_id": "",
                        "custom_carrier_partner": "",
                        "custom_carrier_partner_id": "",
                        "custom_carrier_partner_name": ""
                    })
                    # Reload the document
                    frm = frappe.get_doc("Shipment", frm.get("name"))
            
            except Exception as shipment_error:
                attempt["error"] = f"Error during shipment creation: {str(shipment_error)}"
                
                current_recommendation["status"] = "Shipment Exception Failed"
                current_recommendation["message"] = str(shipment_error)
                log_name = get_last_clickpost_log_for_carrier(rec.get("account_code"))
                current_recommendation["clickpost_log"] = log_name
                log_data["recommendation_reference"] = recommendation_reference
                log_data["recommendation_message"] = f"Error during shipment creation: {str(shipment_error)}"
                
                log_id = update_shipment_log(log_id, log_data)
                
                # Reset carrier if exception occurred
                frappe.db.set_value("Shipment", frm.get("name"), {
                    "shipment_id": "",
                    "custom_carrier_partner": "",
                    "custom_carrier_partner_id": "",
                    "custom_carrier_partner_name": ""
                })
                # Reload the document
                frm = frappe.get_doc("Shipment", frm.get("name"))
            
            attempts.append(attempt)
            
            if success:
                break
        
        if success:
            # Final update to log for successful shipment
            log_data["order_creation_status"] = "Success"
            log_data["account_name"] = successful_carrier.get("account_code")
            log_data["allocated_carrier"] = successful_carrier.get("account_code")
            log_data["recommendation_message"] = f"Shipment created with carrier: {successful_carrier.get('account_code')}"
            # log_name = get_last_clickpost_log_for_carrier(rec.get("account_code"))
            # current_recommendation["clickpost_log"] = log_name
            log_id = update_shipment_log(log_id, log_data)
            
            if len(attempts) > 1 and attempts[0].get("carrier") != successful_carrier.get("account_code"):
                # Show message if we had to use an alternative carrier
                alt_errors = "".join([
                    f"<tr><td>{a.get('carrier')}</td><td>{a.get('error') or 'Unknown error'}</td></tr>"
                    for a in attempts if a.get("carrier") != successful_carrier.get("account_code")
                ])
                
                frappe.msgprint(
                    title="Used Alternative Carrier",
                    indicator="orange",
                    msg=f"""
                    <p>Shipment created with {successful_carrier.get('account_code')}, not your first preference:</p>
                    <table class="table table-bordered">
                        <thead><tr><th>Carrier</th><th>Error</th></tr></thead>
                        <tbody>{alt_errors}</tbody>
                    </table>
                    """
                )
                
                return {"success": True, "message": f"Shipment created with alternative carrier: {successful_carrier.get('account_code')}"}
            
            return {"success": True, "message": f"Shipment created with carrier: {successful_carrier.get('account_code')}"}
        
        else:
            # Clear shipment ID if no attempt was successful
            frappe.db.set_value("Shipment", frm.get("name"), {
                "shipment_id": "",
                "custom_carrier_partner": "",
                "custom_carrier_partner_id": "",
                "custom_carrier_partner_name": ""
            })
            
            # Create error message HTML
            error_html = "".join([
                f"<tr><td>{a.get('carrier') or 'N/A'}</td><td>{a.get('error') or 'No error message'}</td></tr>"
                for a in attempts
            ])
            
            # Final update to log for all failed attempts
            log_data["order_creation_status"] = "Error"
            log_data["recommendation_message"] = "All carrier attempts failed"
            log_data["recommendation_reference"] = recommendation_reference
            # log_name = get_last_clickpost_log_for_carrier(rec.get("account_code"))
            # current_recommendation["clickpost_log"] = log_name
            log_id = update_shipment_log(log_id, log_data)
            
            frappe.msgprint(
                title="Shipment Failed",
                indicator="red",
                msg=f"""
                <p>None of the carriers were successful.</p>
                <table class="table table-bordered">
                    <thead><tr><th>Carrier</th><th>Error</th></tr></thead>
                    <tbody>{error_html}</tbody>
                </table>
                """
            )
            
            return {"success": False, "message": "All carrier attempts failed"}
    
    else:
        # If custom_carrier_partner is already set, proceed with direct shipment creation
        shipment_data = prepare_shipment_payload(frm) or {}
        
        # Update log for direct shipment attempt
        carrier_info = frm.get("custom_carrier_partner_name") or ""
        log_data["recommendation_status"] = "False"
        log_data["recommendation_message"] = f"Using predefined carrier: {carrier_info}"
        
        log_data["account_name"] = carrier_info
        log_data["allocated_carrier"] = carrier_info
        log_id = update_shipment_log(log_id, log_data)
        
        try:
            # Call create_clickpost_shipment directly
            result = create_clickpost_shipment(shipment_data=json.dumps(shipment_data))

            
            
            if (result.get("status") == "success" and
                result.get("response", {}).get("meta", {}).get("success")):
                
                # Update shipment ID
                frappe.db.set_value("Shipment", frm.get("name"), {
                    "shipment_id": result.get("response", {}).get("meta", {}).get("b2b_shipment_id")
                })
                
                # Update log data for successful direct shipment
                log_data["order_creation_status"] = "Success"
                log_data["awb_number"] = result.get("response", {}).get("meta", {}).get("b2b_shipment_id") or ""
                log_data["recommendation_message"] = "ClickPost shipment created successfully"
                log_id = update_shipment_log(log_id, log_data)
                
                return {"success": True, "message": "ClickPost shipment created successfully"}
                
            else:
                # error_msg = (result.get("response", {}).get("meta", {}).get("error") or
                #             result.get("response", {}).get("meta", {}).get("message") or
                #             "Unknown error")
                
                # Update log data for failed direct shipment
                log_data["order_creation_status"] = "Error"
                log_data["recommendation_message"] = f"Shipment creation failed: {result}"
                log_id = update_shipment_log(log_id, log_data)
                
                frappe.msgprint(
                    title=_("Error"),
                    indicator="red",
                    msg=str(result.get('response'))
                )
                
                return {"success": False, "message": result}
                
        except Exception as e:
            frappe.log_error(f"Error creating ClickPost shipment: {str(e)}", "ClickPost Creation Error")
            
            # Update log data for exception in direct shipment
            log_data["order_creation_status"] = "Error"
            log_data["recommendation_message"] = f"Exception during shipment creation: {str(e)}"
            log_id = update_shipment_log(log_id, log_data)
            
            frappe.msgprint(
                title=_("Error"),
                indicator="red",
                msg=str(e)
            )
            
            return {"success": False, "message": str(e)}

def update_shipment_log(log_id, log_data):
    """
    Update an existing shipment log entry or create a new one if it doesn't exist.
    
    Args:
        log_id (str): The ID of the log entry to update, or None to create a new one
        log_data (dict): The log data
        
    Returns:
        str: The ID of the updated or created log entry
    """
    try:
        if log_id:
            # Try to get the existing log document
            try:
                log_doc = frappe.get_doc("Auto Shipment Creation Logs", log_id)
                
                # Update fields
                for key, value in log_data.items():
                    if hasattr(log_doc, key):
                        log_doc.set(key, value)
                
                # Update timestamp
                log_doc.shipment_creation_time = frappe.utils.now_datetime()
                
                # Save the document
                log_doc.save(ignore_permissions=True)
                frappe.db.commit()
                
                return log_id
            except frappe.DoesNotExistError:
                # If log doesn't exist anymore, create a new one
                return shipment_auto_log(log_data)
        else:
            # Create a new log entry
            return shipment_auto_log(log_data)
    except Exception as e:
        frappe.log_error(f"Error updating shipment log: {str(e)}", "Shipment Log Update Error")
        # If update fails, try to create a new log as fallback
        try:
            return shipment_auto_log(log_data)
        except:
            # If even creating a new log fails, just return None
            return None


