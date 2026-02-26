# Copyright (c) 2025, Controlz Customizations and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = [
        {"label": "Stock Entry", "fieldname": "stock_entry", "fieldtype": "Link", "options": "Stock Entry", "width": 300},
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 350},
		{"label": "Serial No", "fieldname": "serial_no", "fieldtype": "Link", "options": "Serial No","width": 180},
        {"label": "FG Item", "fieldname": "fg_item", "fieldtype": "Link", "options": "Item", "width": 300},
        {"label": "FG Value", "fieldname": "fg_value", "fieldtype": "Float", "width": 180},
        {"label": "Part Value", "fieldname": "part_value", "fieldtype": "Float", "width": 180},
        {"label": "Scrap Value", "fieldname": "scrap_value", "fieldtype": "Float", "width": 300},
        
    ]
	data = get_data(filters)
	return columns, data

def get_data(filters):
	pass
