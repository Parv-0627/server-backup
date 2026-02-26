import frappe
import json
from frappe import _
from frappe.utils import get_request_session
from frappe.utils import get_datetime

@frappe.whitelist(allow_guest=True)
def handle_clickpost_webhook():
    """
    Handle incoming webhook from ClickPost for shipment tracking updates
    
    Expected payload structure:
    {
        "additional": {
            "latest_status": {
                "remark": "AWAITED",
                "status": "AWAITED",
                "location": "Pushpak_Nagar",
                "clickpost_status_code": 40,
                "clickpost_status_description": "RiderAllocationAwaited",
                "clickpost_status_bucket": 1,
                "clickpost_status_bucket_description": "Order placed",
                "reference_number": "WERA-9616974",
                "timestamp": "2024-11-19T10:04:20Z"
            },
            "is_rvp": false,
            "carrier_partner_edd": null,
            "order_id": "TESTORDERHLD123"
        },
        "remark": "AWAITED",
        "status": "AWAITED",
        "location": "Pushpak_Nagar",
        "clickpost_status_code": 40,
        "clickpost_status_description": "RiderAllocationAwaited",
        "timestamp": "2024-11-19T10:04:20Z",
        "cp_id": 10001,
        "waybill": "TEST-AWB-HLD-123"
    }
    """
    try:
        # Get the webhook data
        data = frappe.request.data
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        
        webhook_data = json.loads(data)
        frappe.logger().debug(f"ClickPost Webhook Received: {webhook_data}")
        
        # Extract key information
        waybill = webhook_data.get("waybill")
        reference_number = webhook_data.get("additional", {}).get("latest_status", {}).get("reference_number")
        order_id = webhook_data.get("additional", {}).get("order_id")
        
        # Find the shipment based on waybill or reference number
        shipment = None
        awb_registration = None
        
        if waybill:
            shipments = frappe.get_all(
                "Shipment", 
                filters={"awb_number": waybill, "docstatus": 1},
                fields=["name"]
            )
            if shipments:
                shipment = shipments[0].name
        
        if not shipment and reference_number:
            # Try to find by reference number (which could be the shipment name)
            shipments = frappe.get_all(
                "Shipment", 
                filters={"name": reference_number, "docstatus": 1},
                fields=["name"]
            )
            if shipments:
                shipment = shipments[0].name

        if waybill:
            awb_registrations = frappe.get_all(
                "AWB Registration",
                filters={"awb_number": waybill, "docstatus": 1},
                fields=["name"]
            )
            if awb_registrations:
                awb_registration = awb_registrations[0].name
        
        
        if not shipment and not awb_registration:
            frappe.logger().error(f"ClickPost Webhook: No matching shipment or AWB registration found for waybill {waybill} or reference {reference_number}")
            return {"success": False, "message": "No matching shipment or AWB registration found"}
        
        # Prepare tracking data in the format expected by update_shipment_tracking
        tracking_data = {
            "latest_status": {
                "timestamp": get_datetime(webhook_data.get("timestamp")).strftime("%Y-%m-%d %H:%M:%S"),
                "location": webhook_data.get("location"),
                "remark": webhook_data.get("remark"),
                "status": webhook_data.get("status"),
                "clickpost_status_code": webhook_data.get("clickpost_status_code"),
                "clickpost_status_description": webhook_data.get("clickpost_status_description"),
                # "clickpost_status_bucket": webhook_data.get("additional", {}).get("latest_status", {}).get("clickpost_status_bucket", 0),
                # "clickpost_status_bucket_description": webhook_data.get("additional", {}).get("latest_status", {}).get("clickpost_status_bucket_description", ""),
                "created_at": get_datetime(webhook_data.get("timestamp")).strftime("%Y-%m-%d %H:%M:%S")  # Using timestamp as created_at if not provided
            }
        }
        
        # Add scans if available
        # if "scans" in webhook_data:
        #     tracking_data["scans"] = webhook_data["scans"]
        # else:
        #     # Create a scan entry from the current status
        #     tracking_data["scans"] = [{
        #         "timestamp": webhook_data.get("timestamp"),
        #         "location": webhook_data.get("location"),
        #         "remark": webhook_data.get("remark"),
        #         "status": webhook_data.get("status"),
        #         "clickpost_status_code": webhook_data.get("clickpost_status_code"),
        #         "clickpost_status_description": webhook_data.get("clickpost_status_description"),
        #         "clickpost_status_bucket": webhook_data.get("additional", {}).get("latest_status", {}).get("clickpost_status_bucket", 0),
        #         "clickpost_status_bucket_description": webhook_data.get("additional", {}).get("latest_status", {}).get("clickpost_status_bucket_description", ""),
        #         "created_at": webhook_data.get("timestamp"),
        #         "tracking_id": webhook_data.get("waybill")
        #     }]
        
        # Update the shipment tracking
        # Update Shipment if found
        if shipment:
            result = frappe.call(
                "clickpost_erpnext_integration.clickpost_erpnext_integration.utils.update_shipment_tracking",
                shipment_name=shipment,
                tracking_data=tracking_data
            )
            if result and result.get("success"):
                frappe.logger().info(f"ClickPost Webhook: Successfully updated tracking for Shipment {shipment}")
            else:
                error_message = result.get("error", "Unknown error")
                frappe.logger().error(f"ClickPost Webhook: Failed to update tracking for Shipment {shipment}: {error_message}")
        
        # Update AWB Registration if found
        if awb_registration:
            result = frappe.call(
                "clickpost_erpnext_integration.clickpost_erpnext_integration.utils.update_awb_tracking",
                shipment_name=awb_registration,
                tracking_data=tracking_data
            )
            if result and result.get("success"):
                frappe.logger().info(f"ClickPost Webhook: Successfully updated tracking for AWB Registration {awb_registration}")
            else:
                error_message = result.get("error", "Unknown error")
                frappe.logger().error(f"ClickPost Webhook: Failed to update tracking for AWB Registration {awb_registration}: {error_message}")
        
        return {"success": True, "message": "Tracking updated for Shipment and/or AWB Registration"}

    except Exception as e:
        frappe.logger().error(f"ClickPost Webhook Error: {str(e)}\n{frappe.get_traceback()}")
        return {"success": False, "message": str(e)}
