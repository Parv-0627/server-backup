# Copyright (c) 2025, Controlz Customizations and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = [
        {"label": "Stock Entry", "fieldname": "stock_entry", "fieldtype": "Link", "options": "Stock Entry", "width": 300},
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 350},
		{"label": "FG Serial No", "fieldname": "fg_serial_no", "fieldtype": "Link", "options": "Serial No","width": 180},
		{"label": "FG Item", "fieldname": "fg_item", "fieldtype": "Link", "options": "Item", "width": 300},
		{"label": "Part Serial No", "fieldname": "serial_no", "fieldtype": "Link", "options": "Serial No","width": 180},
        {"label": "Part Item", "fieldname": "part_item", "fieldtype": "Link", "options": "Item", "width": 300},
        {"label": "Cost", "fieldname": "fg_value", "fieldtype": "Float", "width": 180},
        {"label": "Part Value", "fieldname": "part_value", "fieldtype": "Float", "width": 180},
        {"label": "Scrap Value", "fieldname": "scrap_value", "fieldtype": "Float", "width": 300},
        
    ]
	data = get_data(filters)
	return columns, data

def get_data(filters):
	app_filters = [
		["docstatus","=",  1],
		["stock_entry_type","=", "Manufacture"],
	]
	if filters.get("from_date"):
		app_filters.append(["posting_date", ">=", filters["from_date"]])
	if filters.get("to_date"):
		app_filters.append(["posting_date","<=", filters["to_date"]])
	data = frappe.get_all("Stock Entry",app_filters)
	final_output = []
	for row in data:
		stock_entry = frappe.get_doc("Stock Entry", row["name"])
		part_value = 0.0
		fg_item = ""
		fg_value = 0.0
		scrap_value = 0.0
		serial_no = ""
		raw_data = []
		for item in stock_entry.items:
			if item.idx == 1:
				serial_no = item.serial_no
				raw_data.append({
					"r_itemcode": item.item_code,
					"r_serial_no": item.serial_no,
					"r_value": item.basic_rate ,
				})
			elif item.is_finished_item:
				fg_item = item.item_code
				fg_value = item.basic_rate
			elif item.is_scrap_item:
				scrap_value = item.basic_rate
			else:
				part_value += item.basic_rate
				raw_data.append({
					"r_itemcode": item.item_code,
					"r_serial_no": item.serial_no,
					"r_value": item.basic_rate,
				})


		final_output.append({
			"stock_entry": stock_entry.name,
			"posting_date": stock_entry.posting_date,
			"fg_item": fg_item,
			"fg_value": fg_value,
			"part_value": part_value,
			"scrap_value": scrap_value,
			"fg_serial_no": serial_no,
			"indent":0
		})
		for temp2 in raw_data:
			final_output.append({
				"part_item": temp2.get("r_itemcode"),
				"serial_no": temp2.get("r_serial_no"),
				"fg_value": temp2.get("r_value"),
				"indent": 1
			})

	return final_output

def get_purchase_value(item_code, serial_no):
	valuation_rate = frappe.db.sql(''' 
	select 
		purchase_recept_item.rate 
	from 
		`tabPurchase Receipt Item` as purchase_recept_item
	where
		purchase_recept_item.item_code = %(item_code)s
		and purchase_recept_item.serial_no = %(serial_no)s
            ''',{ "serial_no":serial_no, "item_code": item_code })
	if valuation_rate and valuation_rate[0]:
		valuation_rate = valuation_rate[0][0]
	else:
		valuation_rate = 0