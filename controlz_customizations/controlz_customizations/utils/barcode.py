from __future__ import annotations

import base64
from io import BytesIO
import frappe


@frappe.whitelist()
def barcode_data_uri(value: str, bctype: str = "code128") -> str:
    """Generate barcode PNG and return as base64 data URI (no HTTP dependency)."""
    if not value:
        return ""

    cache_key = f"barcode_data_uri::{bctype}::{value}"
    cached = frappe.cache().get_value(cache_key)
    if cached:
        return cached

    import barcode
    from barcode.writer import ImageWriter

    Bar = barcode.get_barcode_class(bctype)

    writer_options = {
        "module_width": 0.2,
        "module_height": 10.0,
        "quiet_zone": 2.0,
        "font_size": 0,
        "write_text": False,
    }

    out = BytesIO()
    Bar(value, writer=ImageWriter()).write(out, options=writer_options)

    b64 = base64.b64encode(out.getvalue()).decode("ascii")
    uri = f"data:image/png;base64,{b64}"

    frappe.cache().set_value(cache_key, uri, expires_in_sec=24 * 3600)
    return uri
