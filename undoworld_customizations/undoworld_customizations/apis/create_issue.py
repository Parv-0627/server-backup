import frappe
from frappe.utils.file_manager import save_file
import json

#fname, content, dt, dn, folder=None, decode=False, is_private=0, df=None

@frappe.whitelist(methods="POST")
def endpoint(**kwargs):
    body = form_body()
    ticket = frappe.get_doc(
        {
            "doctype": "Support Ticket",
            "subject": kwargs.get("issue_faced"),
           
            "imei": kwargs.get("serial_number"),
            
            
            "customer_name": kwargs.get("customer_name"),
            "mobile_number": kwargs.get("mobile_number"),
            "email": kwargs.get("email"),
            "invoice_date": kwargs.get("invoice_date"),
            "order_id": kwargs.get("order_id"),
            "platform": kwargs.get("platform"),
            "description": kwargs.get("description"),
            "brand": kwargs.get("brand"),
            "device_model": kwargs.get("device_model"),
            "issue_faced": kwargs.get("issue_faced"),
            "sub_issue": kwargs.get("sub_issue"),
            "house_number": kwargs.get("house_number"),
            "street_line_1": kwargs.get("street_line_1"),
            "street_line_2": kwargs.get("street_line_2"),
            "city": kwargs.get("city"),
            "state": kwargs.get("state"),
            "pincode": kwargs.get("pincode"),
            "landmark": kwargs.get("landmark"),
        }
    )

    ticket.insert(ignore_permissions=True)
    frappe.db.commit()
    
    audio_recording = body.get("audio_recording")
    if audio_recording:
        audio_file = save_file(
            audio_recording.filename,
            audio_recording.stream.read(), 
            "Support Ticket", 
            ticket.name, 
            df= "audio_recording"
        )
        ticket.audio_recording = audio_file.file_url
    
    video_recording = body.get("video_recording")
    if video_recording:
        video_file = save_file(
            video_recording.filename,
            video_recording.stream.read(), 
            "Support Ticket", 
            ticket.name, 
            df= "video_recording"
        )
        ticket.video_recording = video_file.file_url
    
    front1 = body.get("front1")
    if front1:
        video_file = save_file(
            front1.filename,
            front1.stream.read(), 
            "Support Ticket", 
            ticket.name, 
        )
        ticket.append("support_image_table",{
            "title": "Front 1",
            "image_url" : video_file.file_url
        })
    
    front2 = body.get("front2")
    if front2:
        video_file = save_file(
            front2.filename,
            front2.stream.read(), 
            "Support Ticket", 
            ticket.name, 
        )
        ticket.append("support_image_table",{
            "title": "Front 2",
            "image_url" : video_file.file_url
        })
    
    front3 = body.get("front3")
    if front3:
        video_file = save_file(
            front3.filename,
            front3.stream.read(), 
            "Support Ticket", 
            ticket.name, 
        )
        ticket.append("support_image_table",{
            "title": "Front 3",
            "image_url" : video_file.file_url
        })
    
    back1 = body.get("back1")
    if back1:
        video_file = save_file(
            back1.filename,
            back1.stream.read(), 
            "Support Ticket", 
            ticket.name, 
        )
        ticket.append("support_image_table",{
            "title": "Back 1",
            "image_url" : video_file.file_url
        })
    
    back2 = body.get("back2")
    if back2:
        video_file = save_file(
            back2.filename,
            back2.stream.read(), 
            "Support Ticket", 
            ticket.name, 
        )
        ticket.append("support_image_table",{
            "title": "Back 2",
            "image_url" : video_file.file_url
        })
    
    back3 = body.get("back3")
    if back3:
        video_file = save_file(
            back3.filename,
            back3.stream.read(), 
            "Support Ticket", 
            ticket.name, 
        )
        ticket.append("support_image_table",{
            "title": "Back 3",
            "image_url" : video_file.file_url
        })
    

    idproof1 = body.get("idproof1")
    if idproof1:
        video_file = save_file(
            idproof1.filename,
            idproof1.stream.read(), 
            "Support Ticket", 
            ticket.name, 
        )
        ticket.append("support_image_table",{
            "title": "IDProof 1",
            "image_url" : video_file.file_url
        })
    
    idproof2 = body.get("idproof2")
    if idproof2:
        video_file = save_file(
            idproof2.filename,
            idproof2.stream.read(), 
            "Support Ticket", 
            ticket.name, 
        )
        ticket.append("support_image_table",{
            "title": "IDProof 2",
            "image_url" : video_file.file_url
        })
    
    idproof3 = body.get("idproof3")
    if idproof3:
        video_file = save_file(
            idproof3.filename,
            idproof3.stream.read(), 
            "Support Ticket", 
            ticket.name, 
        )
        ticket.append("support_image_table",{
            "title": "IDProof 3",
            "image_url" : video_file.file_url
        })
    
    
    
    ticket.ignore_permissions = True
    
    ticket.save()
    ticket.add_comment("Comment",json.dumps(kwargs, indent=4))
    return ticket.name

def form_body():
    """Returns a dictionary representing the form body parameters including files."""
    body = frappe.request.form.copy()

    # Add files directly as well. Iterating yields the file parameter names. Indexing with the
    # name yields a werkzeug.datastructures.FileStorage which we use as the value
    for f in frappe.request.files:
        body[f] = frappe.request.files[f]

    return body