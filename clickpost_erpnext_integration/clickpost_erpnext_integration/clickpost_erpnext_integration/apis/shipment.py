import frappe
from frappe import _
from .base import ClickpostBase
import json

class ClickpostShipment(ClickpostBase):
    BASE_PATH = "api/v1/create-b2b-order/"

    def create_shipment(self, shipment_data):
        """
        Create new shipment in Clickpost
        
        Args:
            shipment_data (dict): Shipment details with Clickpost required structure
        """
        params = {
            "key": self.api_key,
            "username": self.username
        }
        return self.post("", params=params, json=shipment_data)

    def fetch_recommendation(self, payload):
        self.BASE_PATH = "/api/v1/recommendation_api/"
        params = {
            "key": self.api_key
        }
        return self.post("", params=params, json=payload)
    
    def create_awb(self, shipment_data):
        self.BASE_PATH = "/api/v1/b2b-awb-register/"
        """
        Create new shipment in Clickpost
        
        Args:
            shipment_data (dict): Shipment details with Clickpost required structure
        """
        params = {
            "key": self.api_key,
        }
        return self.post("", params=params, json=shipment_data)
    
    def sync_shipment(self, reference_number, courier_partner, account_code):
        """
        Sync shipment in Clickpost
        
        Args:
            reference_number (str): Reference number of the shipment
            courier_partner (str): Courier partner name
            account_code (str): Account code
        """
        params = {
            "key": self.api_key,
            "username": self.username,
            "reference_number": reference_number,
            "courier_partner": courier_partner,
            "account_code": account_code
        }
        return self.get("", params=params)
    
    
    def track_shipment(self, waybill, cp_id):
        """
        Track shipment by waybill number
        
        Args:
            waybill (str): Waybill number to track
        """
        
        self.BASE_PATH = "/api/v2/track-order/"
        params = {
            "key": self.api_key,
            "username": self.username,
            "waybill": waybill,
            "cp_id": cp_id,
        }
        return self.get("", params=params)
       
    
    def cancel_shipment(self, waybill, cp_id, account_code):
        """
        Cancel shipment by waybill number
        
        Args:
            waybill (str): Waybill number to cancel
        """
        self.BASE_PATH = "api/v1/cancel-order/"
        params = {
            "key": self.api_key,
            "username": self.username,
            "waybill": waybill,
            "cp_id": cp_id,
            "account_code": account_code
        }
        return self.get("", params=params)

    def cancel_awb(self, waybill, cp_id, account_code, manual_update_status):
        """
        Cancel shipment by waybill number
        
        Args:
            waybill (str): Waybill number to cancel
        """
        self.BASE_PATH = "api/v1/cancel-order/"
        params = {
            "key": self.api_key,
            "username": self.username,
            "waybill": waybill,
            "cp_id": cp_id,
            "account_code": account_code,
            "manual_update_status": manual_update_status
        }
        return self.get("", params=params)

    def proof_of_delivery(self, waybill, cp_id):
        self.BASE_PATH = "api/v1/pod/pod_from_shipment_details/"
        params = {
            "key": self.api_key,
            "waybill": waybill,
            "cp_id": cp_id,
        }
        return self.get("", params=params)

    def get_appointment(self, awb_number, account_code, courier_partner_id):
        self.BASE_PATH = "api/v1/appointment-details/"
        params = {
            "key": self.api_key,
            "username": self.username,
            "awb_number": awb_number,
            "account_code": account_code,
            "courier_partner_id": courier_partner_id
        }
        return self.get("", params=params)

@frappe.whitelist()
def create_clickpost_shipment(shipment_data):
    clickpost = ClickpostShipment()
    try:
        # Ensure shipment_data is a dictionary
        if isinstance(shipment_data, str):
            shipment_data = json.loads(shipment_data)  # Convert from string if needed

        response = clickpost.create_shipment(shipment_data)

        return {
            "status": "success" if response else "failed",
            "response": response
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": str(e).replace(clickpost.api_key, "****")
        }

