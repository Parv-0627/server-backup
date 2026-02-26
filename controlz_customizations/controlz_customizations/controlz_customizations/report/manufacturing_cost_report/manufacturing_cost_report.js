// Copyright (c) 2025, Controlz Customizations and contributors
// For license information, please see license.txt

frappe.query_reports["Manufacturing Cost Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": "From",
			"fieldtype": "Date",
			"requeired": 1,
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			"fieldname": "to_date",
			"label": "To",
			"fieldtype": "Date",
			"requeired": 1,
			"default": frappe.datetime.get_today()
		}
	]
};
