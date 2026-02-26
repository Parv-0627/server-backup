# Copyright (c) 2025, nasirucode and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document


class AWBRegistration(Document):
    def on_submit(self):
        if self.status == "Draft":
            self.status = "Submitted"
    def validate(self):
        if self.carrier_partner_id and self.carrier_account_name:
            self.carrier_partner = f"{self.carrier_partner_id}-{self.carrier_account_name}"
            # Check if the AWB number already exists
        if self.get("sales_invoice"):
            for shipment in self.sales_invoice:
                # Clear ewaybill_expiry_date if ewaybill_no is not set
                if not shipment.get("e_waybill_number"):
                    shipment.e_waybill_expiry_date = None

    def on_cancel(self):
        if hasattr(doc, 'carrier_partner_id') and hasattr(doc, 'carrier_account_name') and hasattr(doc, 'awb_number'):
            try:
                config = frappe.get_single("Clickpost Configuration")
                # Call the ClickPost API to cancel the AWB
                manual_update_status = config.manual_update_status == 1            
                response = frappe.call(
                    "clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment.cancel_clickpost_awb",
                    cp_id=doc.carrier_partner_id,
                    account_code=doc.carrier_account_name,
                    waybill=doc.awb_number,
                    manual_update_status=manual_update_status
                )
                
                # Convert the response to JSON
                response_json = json.loads(response) if isinstance(response, str) else response

                # Process the response
                if response_json:
                    success = response_json.get("response", {}).get("meta", {}).get("success")

                    if success:
                        # Update the AWB Registration status
                        frappe.db.set_value("AWB Registration", doc.name, "clickpost_status", "Cancelled")

                        success_message = response_json.get("response", {}).get("meta", {}).get("message", "AWB cancelled successfully")
                        frappe.msgprint(
                            msg=success_message,
                            title="Success",
                            indicator="green"
                        )
                    else:
                        error_message = response_json.get("response", {}).get("meta", {}).get("message", "Failed to cancel AWB")
                        frappe.throw(f"AWB cancelation not initiated as AWB is not created")
                else:
                    frappe.throw("Invalid response from ClickPost API.")
            except Exception as e:
                frappe.log_error("ClickPost AWB Cancellation", f"Error cancelling ClickPost AWB: {str(e)}")
                frappe.msgprint(
                    msg=f"Error cancelling ClickPost AWB: {str(e)}",
                    title="Error",
                    indicator="red"
                )
        else:
            frappe.throw("Missing required fields for AWB cancellation.")

    