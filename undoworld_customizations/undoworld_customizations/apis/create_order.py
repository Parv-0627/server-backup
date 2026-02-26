import frappe
import erpnext
from frappe.utils import nowdate, add_days, flt
from erpnext.manufacturing.doctype.work_order.work_order import get_default_warehouse



@frappe.whitelist(methods="POST")
def endpoint(mobile_number, customer_name, address,  item_codes,shipping_address,email="", payment=None, discount = None, gst=0, shipping_charge=0, order_payment_type = "", order_id="", juspayid ="", offer_code = "", offer_discount = "", custom_website_coupon_code="", discount_amount=""):
    default_warehouses = get_default_warehouse()
    do_not_save = True
    do_not_submit = True
    customer_doc = frappe.new_doc("Customer")
    customer_doc.customer_name = customer_name + " (" +order_id + ")"
    customer_doc.customer_type = "Individual"
    customer_doc.customer_group = "All Customer Groups"
    customer_doc.territory = "All Territories"
    customer_doc.cu_mobile_number = mobile_number
    customer_doc.cu_email = email
    customer_doc.insert(ignore_permissions=True)
    customer =  customer_doc.name
    
    address_doc = create_addres(address, customer, "Billing")
    shipping_address_doc = create_addres(shipping_address, customer, "Shipping")
        
    so = make_sales_order(
        company=erpnext.get_default_company(),
        transaction_date=nowdate(),
        customer=customer,
        item_codes=item_codes,
        warehouse=default_warehouses,
        qty=1,
        do_not_save=do_not_save,
        do_not_submit=do_not_submit,
        address = address_doc,
        shipping_address = shipping_address_doc,
        gst=gst,
        shipping_charge=shipping_charge,
        discount= discount,
        custom_website_coupon_code=custom_website_coupon_code,
        discount_amount=discount_amount,
        is_b2c=True  # Mark as B2C order from controlz.world
    )
    so.custom_mobile_number = mobile_number
    so.custom_email_id = email
    so.custom_order_payment_type = order_payment_type
    so.custom_order_id = order_id
    so.custom_justpay_id = juspayid
    so.payment_type_un = payment.get("paymenttype")
    so.payment_amount_un = payment.get("amount")
    so.paymentmethod = payment.get("paymentmethod")
    so.payment_status = payment.get("status")
    so.offer_code = offer_code
    so.offer_discount = offer_discount
    so.flags.ignore_permissions = True
    so.save()
    so.flags.ignore_permissions = True
    so.submit()
    return so.name
def create_addres(address, customer, add_type):
    address_doc = frappe.new_doc("Address")
    address_doc.address_type= add_type
    address_doc.address_title = customer
    address_doc.address_line1 = address.get("address_line1")
    address_doc.address_line2 = address.get("address_line2")
    address_doc.city = address.get("city")
    address_doc.state = address.get("state")
    address_doc.country = address.get("country")
    address_doc.pincode = address.get("pincode")
    
    address_doc.append("links",{
        "link_doctype": "Customer",
        "link_name": customer,
    })
    address_doc.insert(ignore_permissions=True)
    return address_doc.name


def make_sales_order(**args):
    so = frappe.new_doc("Sales Order")
    args = frappe._dict(args)
    
    # Set naming series based on order source (B2B or B2C)
    if args.get("is_b2c"):
        so.naming_series = "SO-B2C-.YYYY.-"
        so.order_source = "B2C"
    else:
        so.naming_series = "SO-B2B-.YYYY.-"
        so.order_source = "B2B"
    
    if args.transaction_date:
        so.transaction_date = args.transaction_date

    so.set_warehouse = ""  # no need to test set_warehouse permission since it only affects the client
    so.company = args.company 
    so.customer = args.customer 
    so.currency = "INR"
    so.po_no = args.po_no or ""
    so.shipping_address_name = args.shipping_address
    so.customer_address = args.address
    so.custom_website_coupon_code=args.custom_website_coupon_code
    so.discount_amount=args.discount_amount
    if args.selling_price_list:
        so.selling_price_list = args.selling_price_list

    if "warehouse" not in args:
        args.warehouse = "_Test Warehouse - _TC"

    for row in args.item_codes:
        so.append(
            "items",
            {
                "item_code": row.get("item_code"),
                "margin_type": "",
                "qty": row.get("qty"),
                "rate": row.get("rate"),
            },
        )
        
        # Only add protection plans for items >= Rs.5000 (skip accessories like Charger, Tempered Glass)
        item_rate = flt(row.get("rate", 0))
        if item_rate >= 5000:
            for addon in row.get("addons", []):
                so.append(
                    "items",
                    {
                        "item_code": addon.get("item_code"),
                        "margin_type": "",
                        "is_addons": True,
                        "addons_for": row.get("item_code"),
                        "qty": addon.get("qty"),
                        "rate": addon.get("rate"),
                    },
                )

    if args.gst:
        so.append("taxes", {
            "charge_type": "On Net Total",
            "account_head": frappe.db.get_single_value("OMS Setup", "gst_account"),
            "rate": "18",
            "description": "GST"
        })
    if args.shipping_charge:
        so.append("taxes", {
            "charge_type": "Actual",
            "account_head": frappe.db.get_single_value("OMS Setup", "shipping_account"),
            "tax_amount": args.shipping_charge,
            "description": "Shipping"
        })
    
    if args.discount:
        if args.discount.get("discount_type") == "percentage":
            so.additional_discount_percentage = flt(args.discount.get("discount"))
            so.apply_discount_on = "Net Total"

        if args.discount.get("discount_type") == "amount":
            so.discount_amount = flt(args.discount.get("discount"))
            so.apply_discount_on = "Net Total"

    so.delivery_date = add_days(so.transaction_date, 10)

    if not args.do_not_save:
        so.insert(ignore_permissions=True)
        if not args.do_not_submit:
            so.submit()
        else:
            so.payment_schedule = []
    else:
        so.payment_schedule = []

    return so
