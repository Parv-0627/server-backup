from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
import frappe

def setup_custom_fields():
	custom_fields = {
		"Issue": [
			dict(fieldname="serial_number_cu",
				label="Serial Number",
				fieldtype="Data",
				insert_after="subject"
			),
			dict(fieldname="customer_name_cu",
				label="Customer Name",
				fieldtype="Data",
				insert_after="serial_number_cu"
			),
		],
		"Customer": [
			dict(fieldname="cu_mobile_number",
				label="Mobile Number",
				fieldtype="Data",
				insert_after="customer_group"
			),
			dict(fieldname="cu_email",
				label="Email",
				fieldtype="Data",
				insert_after="cu_mobile_number"
			),
		],
		"Sales Order": [
			dict(fieldname="so_status",
				label="Sales Order Status",
				fieldtype="Select",
				options="Pending\nApproved\nCancelled\nProcessing\nShipped",
				allow_on_submit=True,
				insert_after="delivery_date"
			),
			dict(fieldname="so_address",
				label="Shipping Address",
				fieldtype="Small Text",
				allow_on_submit=True,
				insert_after="so_status"
			),
			dict(fieldname="payment_type_un",
				label="Payment Type",
				fieldtype="Data",
				allow_on_submit=True,
				insert_after="so_address"
			),
			dict(fieldname="payment_amount_un",
				label="Payment Amount",
				fieldtype="Data",
				allow_on_submit=True,
				insert_after="payment_type_un"
			),
			dict(fieldname="paymentmethod",
				label="Payment Method",
				fieldtype="Data",
				allow_on_submit=True,
				insert_after="payment_amount_un"
			),
			dict(fieldname="payment_status",
				label="Payment Status",
				fieldtype="Data",
				allow_on_submit=True,
				insert_after="paymentmethod"
			),
			dict(fieldname="offer_code",
				label="Offer Code",
				fieldtype="Data",
				allow_on_submit=True,
				insert_after="payment_status"
			),
			dict(fieldname="offer_discount",
				label="Offer Discount",
				fieldtype="Data",
				allow_on_submit=True,
				insert_after="offer_code"
			),
			dict(fieldname="order_source",
				label="Order Source",
				fieldtype="Select",
				options="\nB2B\nB2C",
				insert_after="naming_series",
				read_only=1
			),
		],
		"Sales Order Item": [
			dict(fieldname="is_addons",
				label="Is Addons",
				fieldtype="Check",
				insert_after="item_code"
			),
			dict(fieldname="addons_for",
				label="Addons For",
				fieldtype="Data",
				insert_after="is_addons"
			),
		]
	}
	try:
		create_custom_fields(custom_fields)
		frappe.db.commit()
	except Exception as e:
		print(f"Exception while creating custom fields: {e}")
	
	# Setup naming series for B2B/B2C
	setup_naming_series()


def setup_naming_series():
	"""Add B2B and B2C naming series options for Sales Order"""
	try:
		# Get current naming series options
		meta = frappe.get_meta("Sales Order")
		naming_field = meta.get_field("naming_series")
		current_options = naming_field.options or ""
		
		# Define new series to add
		new_series = ["SO-B2B-.YYYY.-", "SO-B2C-.YYYY.-"]
		
		# Parse current options
		options_list = [opt.strip() for opt in current_options.split("\n") if opt.strip()]
		
		# Add new series if not already present
		for series in new_series:
			if series not in options_list:
				options_list.append(series)
		
		# Update the options via Property Setter
		new_options = "\n".join(options_list)
		
		# Check if property setter exists
		existing = frappe.db.exists("Property Setter", {
			"doc_type": "Sales Order",
			"field_name": "naming_series",
			"property": "options"
		})
		
		if existing:
			frappe.db.set_value("Property Setter", existing, "value", new_options)
		else:
			frappe.get_doc({
				"doctype": "Property Setter",
				"doctype_or_field": "DocField",
				"doc_type": "Sales Order",
				"field_name": "naming_series",
				"property": "options",
				"property_type": "Text",
				"value": new_options
			}).insert(ignore_permissions=True)
		
		frappe.db.commit()
		print("Naming series updated successfully")
	except Exception as e:
		print(f"Exception while setting up naming series: {e}")
