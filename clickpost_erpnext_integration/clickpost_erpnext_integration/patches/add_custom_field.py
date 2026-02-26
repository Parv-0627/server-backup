import frappe

def execute():
    add_custom_field()

def add_custom_field():
    doctype = "Journal Entry Account"
    fieldname = "custom_party_name"
    try:
        if not frappe.db.exists("Custom Field", {"fieldname": fieldname, "dt": doctype}):
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = doctype
            custom_field.fieldname = fieldname
            custom_field.label = "Party Name"
            custom_field.fieldtype = "Data"
            custom_field.allow_on_submit = 1
            custom_field.insert_after = "Party"
            custom_field.insert()
            frappe.db.commit()
            print(f"Custom field '{fieldname}' added successfully to {doctype}")
        else:
            print(f"Custom field '{fieldname}' already exists in {doctype}")
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error adding custom field '{fieldname}': {str(e)}", "Add Custom Field")
        print(f"Error occurred while adding custom field: {str(e)}")