# Copyright (c) 2025, Controlz Customizations and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = [
        {"label": "Work Oder", "fieldname": "workorder", "fieldtype": "Link", "options": "Work Order", "width": 300},
        {"label": "Item To Manufacture", "fieldname": "production_item", "fieldtype": "Link", "options": "Item", "width": 300},
        {"label": "Workstation", "fieldname": "workstation", "fieldtype": "Data", "width": 180},
        {"label": "Arrival Time", "fieldname": "arrival_time", "fieldtype": "Datetime", "width": 180},
        {"label": "Serial No", "fieldname": "serial_no", "fieldtype": "Data", "width": 300},
        {"label": "idx", "fieldname": "idx", "fieldtype": "Data", "width": 300},
        
    ]
	data = get_data(filters)
	return columns, data

def get_data(filters):
	final_data = frappe.db.sql("""
		SELECT 
			wo.name AS workorder,
			wo.production_item,
			wim1.workstation,
			wim1.arrival_time,
			wim1.serial_no,
			wim1.idx
		FROM 
			`tabWork Order` wo
		JOIN (
			SELECT 
				wim.parent,
				wim.workstation,
				wim.arrival_time,
				wim.serial_no,
				wim.idx
			FROM `tabWorkstation Item Movement` wim
			JOIN (
				SELECT 
					parent,
					workstation,
					MIN(idx) AS min_idx
				FROM `tabWorkstation Item Movement`
				GROUP BY parent, workstation
			) AS min_wim
			ON wim.parent = min_wim.parent AND wim.workstation = min_wim.workstation AND wim.idx = min_wim.min_idx
		) AS wim1
		ON wo.name = wim1.parent
		WHERE 
			wo.docstatus = 1
			AND wo.creation >= %(from_date)s
			AND wo.creation <= %(to_date)s
		ORDER BY wo.creation DESC;
	""", {
		"from_date": filters.get("from_date"),
		"to_date": filters.get("to_date")
	}, as_dict=True)

	return final_data
