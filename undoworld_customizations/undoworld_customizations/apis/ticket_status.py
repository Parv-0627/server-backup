import frappe

@frappe.whitelist(methods="POST")
def endpoint(ticket_id):
    try:
        ticket = frappe.get_doc("Support Ticket",ticket_id)
        return {
            "status": ticket.status,
            "status_reason": ticket.status_reason,
            "awb_number_pickup": ticket.awb_number_pickup,
            "awb_number_delivery": ticket.awb_number_delivery,
            "history": ticket.get_history()

        }
    except frappe.DoesNotExistError:
        frappe.clear_messages()
        frappe.local.response.http_status_code = 404
        return "Invalid Ticket Number"