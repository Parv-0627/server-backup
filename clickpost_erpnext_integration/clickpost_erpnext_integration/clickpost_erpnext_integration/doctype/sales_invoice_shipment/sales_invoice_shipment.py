# Copyright (c) 2025, nasirucode and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SalesInvoiceShipment(Document):
	def validate(self):
        # Check if ewaybill_no is empty
		if not self.e_waybill_number:
            # Set ewaybill_expiry_date to None
			self.e_waybill_expiry_date = None