@frappe.whitelist()
def fetch_recommendation(payload):
    clickpost = ClickpostShipment()
    try:
        # Ensure payload is a dictionary
        if isinstance(payload, str):
            payload = json.loads(payload)  # Convert from string if needed

        response = clickpost.fetch_recommendation(payload)

        return {
            "status": "success" if response else "failed",
            "response": response
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": str(e).replace(clickpost.api_key, "****")
        }

@frappe.whitelist()
def create_clickpost_awb_order(shipment_data):
    clickpost = ClickpostShipment()
    try:
        # Ensure shipment_data is a dictionary
        if isinstance(shipment_data, str):
            shipment_data = json.loads(shipment_data)  # Convert from string if needed

        response = clickpost.create_awb(shipment_data)

        return {
            "status": "success" if response else "failed",
            "response": response
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": str(e).replace(clickpost.api_key, "****")
        }
    
@frappe.whitelist()
def sync_shipment(reference_number, courier_partner, account_code):
    clickpost = ClickpostShipment()
    try:
        # Ensure shipment_data is a dictionary
         # Convert from string if needed

        response = clickpost.sync_shipment(reference_number, courier_partner, account_code)

        return {
            "status": "success" if response else "failed",
            "response": response
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": str(e).replace(clickpost.api_key, "****")
        }

@frappe.whitelist()
def track_shipment(waybill, cp_id):
    clickpost = ClickpostShipment()
    try:
        response = clickpost.track_shipment(waybill, cp_id)

        return {
            "status": "success" if response else "failed",
            "response": response
        }
    except Exception as e:
        frappe.log_error(message=str(e).replace(clickpost.api_key, "****"), title="ClickPost Shipment Tracking Failed")
        return {
            "status": "failed",
            "message": str(e).replace(clickpost.api_key, "****")
        }

@frappe.whitelist()
def get_appointment(awb_number, account_code, courier_partner_id):
    clickpost = ClickpostShipment()
    try:
        response = clickpost.get_appointment(awb_number, account_code, courier_partner_id)

        return {
            "status": "success" if response else "failed",
            "response": response
        }
    except Exception as e:
        frappe.log_error(message=str(e).replace(clickpost.api_key, "****"), title="ClickPost Shipment Tracking Failed")
        return {
            "status": "failed",
            "message": str(e).replace(clickpost.api_key, "****")
        }

    
@frappe.whitelist()
def cancel_clickpost_shipment(waybill, cp_id, account_code):
    clickpost = ClickpostShipment()
    try:
        response = clickpost.cancel_shipment(waybill, cp_id, account_code)

        return {
            "status": "success" if response else "failed",
            "response": response
        }
    except Exception as e:
        frappe.log_error(message=str(e).replace(clickpost.api_key, "****"), title="ClickPost Shipment Cancellation Failed")
        return {
            "status": "failed",
            "message": str(e).replace(clickpost.api_key, "****")
        }

@frappe.whitelist()
def cancel_clickpost_awb(waybill, cp_id, account_code, manual_update_status):
    clickpost = ClickpostShipment()
    try:
        response = clickpost.cancel_awb(waybill, cp_id, account_code, manual_update_status)

        return {
            "status": "success" if response else "failed",
            "response": response
        }
    except Exception as e:
        frappe.log_error(message=str(e).replace(clickpost.api_key, "****"), title="ClickPost AWB Cancellation Failed")
        return {
            "status": "failed",
            "message": str(e).replace(clickpost.api_key, "****")
        }

@frappe.whitelist()
def get_proof_of_delivery(waybill, cp_id):
    clickpost = ClickpostShipment()
    try:
        # Ensure shipment_data is a dictionary
         # Convert from string if needed

        response = clickpost.proof_of_delivery(waybill, cp_id)

        return {
            "status": "success" if response else "failed",
            "response": response
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": str(e).replace(clickpost.api_key, "****")
        }