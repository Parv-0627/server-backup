from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
import frappe

def setup_custom_fields():
	custom_fields = {
		"Stock Entry": [
			dict(fieldname='production_planning_record',
				label='Production Planning Record',
				fieldtype='Link',
				options='Production Planning Record',
				insert_after='stock_entry_type',
				read_only=True
			),
		],
		"Item": [
			dict(fieldname='part_warehouse',
				label='Part Warehouse',
				fieldtype='Link',
				options='Warehouse',
				insert_after='stock_uom'
			),
			dict(fieldname='short_code',
				label='Short Code',
				fieldtype='Data',
				insert_after='stock_uom'
			)
		],
		"Material Request": [
			dict(fieldname='production_stock_planning',
				label='Production Stock Planning',
				fieldtype='Link',
				options='Production Stock Planning',
				insert_after='material_request_type',
				read_only=True
			),
		],
		"Material Request Item": [
			dict(fieldname='parts_for',
				label='Parts For',
				fieldtype='Link',
				options='Item',
				insert_after='item_name',
				# read_only=True
			),
		],
		"Item Group": [
			dict(fieldname='item_group_percentage',
				label='Item Group Percentage',
				fieldtype='Table',
				options='Item Group Percentage',
				insert_after='item_group_defaults',
				# read_only=True
			),
		],
		"Customer": [
			dict(fieldname='retailer_code',
				label='Retailer Code',
				fieldtype='Data',
				insert_after='customer_group'
			),
			dict(fieldname='distributor_code',
				label='Distributor Code',
				fieldtype='Data',
				insert_after='retailer_code'
			)
		],
		"Serial No": [
			dict(fieldname='retailer_code',
				label='Retailer Code',
				fieldtype='Data',
				insert_after='company'
			),
			dict(fieldname='distributor_code',
				label='Distributor Code',
				fieldtype='Data',
				insert_after='work_order'
			),
			dict(fieldname='sr_status',
				label='SR Status',
				fieldtype='Check',
				insert_after='retailer_code'
			)
		],
		"Purchase Receipt": [
			dict(fieldname='rejected_serial_no',
				label='Rejected Serial No',
				fieldtype='Text',
				insert_after='rejected_warehouse'
			)
		]
	}
	try:
		create_custom_fields(custom_fields)
		frappe.db.commit()
	except:
		print("Exception while createing customfield")