frappe.ui.form.on('Address', {

    refresh: function(frm) {
        $('[data-label="Update%20Address"]').css('display', 'none');
        if(frm.doc.custom_clickpost_location_id){
            frm.set_df_property('custom_upload_to_clickpost', 'read_only', true);
        }
    },
    onload: function(frm) {
        $('[data-label="Update%20Address"]').css('display', 'none');

    },
    onload_post_render: function(frm) {
        $('[data-label="Update%20Address"]').css('display', 'none');
    },
    validate: function(frm) {
        // If custom_upload_to_clickpost is checked, make certain fields mandatory
        if (frm.doc.custom_upload_to_clickpost == 1) {
            const required_fields = [
                { field: 'state', label: 'State' },
                { field: 'email_id', label: 'Email' },
                { field: 'phone', label: 'Phone Number' },
                { field: 'pincode', label: 'Pincode' },
                { field: 'gstin', label: 'GSTIN' }
            ];
            
            let missing_fields = [];
            
            required_fields.forEach(field => {
                if (!frm.doc[field.field]) {
                    missing_fields.push(field.label);
                }
            });
            
            if (missing_fields.length > 0) {
                frappe.msgprint({
                    title: __('Missing Required Fields'),
                    indicator: 'red',
                    message: __(`The following fields are required when uploading to ClickPost: ${missing_fields.join(', ')}`)
                });
                frappe.validated = false;
            }
            // Add validation for phone number
            if (frm.doc.phone && !/^\d{10}$/.test(frm.doc.phone)) {
                frappe.throw(__(`Phone number must be exactly 10 digits. Current value: ${frm.doc.phone}. <a href="/app/address/${frm.doc.name}">${frm.doc.name}</a>`));
            }

            // Add validation for 6-digit pincode
            if (frm.doc.pincode && !/^\d{6}$/.test(frm.doc.pincode)) {
                frappe.throw(__(`Pincode must be exactly 6 digits. Current value: ${frm.doc.pincode}. <a href="/app/address/${frm.doc.name}">${frm.doc.name}</a>`));
            }
        }
    },
    after_save: function(frm) {
        // Only proceed if custom_upload_to_clickpost is checked
        if (frm.doc.custom_upload_to_clickpost == 1) {
            const location_data = {
                "code": frm.doc.name,
                "name": frm.doc.address_title,
                "address": `${frm.doc.address_line1}  ${frm.doc.address_line2 || ""}`,
                "state": frm.doc.state,
                "city": frm.doc.city,
                "pincode": frm.doc.pincode,
                "drop_type": "STORE",
                "max_allowed_tat": 3,
                "floor_number": 1,
                "transport_mode": [
                    frm.doc.custom_transport_mode || "SURFACE"
                ],
                "phone_number": frm.doc.phone,
                "lat": "",
                "long": "",
                "organization_name": "Akhilam Inc",
                "poc_name": "",
                "email": frm.doc.email_id,
                "gstin": frm.doc.gstin,
                "tag": "ERPNext Address",
                "pickup": true,
                "drop": true
            };

            // If form is new, create a new location
            if (frm.is_new()) {
                createClickpostLocation(frm, location_data);
            } 
            // If form is not new and has a clickpost location ID, update the location
            else if (frm.doc.custom_clickpost_location_id) {
                updateClickpostLocation(frm, location_data);
            }
            // If form is not new but doesn't have a clickpost location ID, create a new location
            else {
                createClickpostLocation(frm, location_data);
            }
        }
    }
});

// Function to create a new location in ClickPost
function createClickpostLocation(frm, location_data) {
    frappe.call({
        method: "clickpost_erpnext_integration.clickpost_erpnext_integration.apis.location.create_clickpost_location",
        freeze: true,
        args: { location_data: location_data },
        callback: function(r) {
            
            // Check if the response has the expected structure
            if (r.message && r.message.response && r.message.response.meta && r.message.response.meta.success === false) {
                frappe.show_alert({
                    title: __('Error'),
                    indicator: 'red',
                    message: __(`Error: ${JSON.stringify(r.message.response.meta.message)}` || 'Failed to create location in ClickPost')
                }, 10);
                frm.set_value('custom_upload_to_clickpost', 0);
                frm.save()
            } else if (r.message && r.message.response && r.message.response.id) {
                // Assuming the ID is directly in the response object
                frappe.db.set_value('Address', frm.doc.name, 'custom_clickpost_location_id', JSON.stringify(r.message.response.id), false)

                .then(() => {
                    frm.set_df_property('custom_upload_to_clickpost', 'read_only', true);
                    // Refresh the form to show the updated value
                    frm.refresh_field('custom_clickpost_location_id');
                    
                    frappe.show_alert({
                        title: __('Success'),
                        indicator: 'green',
                        message: __('Location successfully created in ClickPost.')
                    }, 10);
                    frm.reload_doc()
                });
            } else {
                // Handle unexpected response structure
                frappe.show_alert({
                    title: __('Error'),
                    indicator: 'red',
                    message: __('Unexpected response format from ClickPost API')
                }, 10);
                frm.set_value('custom_upload_to_clickpost', 0);
            }
        },
        error: function(err) {
            frappe.show_alert({
                title: __('Error'),
                indicator: 'red',
                message: __('Failed to create location in ClickPost: ' + (err.message || ''))
            }, 10);
            frm.set_value('custom_upload_to_clickpost', 0);
        }
    });
}

// Function to update an existing location in ClickPost
function updateClickpostLocation(frm, location_data) {
    frappe.call({
        method: "clickpost_erpnext_integration.clickpost_erpnext_integration.apis.location.update_clickpost_location",
        args: { location_data: location_data },
        freeze: true,
        callback: function(r) {
            if (r.message.status === "success") {
                frappe.show_alert({
                    title: __('Success'),
                    indicator: 'green',
                    message: __('Location successfully updated in ClickPost.')
                }, 10);
            } else {
                frappe.show_alert({
                    title: __('Error'),
                    indicator: 'red',
                    message: __(r.message.message || 'Failed to update location in ClickPost')
                }, 10);
                frm.set_value('custom_upload_to_clickpost', 0);
            }
        },
        error: function(err) {
            console.log(err);
            frappe.show_alert({
                title: __('Error'),
                indicator: 'red',
                message: __('Failed to update location in ClickPost: ' + (err.message || ''))
            }, 10);
            frm.set_value('custom_upload_to_clickpost', 0);
        }
    });
}

