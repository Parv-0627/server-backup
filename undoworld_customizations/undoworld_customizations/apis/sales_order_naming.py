import frappe

def before_insert(doc, method):
    """
    Set naming series for Sales Orders based on source:
    - B2B: Orders from ERP webshop (Shopping Cart)
    - B2C: Orders from controlz.world (already handled in create_order.py)
    """
    # Skip if naming_series is already set to B2B or B2C
    if doc.naming_series and doc.naming_series.startswith("SO-B2"):
        return
    
    # Check if this is a Shopping Cart order (B2B from ERP webshop)
    is_webshop_order = False
    
    # Check if converted from a Shopping Cart quotation
    if doc.get("quotation"):
        quotation = frappe.db.get_value("Quotation", doc.quotation, "order_type")
        if quotation == "Shopping Cart":
            is_webshop_order = True
    
    # Also check items for Shopping Cart source
    if not is_webshop_order:
        for item in doc.get("items", []):
            if item.get("prevdoc_doctype") == "Quotation":
                quotation_order_type = frappe.db.get_value(
                    "Quotation", item.get("prevdoc_docname"), "order_type"
                )
                if quotation_order_type == "Shopping Cart":
                    is_webshop_order = True
                    break
    
    # Set naming series based on source
    if is_webshop_order:
        doc.naming_series = "SO-B2B-.YYYY.-"
        doc.order_source = "B2B"
    elif not doc.order_source:
        # Default to existing naming series for manual orders
        pass
