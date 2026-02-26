import frappe
from frappe import _
from .base import ClickpostBase
import json

class ClickpostLocation(ClickpostBase):
    BASE_PATH = "api/v1/dashboard/locationmaster/locations/"

    def create_location(self, location_data):
        """
        Create new location in Clickpost
        
        Args:
            location_data (dict): Location details with following structure:
                pickup (bool): True/False to mark pickup
                drop (bool): True/False to mark Drop
                code (str): Code, max 100 chars
                organization_name (str): Org Name, Max 100 chars
                name (str): Name for the Location, Max 100 char
                pincode (str): Pincode, 6 chars
                city (str): City, max 100
                state (str): State, max 100
                address (str): Address, max 500 char
                poc_name (str, optional): Poc Name, max 100 char
                phone_number (str): Phone Number
                email (str): Email
                lat (float, optional): Latitude
                long (float, optional): Longitude
                gstin (str, optional): GSTIN
                tag (str, optional): Custom Tag, max 100 char
                drop_type (str, optional): Drop Type, max 100 char STORE WAREHOUSE
                floor_number (int, optional): Floor Number, max 100 char
                max_allowed_tat (int, optional): Max Allowed TAT, max 100 char
                transport_mode (str, optional): allowed values SURFACE AIR EXPRESS_SURFACE HEAVY_SURFACE
        """
        return self.post("", json=location_data)
    
    def get_location(self, code):
        """
        Fetch location details from ClickPost using location code.
        """
        return self.get("", params={"key": self.api_key, "code": code})
    
    def delete_location(self, code):
        """
        Fetch location details from ClickPost using location code.
        """
        return self.delete("", params={"key": self.api_key, "code": code})
    
    def update_location(self, location_data):
        """
        Fetch location details from ClickPost using location code.
        """
        return self.put("", json=location_data)

@frappe.whitelist()
def create_clickpost_location(location_data):
    clickpost = ClickpostLocation()
    try:

        # Ensure location_data is a dictionary
        if isinstance(location_data, str):
            location_data = json.loads(location_data)  # Convert from string if needed

        response = clickpost.create_location(location_data)

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
def get_clickpost_location(code):
    clickpost = ClickpostLocation()
    try:
        response = clickpost.get_location(code)

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
def delete_clickpost_location(code):
    clickpost = ClickpostLocation()
    try:
        response = clickpost.delete_location(code)

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
def update_clickpost_location(location_data):
    clickpost = ClickpostLocation()
    try:
        # Ensure location_data is a dictionary
        if isinstance(location_data, str):
            location_data = json.loads(location_data)  # Convert from string if needed

        response = clickpost.update_location(location_data)

        return {
            "status": "success" if response else "failed",
            "response": response
        }
    except Exception as e:
        
        return {
            "status": "failed",
            "message": str(e).replace(clickpost.api_key, "****")
        }

    
