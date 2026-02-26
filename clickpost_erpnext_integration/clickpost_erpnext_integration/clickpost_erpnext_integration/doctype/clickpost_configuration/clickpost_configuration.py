# Copyright (c) 2025, nasirucode and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from clickpost_erpnext_integration.clickpost_erpnext_integration.apis.connection import test_clickpost_connection


class ClickpostConfiguration(Document):
	# pass
	def before_save(self):
		"""
		Validate the Clickpost Configuration.
		"""
		if self.enable:
			response = test_clickpost_connection()
			if response.get("status") == "success":
				frappe.msgprint(
					msg="Clickpost connection is successfully authorized",
					title="Success",
					indicator="green",
				)
			else:
				frappe.throw("Clickpost connection is not authorized, please check your credentials.")
				# self.enable = 0
		else:
			frappe.msgprint(
				msg="Clickpost Configuration is disabled",
				title="Disabled",
				indicator="orange",
			)
