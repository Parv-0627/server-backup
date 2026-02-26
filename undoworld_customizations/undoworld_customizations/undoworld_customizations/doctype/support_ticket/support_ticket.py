# Copyright (c) 2024, Frappe Customizations and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, now
from frappe.desk.form import assign_to

class SupportTicket(Document):
    def validate(self):
        self.update_serial_number()
        if self.serial_number:
            dn = self.get_dn(self.serial_number)
            if dn:
                self.customer = frappe.db.get_value("Delivery Note", dn, "customer")
        self.update_history()
        self.assigned_user()
    
    def assigned_user(self):
        for row in self.repairing_planning:
            if row.user_doc:
                filters = {
                    "reference_type": self.doctype,
                    "reference_name": self.name,
                    "status": "Open",
                    "allocated_to": row.user_doc,
                }
                if not frappe.get_all("ToDo", filters=filters):
                    assign_to.add(
                        {
                            "assign_to": [row.user_doc],
                            "doctype": self.doctype,
                            "name": self.name,
                            "description": "Close this task",
                        }
                    )

    
    def update_serial_number(self):
        if self.imei:
            srn = self.get_srn()
            if srn:
                self.serial_number = srn
    
    def get_srn(self):
        args = {
            "custom_imei1": "%s" % self.imei,
            "custom_imei2": "%s" % self.imei,
        }

        parent = frappe.db.sql(
            """
            select srn.name
            from
                `tabSerial No` as srn
            where
                srn.custom_imei1 = %(custom_imei1)s
                or 
                srn.custom_imei2 = %(custom_imei2)s
            order by srn.creation DESC
            """,
            args,
        )
        print("Helllooo")
        try:
            return parent[0][0]
        except:
            return None

    
    def get_dn(self, srn):
        args = {
            "serial_no": "%%%s%%" % srn,
        }

        parent = frappe.db.sql(
            """
            select dni.parent
            from
                `tabDelivery Note Item` dni,
                `tabDelivery Note` as dn
            where
                dn.name = dni.parent and
                dni.docstatus <> "2" and 
                dni.serial_no like %(serial_no)s
            order by dn.posting_date DESC
            """,
            args,
        )
        print("Helllooo")
        try:
            return parent[0][0]
        except:
            return None
    def update_history(self):
        if self.has_value_changed("status"):
            if not self.has_value_changed("status_reason"):
                self.status_reason = ""
            self.append("status_tracking", {
                "status": self.status,
                "posting_date": now(),
                "remark": self.status_reason
            })
    def get_history(self):
        data = []
        for row in self.status_tracking:
            data.append({
                "status": row.status,
                "posting_date": row.posting_date,
                "posting_time": row.posting_time,
                "remark": row.remark
            })
        return data

