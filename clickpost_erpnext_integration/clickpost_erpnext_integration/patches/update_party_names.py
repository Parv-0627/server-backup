import frappe

def execute():
    update_party_names_in_journal_entries()

def update_party_names_in_journal_entries():

    try:
        journal_entries = frappe.db.sql("""
            SELECT je.name, jea.party_type, jea.party
            FROM `tabJournal Entry` je
            INNER JOIN `tabJournal Entry Account` jea ON je.name = jea.parent
            WHERE jea.party_type IN ('Customer', 'Supplier')
            AND je.docstatus = 1
        """, as_dict=1)

        update_count = 0

        for entry in journal_entries:
            if entry.party_type == "Customer":
                update_field = "customer_name"
            elif entry.party_type == "Supplier":
                update_field = "supplier_name"

            update_data = frappe.db.get_value(entry.party_type, entry.party, update_field)
            if update_data:
                frappe.db.set_value("Journal Entry Account", {"parent": entry.name,"party_type":entry.party_type,"party":entry.party}, "custom_party_name", update_data)
                update_count += 1

        frappe.db.commit()
        print(f"Total records updated: {update_count}")

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error updating custom party names in journal entries: {str(e)}", "Update Custom Party Names")
        print(f"Error updating custom party names in journal entries: {str(e)}")
