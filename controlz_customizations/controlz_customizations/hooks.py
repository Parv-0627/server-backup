app_name = "controlz_customizations"
app_title = "Controlz Customizations"
app_publisher = "Controlz Customizations"
app_description = "Controlz Customizations"
app_email = "controlz@controlz.in"
app_license = "mit"

# -------------------------
# Jinja method registration
# -------------------------
jinja = {
    "methods": [
        "controlz_customizations.utils.barcode.barcode_data_uri"
    ]
}

# backward compatibility
jenv = jinja

doctype_js = {
    "Sales Order": "public/js/sales_order.js",
    "Purchase Receipt": "public/js/purchase_receipt.js"
}
