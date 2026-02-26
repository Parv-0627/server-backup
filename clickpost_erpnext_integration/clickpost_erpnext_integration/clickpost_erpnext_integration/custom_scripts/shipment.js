
let settings = frappe.db.get_doc("Clickpost Configuration")
frappe.ui.form.on("Shipment", {
    add_template: function(frm) {        
        if (frm.doc.parcel_template) {
            // if (doc.custom_sales_invoice.length > 0) {
            //     frm.set_df_property("custom_map_items", "hidden", 0)
            // }
            frappe.model.with_doc("Shipment Parcel Template", frm.doc.parcel_template, () => {
                let parcel_template = frappe.model.get_doc(
                    "Shipment Parcel Template",
                    frm.doc.parcel_template
                );
                if (frm.doc.shipment_parcel && frm.doc.shipment_parcel.length > 0) {
                    frm.doc.shipment_parcel.pop();
                }
                let row = frappe.model.add_child(frm.doc, "Shipment Parcel", "shipment_parcel");
                row.length = parcel_template.length;
                row.width = parcel_template.width;
                row.height = parcel_template.height;
                row.weight = parcel_template.weight;
                
                // Set the custom_parcel field to the name of the parcel template
                row.custom_parcel = frm.doc.parcel_template;
                
                frm.refresh_fields("shipment_parcel");
            });
        }
        
    },
    onload: function(frm) {
        pickup_date_restrictions(frm);
        frm.page.btn_secondary.hide()
    },
    setup: function(frm) {
        frm.set_query("custom_carrier_partner_id", function() {
            return {
                "filters": {
                    "active": 1
                }
            };
        });
        frm.set_query("sales_invoice", "custom_sales_invoice", function() {
            return {
                "filters": [
                    ["Sales Invoice", "docstatus", "=", 1],
                    ["Sales Invoice", "customer", "=", frm.doc.delivery_customer],
                    ["Sales Invoice", "custom_shipment_reference", "=", ""],
                ],
                // "query": "clickpost_erpnext_integration.clickpost_erpnext_integration.utils.get_unshipped_sales_invoices"
            };
        });
    },
    validate: async function(frm) {
        validate_datetime_fields(frm);
        const required_fields = [
            { field: 'custom_order_type', label: 'Order Type' },
            { field: 'custom_delivery_type', label: 'Delivery Type' },
            // { field: 'custom_carrier_partner_id', label: 'Carrier Partner ID' },
            { field: 'shipment_parcel', label: 'Shipment Parcel' },
        ];
        
        let missing_fields = [];
        
        required_fields.forEach(field => {
            if (!frm.doc[field.field]) {
                missing_fields.push(field.label);
            }
        });
        
        
        if (missing_fields.length > 0) {
            frappe.throw(__(`The following fields are required when uploading to ClickPost, please fill them before submnitting: ${missing_fields.join(', ')}`));
        }

        const pickup_address_details = await get_address_details(frm.doc.pickup_address_name);
        const delivery_address_details = await get_address_details(frm.doc.delivery_address_name);

        if (pickup_address_details.pincode == undefined) {
            frappe.throw(__(`Pincode does not exist for pickup address. <a href="/app/address/${frm.doc.pickup_address_name}">${frm.doc.pickup_address_name}</a>`));
        }
        if (!delivery_address_details.pincode) {
            frappe.throw(__(`Pincode does not exist for delivery address. <a href="/app/address/${frm.doc.delivery_address_name}">${frm.doc.delivery_address_name}</a>`));
        }
        // Add validation for 6-digit pincode
        if (pickup_address_details.pincode && !/^\d{6}$/.test(pickup_address_details.pincode)) {
            frappe.throw(__(`Pickup address pincode must be exactly 6 digits. Current value: ${pickup_address_details.pincode}. <a href="/app/address/${frm.doc.pickup_address_name}">${frm.doc.pickup_address_name}</a>`));
        }
        
        if (delivery_address_details.pincode && !/^\d{6}$/.test(delivery_address_details.pincode)) {
            frappe.throw(__(`Delivery address pincode must be exactly 6 digits. Current value: ${delivery_address_details.pincode}. <a href="/app/address/${frm.doc.delivery_address_name}">${frm.doc.delivery_address_name}</a>`));
        }
    },
    custom_start_time: function(frm) {
        if (frm.doc.custom_start_time) {
            validate_start_date(frm);
            // Auto-clear end date if it becomes invalid
            if (frm.doc.custom_end_time) {
                validate_end_date(frm);
            }
        }
    },
    
    custom_end_time: function(frm) {
        if (!frm.doc.custom_start_time) {
            frm.set_value('custom_end_time', '');
            frappe.msgprint(__('Please select start date first'));
            return;
        }
        if (frm.doc.custom_end_time) {
            validate_end_date(frm);
        }
    },
    refresh: async function(frm) {
        set_datetime_restrictions(frm)
        const doc = frm.doc;
        let awaitsettings = await settings
        // item_box_mapping(frm) 
        if (doc.shipment_parcel.length > 0 && doc.custom_sales_invoice.length > 0 && !doc.shipment_id) {
            frm.set_df_property("custom_map_items", "hidden", 0)
        }
        // if(!frm.is_new()){           
        //     frm.reload_doc();
        // }

        if(awaitsettings.use_carrier_recommendation){
            frm.set_df_property("custom_carrier_partner", "read_only", 1)
        }
        if(doc.custom_carrier_partner && !awaitsettings.use_carrier_recommendation){
            frm.set_df_property("custom_carrier_partner", "read_only", 1)
        }

        if(doc.amended_from && frm.is_new()) {
            frm.set_value("shipment_id", "")
            frm.set_value("status", "Draft")
            frm.set_value("custom_clickpost_status", "")
        }

        if(frm.is_new() && frm.doc.value_of_good){
            frm.set_value("custom_cod_value", frm.doc.value_of_good)
        }
        
        if(doc.docstatus === 1 && 
            !doc.shipment_id && 
            !frm.doc.custom_carrier_partner && 
            awaitsettings.use_carrier_recommendation && 
            awaitsettings.recommendation_type == "Manual Selection"
        ) {
            frm.add_custom_button(__('Fetch Recommendations'), function() {
                fetch_recommendation(frm);
            }).css({
                'background-color': 'purple', 
                'color': 'white'
            });
            
        }
        if(doc.docstatus === 1 && 
            !doc.shipment_id && 
            frm.doc.custom_carrier_partner &&
            awaitsettings.use_carrier_recommendation && 
            awaitsettings.recommendation_type == "Manual Selection"
        ) {
            frm.add_custom_button(__('Change Carrier Partner'), function() {
                fetch_recommendation(frm);
            }).css({
                'background-color': 'purple', 
                'color': 'white'
            });
            
        }
        //Create shipment 
        check_shipment_processing_status(frm);
        
        if(doc.docstatus === 1 && doc.shipment_id && doc.awb_number && doc.custom_clickpost_status !== "Cancelled") {
            
            frm.add_custom_button(__('Track Shipment'), function() {
                // Button click action here
                track_shipment(frm)
            }).css({
                'background-color': 'rgb(37, 114, 208)', 
                'color': 'white'
            });
            frm.add_custom_button(__('Get Appointment'), function() {
                // Button click action here
                get_appointment(frm)
            }).css({
                'background-color': 'purple', 
                'color': 'white'
            });
        }
        if (doc.docstatus === 1 && doc.shipment_id && doc.awb_number && doc.custom_clickpost_status !== "Cancelled" && doc.tracking_status === "Delivered") {
            frm.add_custom_button(__('Proof Of Delivery'), function() {
                // Button click action here
                proof_of_delivery(frm)
            }).css({
                'background-color': 'rgb(37, 114, 208)', 
                'color': 'white'
            });
        }
 
        if(doc.docstatus === 1 && doc.shipment_id && doc.awb_number && doc.custom_clickpost_status !== "Cancelled" && doc.tracking_status != "Delivered") {
            
              // Create a dropdown button for Print options
            let print_btn = frm.add_custom_button(__('Print Options'), function() {
                // This function is intentionally empty as we're using it as a dropdown parent
            });
            
            // Style the dropdown button
            print_btn.css({
                'background-color': 'rgb(81, 57, 242)', 
                'color': 'white'
            });
            
            // Make it a dropdown
            print_btn.addClass('dropdown-toggle');
            print_btn.attr('data-toggle', 'dropdown');
            
            // Create dropdown menu
            let dropdown_list = $('<ul class="dropdown-menu" role="menu"></ul>').insertAfter(print_btn);
            
            // Add dropdown items
            [
                {label: __('Print Label'), action: () => get_and_print_document(frm, 'label')},
                {label: __('Print A6 Box Sticker'), action: () => get_and_print_document(frm, 'box_sticker_a6')},
                {label: __('Print A8 Box Sticker'), action: () => get_and_print_document(frm, 'box_sticker_a8')}
            ].forEach(item => {
                $(`<li><a href="#">${item.label}</a></li>`)
                    .on('click', function(e) {
                        e.preventDefault();
                        item.action();
                    })
                    .appendTo(dropdown_list);
            });
            
        }
    },
    on_submit: function(frm) {
        // Update all linked Sales Invoices with the shipment reference
        update_sales_invoice_shipment_reference(frm);
    },
    delivery_customer: function(frm) {
        // Refresh the custom_sales_invoice table when delivery_customer changes
        frm.refresh_field('custom_sales_invoice');
    },
    custom_map_items: function(frm) {
        item_box_mapping(frm);
    },
    before_cancel: function(frm) {
        console.log(frm)
    }
});

function validate_start_date(frm) {
    if (!frm.doc.custom_start_time) return true;
    
    const start_date = frm.doc.custom_start_time;
    const now = frappe.datetime.now_datetime();
    
    if (start_date < now) {
        frm.set_value('custom_start_time', '');
        frm.set_df_property('custom_start_time', 'description', 
            '<span style="color: red;">Start date cannot be in the past</span>');
        frappe.throw(__('Start date cannot be in the past.'));
        return false;
    } else {
        frm.set_df_property('custom_start_time', 'description', '');
    }
    
    return true;
}

function validate_end_date(frm) {
    if (!frm.doc.custom_start_time || !frm.doc.custom_end_time) return true;
    
    const start_date = frappe.datetime.str_to_obj(frm.doc.custom_start_time);
    const end_date = frappe.datetime.str_to_obj(frm.doc.custom_end_time);
    
    if (end_date <= start_date) {
        frm.set_value('custom_end_time', '');
        frm.set_df_property('custom_end_time', 'description', 
            '<span style="color: red;">End date must be after start date</span>');
        frappe.throw(__('End date must be after start date.'));
        return false;
    } else {
        frm.set_df_property('custom_end_time', 'description', '');
    }
    
    return true;
}

function validate_datetime_fields(frm) {
    try {
        validate_start_date(frm);
        validate_end_date(frm);
        return true;
    } catch (e) {
        frappe.validated = false;
        return false;
    }
}

function set_datetime_restrictions(frm) {
    // Set minimum datetime for start time (current datetime)
    set_start_time_restriction(frm);
    
    // Set minimum datetime for end time
    set_end_time_restriction(frm);
}

function set_start_time_restriction(frm) {
    let now = frappe.datetime.now_datetime();
    
    // Set minimum datetime for custom_start_time
    frm.set_df_property('custom_start_time', 'options', {
        minDate: frappe.datetime.get_today(),
        minTime: now
    });
    
    // For datetime field, use this approach
    frm.fields_dict.custom_start_time.datepicker.update({
        minDate: new Date()
    });
    
    
}


function set_end_time_restriction(frm) {
    let now = frappe.datetime.now_datetime();
    let start_time = frm.doc.custom_start_time;

    // Minimum should be either current time or start time (whichever is later)
    let min_datetime = start_time && moment(start_time).isAfter(moment(now)) ? start_time : now;

    frm.fields_dict.custom_end_time.datepicker.update({
        minDate: new Date(min_datetime)
    });

}

function pickup_date_restrictions(frm){
    // Set minimum date for pickup date
    let now = frappe.datetime.now_date();
    
    frm.set_df_property('pickup_date', 'options', {
        minDate: now
    });
    
    // For date field, use this approach
    frm.fields_dict.pickup_date.datepicker.update({
        minDate: new Date(now)
    });
}

function check_shipment_processing_status(frm) {
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Auto Shipment Creation Logs',
            filters: {
                'shipment_reference': frm.doc.name
            },
            fields: ['order_creation_status'],
            limit: 1,
            order_by: 'creation desc'
        },
        callback: function(response) {
            let is_processing = false;
            
            if (response.message && response.message.length > 0) {
                let status = response.message[0].order_creation_status;
                
                if (status === 'Pending') {
                    is_processing = true;
                    frappe.msgprint(__('Shipment still processing, please wait'));
                }
            }
            
            // Add both buttons with conditional state
            add_shipment_buttons(frm, is_processing);
        },
        error: function(error) {
            // Silently handle error (DocType not found or other issues)
            // Just add the buttons normally without any processing check
            add_shipment_buttons(frm, false);
        }
    });
}

function add_shipment_buttons(frm, is_disabled) {
    let doc = frm.doc;
    
    // Create Shipment button
    if (doc.docstatus === 1 && !doc.shipment_id) {
        let create_btn = frm.add_custom_button(__('Create Shipment'), function() {
            if (!is_disabled) {
                create_ship(frm);
            }
        }).css({
            'background-color': 'rgb(29, 160, 142)',
            'color': 'white'
        });
        
        // Disable button if shipment is processing
        if (is_disabled) {
            create_btn.prop('disabled', true);
            create_btn.css('opacity', '0.6');
        }
    }
    
    // Update Status button
    if (doc.docstatus === 1 && !doc.awb_number && doc.shipment_id && doc.custom_clickpost_status !== "Cancelled") {
        let update_btn = frm.add_custom_button(__('Update Status'), async function() {
            if (!is_disabled) {
                // Button click action here
                let sync_result = await sync_shipment(frm);
                if (!sync_result.success) {
                    frappe.throw(`Update failed: ${sync_result.message}`)
                }
            }
        }).css({
            'background-color': 'rgb(37, 114, 208)',
            'color': 'white'
        });
        
        // Disable button if shipment is processing
        if (is_disabled) {
            update_btn.prop('disabled', true);
            update_btn.css('opacity', '0.6');
        }
    }
}

//track shipment
function track_shipment(frm){
    frappe.call({
        method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment.track_shipment',
        args: {
            'waybill': frm.doc.awb_number,
            'cp_id': frm.doc.custom_carrier_partner_id,
        },
        freeze: true,
        freeze_message: __('Tracking Shipment Order...'),
        callback: function(r) {
            if(r.message.response.meta.success == false) {
                frappe.msgprint({
                    title: __('Error'),
                    indicator: 'red',
                    message: `${r.message.response.meta.message.toString()}, ${r.message.response.error.meta.message.toString()}`
                });
            } else {
                if(r.message && r.message.status === 'success') {
                    const result = r.message.response.result;
                    const awb_number = frm.doc.awb_number;
                    const shipment = result[awb_number];
                    console.log(shipment)
            
                    if(shipment) {
                        // Instead of directly manipulating the form, use a server-side method to update the shipment
                        frappe.call({
                            method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.utils.update_shipment_tracking',
                            args: {
                                'shipment_name': frm.doc.name,
                                'tracking_data': shipment
                            },
                            freeze: true,
                            freeze_message: __('Updating shipment tracking data...'),
                            callback: function(update_r) {
                                if(update_r.message && update_r.message.success) {
                                    // Reload the document to show the updated data
                                    frm.reload_doc();
                                    frappe.model.with_doc("Shipment", frm.doc.name, function() {
                                        var doc = frappe.model.get_doc("Shipment", frm.doc.name);
                                    });
                                    
                                    frappe.msgprint({
                                        title: __('Success'),
                                        message: __(`${r.message.response.meta.message.toString()}, shipment tracked successfully`),
                                        indicator: 'green'
                                    });
                                } else {
                                    frappe.msgprint({
                                        title: __('Error'),
                                        indicator: 'red',
                                        message: update_r.message.error || __('Failed to update shipment tracking data')
                                    });
                                }
                            }
                        });
                    }
                }
            }
        }
    });
}

// //sync shipment

async function sync_shipment(frm) {
    try {
        const sync_response = await frappe.call({
            method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment.sync_shipment',
            args: {
                'reference_number': frm.doc.name,
                'courier_partner': frm.doc.custom_carrier_partner_id,
                'account_code': frm.doc.custom_carrier_partner_name,
            },
            freeze: true,
            freeze_message: __('Syncing Shipment...')
        });

        const meta = sync_response.message?.response?.meta;
        const shipment = sync_response.message?.response?.result;

        if (!meta || !meta.success) {
            return {
                success: false,
                message: meta?.message || 'Failed to sync shipment'
            };
        }

        // Update waybill number
        await frappe.call({
            method: 'frappe.client.set_value',
            args: {
                doctype: 'Shipment',
                name: frm.doc.name,
                fieldname: 'awb_number',
                value: shipment.waybill
            },
            freeze: true,
            freeze_message: __('Updating shipment details...')
        });

        // Handle file attachments (label + box stickers)
        const attachment_promises = [];

        if (shipment.label) {
            attachment_promises.push(
                attach_file(shipment.label, frm.doc.name, `label_${frm.doc.name}.pdf`, 'shipping label')
            );
        }

        if (shipment.box_stickers && typeof shipment.box_stickers === 'object') {
            for (const [format, url] of Object.entries(shipment.box_stickers)) {
                if (url) {
                    attachment_promises.push(
                        attach_file(url, frm.doc.name, `${format}_box_sticker_${frm.doc.name}.pdf`, `box sticker ${format}`)
                    );
                }
            }
        }

        const results = await Promise.allSettled(attachment_promises);
        await frm.reload_doc();

        results.forEach(r => {
            if (r.status === 'fulfilled') {
                frappe.show_alert({ message: r.value, indicator: 'green' });
            } else {
                frappe.show_alert({ message: r.reason, indicator: 'red' });
            }
        });

        return {
            success: true,
            message: meta.message || 'Shipment synced and updated successfully'
        };

    } catch (error) {
        return {
            success: false,
            message: error.message || 'Unexpected sync error'
        };
    }
}

// Helper for file attachment
function attach_file(url, docname, filename, filetype) {
    return new Promise((resolve, reject) => {
        frappe.call({
            method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.utils.download_and_attach_file',
            args: {
                url,
                doctype: 'Shipment',
                docname,
                filename
            },
            freeze: true,
            freeze_message: __(`Attaching ${filetype}...`),
            callback: function (r) {
                if (r.message?.success) {
                    resolve(`${filetype} attached successfully`);
                } else {
                    reject(`Failed to attach ${filetype}`);
                }
            }
        });
    });
}

async function create_ship(frm){
    let freeze = false;
    let freeze_message = ''
    if(frm.doc.custom_carrier_partner){
        freeze = true;
        freeze_message = `Creating clickpost shipment, please wait... ${frm.doc.name}`
    }else{
        freeze = true;
        frappe.msgprint({
            title: "Automatic Creation",
            indicator: "green",
            message: (`Clickpost automatic creation added to queue for ${frm.doc.name}, please check log...`)
        });
    }
    await frappe.call({
    method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.custom_scripts.shipment.create_clickpost_shipment_api',
        args: {
            'name': frm.doc.name  // Convert to string for API call if needed
        },
        freeze: freeze,
        freeze_message: freeze_message,
        callback: function(r) {
            if(r.message.success){
                frappe.msgprint({
                    title: "Clickpost Shipment Creation",
                    indicator: "green",
                    message: (`Clickpost shipment successfully created for ${frm.doc.name}`)
                });
                frm.reload_doc()
            }
        }
    });
}

async function create_clickpost_shipment(frm) {
    
    // Ensure sleep is defined once
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    if (!frm.doc.custom_carrier_partner) {
        frappe.show_alert({ message: '🚀 Starting shipment process...', indicator: 'blue' });
        await sleep(1000);

        frappe.show_alert({ message: '📦 Fetching pickup and drop address details...', indicator: 'blue' });
        let pickpincode = await get_address_details(frm.doc.pickup_address_name);
        await sleep(500);
        let droppincode = await get_address_details(frm.doc.delivery_address_name);
        await sleep(500);

        const payload = [{
            reference_number: frm.doc.name,
            pickup_location_code: frm.doc.pickup_address_name,
            pickup_name: frm.doc.custom_pickup_contact_person_name,
            drop_location_code: frm.doc.delivery_address_name,
            pickup_city: pickpincode.city,
            is_restricted: "false",
            drop_city: droppincode.city,
            pickup_state: pickpincode.state,
            drop_state: droppincode.state,
            pickup_address: formatAddress(frm.doc.pickup_address),
            drop_address: formatAddress(frm.doc.delivery_address),
            zone: "WEST",
            box_code: "Small-Box-01",
            item_count: calculate_total_item_count(frm),
            pickup_pincode: pickpincode.pincode,
            drop_pincode: droppincode.pincode,
            invoice_value: frm.doc.value_of_goods,
            weight: calculate_total_weight(frm),
            delivery_type: frm.doc.custom_delivery_type,
            order_type: frm.doc.custom_order_type,
            boxes: recommendation_box(frm)
        }];

        frappe.show_alert({ message: '🔍 Getting carrier recommendations...', indicator: 'blue' });

        let recommendations = [];
        let recommendations_error = [];
        await frappe.call({
            method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment.fetch_recommendation',
            args: { payload },
            callback: (r) => {
                if (r.message && r.message.status === 'success') {
                    recommendations = r.message.response.result[0].preference_array;
                    recommendations_error = r.message.response.result[0];
                }
            }
        });

        console.log(recommendations)

        if (!recommendations.length) {
            frappe.show_alert({ message: `❌ No carriers available ${recommendations_error.toString()}`, indicator: 'red' });
            return;
        }

        frappe.show_alert({ message: `✅ Found ${recommendations.length} carriers`, indicator: 'green' });
        await sleep(1000);

        let success = false;
        let successfulCarrier = null;
        let attempts = [];

        for (let i = 0; i < Math.min(3, recommendations.length); i++) {
            const rec = recommendations[i];

            frappe.show_alert({
                message: `📡 Trying carrier ${i + 1}/${Math.min(3, recommendations.length)}: ${rec.account_code}`,
                indicator: 'blue'
            });
            await sleep(1000);

            // await frappe.db.set_value('Shipment', frm.doc.name, {
            //     custom_carrier_partner: `${rec.cp_id}-${rec.account_code}`,
            //     custom_carrier_partner_id: rec.cp_id,
            //     custom_carrier_partner_name: rec.account_code
            // });
            // await frm.reload_doc();

            frm.set_value('custom_carrier_partner', `${rec.cp_id}-${rec.account_code}`);
            frm.set_value('custom_carrier_partner_id', rec.cp_id);
            frm.set_value('custom_carrier_partner_name', rec.account_code);
            await frm.save('Update');

            let shipment_data = await prepare_shipment_payload(frm);
            let attempt = { carrier: rec.account_code, error: null };

            try {
                let r = await frappe.call({
                    method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment.create_clickpost_shipment',
                    args: { shipment_data: JSON.stringify(shipment_data) }
                });

                if (r.message?.status === 'success' && r.message.response.meta?.success) {
                    await frappe.db.set_value('Shipment', frm.doc.name, {
                        shipment_id: r.message.response.meta.b2b_shipment_id
                    });

                    $('.menu-item-label[data-label="Create%20Shipment"]').remove();
                    await frm.reload_doc();
                    frappe.show_alert({
                        message: `✅ Shipment created with ${rec.account_code}, Syncing... please wait for a few seconds`,
                        indicator: 'green'
                    });

                    await sleep(3000);

                    try {
                        let sync_result = await sync_shipment(frm);
                        console.log(sync_result)

                        // Ensure sync_result has a `success` property
                        if (sync_result.message == 'Order Placed Successfully') {
                            frappe.show_alert({
                                message: `✅ Shipment synced and updated with ${rec.account_code}`,
                                indicator: 'green'
                            });

                            success = true;
                            successfulCarrier = rec;
                        } else {
                            let msg = sync_result?.message?.response?.meta?.message || 'Unknown sync failure';
                            attempt.error = `Sync failed: ${sync_result.message}`;
                            await frappe.db.set_value('Shipment', frm.doc.name, { 
                                shipment_id: "",
                                custom_carrier_partner: "",
                                custom_carrier_partner_id: "",
                                custom_carrier_partner_name: ""
                            });
                            await frm.reload_doc();                        }

                    } catch (syncError) {
                        attempt.error = `Sync exception: ${syncError.message || 'Unknown sync error'}`;
                        await frappe.db.set_value('Shipment', frm.doc.name, { 
                            shipment_id: "",
                            custom_carrier_partner: "",
                            custom_carrier_partner_id: "",
                            custom_carrier_partner_name: ""
                        });
                        await frm.reload_doc();                    }

                } else {
                    attempt.error = r.message?.response?.meta?.message || 'Unknown shipment creation error';
                }

            } catch (shipmentError) {
                attempt.error = shipmentError.message || 'Unknown error during shipment creation';
            }

            attempts.push(attempt);

            if (success) {
                await frm.reload_doc();
                break
            };


        }

        if (!success) {
            // Clear shipment ID if no attempt was successful
            await frappe.db.set_value('Shipment', frm.doc.name, { 
                shipment_id: "",
                custom_carrier_partner: "",
                custom_carrier_partner_id: "",
                custom_carrier_partner_name: ""
            });
            await frm.reload_doc();
            frappe.show_alert({
                message: `❌ None of the carriers were successful.`,
                indicator: 'red'
            });

            let errorHtml = attempts.map(a => `
                <tr>
                    <td>${a.carrier || 'N/A'}</td>
                    <td>${a.error || 'No error message'}</td>
                </tr>
            `).join('');

            frappe.msgprint({
                title: 'Shipment Failed',
                indicator: 'red',
                message: `
                    <p>None of the carriers were successful.</p>
                    <table class="table table-bordered">
                        <thead><tr><th>Carrier</th><th>Error</th></tr></thead>
                        <tbody>${errorHtml}</tbody>
                    </table>
                `
            });
        }

        else if (attempts.length > 1 && attempts[0].carrier !== successfulCarrier.account_code) {
            let altErrors = attempts
                .filter(a => a.carrier !== successfulCarrier.account_code)
                .map(a => `<tr><td>${a.carrier}</td><td>${a.error || 'Unknown error'}</td></tr>`)
                .join('');

            frappe.msgprint({
                title: 'Used Alternative Carrier',
                indicator: 'orange',
                message: `
                    <p>Shipment created with ${successfulCarrier.account_code}, not your first preference:</p>
                    <table class="table table-bordered">
                        <thead><tr><th>Carrier</th><th>Error</th></tr></thead>
                        <tbody>${altErrors}</tbody>
                    </table>
                `
            });
        }
    }


    
    else {
        // If custom_carrier_partner is already set, proceed with shipment creation
        let shipment_data = await prepare_shipment_payload(frm) || {};
        frappe.call({
            method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment.create_clickpost_shipment',
            args: { 'shipment_data': JSON.stringify(shipment_data) },
            freeze: true,
            freeze_message: __('Creating ClickPost Shipment...'),
            callback: function(r) {
                if (r.message && r.message.status === 'success' && r.message.response.meta.success) {
                    let update_data = {
                        'shipment_id': r.message.response.meta.b2b_shipment_id
                    };

                    frappe.db.set_value('Shipment', frm.doc.name, update_data).then(() => {
                        frm.doc.custom_b2b_shipment_id = r.message.response.meta.b2b_shipment_id;
                        $('.menu-item-label[data-label="Create%20Shipment"]').remove();
                        frm.reload_doc();
                        frappe.msgprint({
                            title: __('Success'),
                            indicator: 'green',
                            message: __('ClickPost shipment created successfully')
                        });
                    });
                } else {
                    frappe.msgprint({
                        title: __('Error'),
                        indicator: 'red',
                        message: r.message.response.meta.error || r.message.response.meta.message
                    });
                }
            }
        });
    }
}

//prepare shipment
async function prepare_shipment_payload(frm) {
    // Prepare the shipment payload here
    // Format pickup time to YYYY-MM-DDThh:mm:ss
    let pickup_date = frm.doc.pickup_date;
    let pickup_time = frm.doc.pickup_from;
    
    const formatted_pickup_time = pickup_date 
        ? moment(
            pickup_time 
                ? `${pickup_date} ${pickup_time}` 
                : pickup_date, 
            pickup_time 
                ? 'YYYY-MM-DD HH:mm:ss' 
                : 'YYYY-MM-DD'
        ).format('YYYY-MM-DDTHH:mm:ss') + "+0530"
        : moment().format('YYYY-MM-DDTHH:mm:ss') + "+0530";

    const pickup_address_details = await get_address_details(frm.doc.pickup_address_name);
    const delivery_address_details = await get_address_details(frm.doc.delivery_address_name);
    // Create pickup_info object based on whether location_code exists
    let pickup_info = {};

    const clickpost_config = await get_clickpost_config();
    const use_location_code = clickpost_config.use_location_code_if_available;
    let consignee_gstin = "";
    let enterprise_gstin = "";
    // If location_code exists, only include that
   
    pickup_info.name= frm.doc.custom_pickup_contact_person_name,
    pickup_info.phone= frm.doc.custom_pickup_contact_phone || "0000000000",
    pickup_info.organisation= frm.doc.pickup_company || frm.doc.pickup_customer || frm.doc.pickup_supplier,
    pickup_info.email= frm.doc.pickup_contact_email,
    pickup_info.vendor_code= "",
    pickup_info.time = formatted_pickup_time.toString(),
    // Otherwise include all the address details
    pickup_info.district = pickup_address_details.district;
    pickup_info.city = pickup_address_details.city;
    pickup_info.landmark = "";
    pickup_info.state = pickup_address_details.state;
    pickup_info.pincode = pickup_address_details.pincode;
    pickup_info.country = pickup_address_details.country || "IN";
    pickup_info.address_type = "";
    pickup_info.address = formatAddress(frm.doc.pickup_address);
    enterprise_gstin = pickup_address_details.gstin;

    
    
    // Do the same for drop_info
    let drop_info = {};
    
    // If location_code exists, only include that
    // senitise delivery_contact_name name "Shivam-Akhilm"
    
    drop_info.name = frm.doc.delivery_contact_name.split("-")[0] || frm.doc.custom_delivery_contact_name;
    drop_info.phone = frm.doc.custom_delivery_contact_phone;
    drop_info.email = frm.doc.delivery_contact_email.toString();
    drop_info.organisation = frm.doc.delivery_customer;
    drop_info.vendor_code = "";
    // Otherwise include all the address details
    drop_info.district = delivery_address_details.district;
    drop_info.address_type = "";
    drop_info.landmark = "";
    drop_info.city = delivery_address_details.city;
    drop_info.state = delivery_address_details.state;
    drop_info.pincode = delivery_address_details.pincode;
    drop_info.country = delivery_address_details.country || "IN";
    drop_info.address = formatAddress(frm.doc.delivery_address);
    consignee_gstin = delivery_address_details.gstin;


    //fetch purchase order info
    const purchase_order_info =  await get_purchase_order_info(frm);

    return {
        "pickup_info": pickup_info,
        "drop_info": drop_info,
        "shipment_info": {
            "description": frm.doc.description_of_content,
            "reference_number": frm.doc.name,
            "courier_partner": frm.doc.custom_carrier_partner_id,
            "account_code": frm.doc.custom_carrier_partner_name,
            "cod_value": frm.doc.custom_order_type === "PREPAID" ? 0 : frm.doc.custom_cod_value,
            "order_type": frm.doc.custom_order_type,
            "order_id": "",
            "delivery_type": frm.doc.custom_delivery_type,
            "weight": calculate_total_weight(frm),
            "invoice_info": get_invoice_info(frm),
            "purchase_order_info": purchase_order_info,
            "box_info": get_box_info(frm),
            "gst_info": {
                "seller_gstin": "",
                "enterprise_gstin": pickup_address_details.gstin,
                "taxable_value": 0,
                "is_seller_registered_under_gst": "",
                "place_of_supply": "",
                "gst_discount": 0,
                "gst_total_tax": 0,
                "sgst_tax_rate": 0,
                "sgst_amount": 0,
                "igst_tax_rate": 0,
                "igst_amount": 0,
                "cgst_tax_rate": 0,
                "cgst_amount": 0,
                "consignee_gstin": delivery_address_details.gstin,
                "sgst_total_tax": 0
            },
            "products_in_shipment": products_in_shipment(frm)
        },
        "appointment_info": {
            "start_time": formatERPNextDateTime(frm.doc.custom_start_time) || null,
            "end_time": formatERPNextDateTime(frm.doc.custom_end_time) || null,
            "id": ""
        },
        "additional_info": {
            "return_info": pickup_info,
        }
         
    }      
}


function formatERPNextDateTime(erpNextDateTime) {
    if (!erpNextDateTime) {
      return null
    }
    // Parse the ERPNext datetime
    const dateTime = moment(erpNextDateTime)
  
    // For Indian timezone, we know the offset is always +05:30, which becomes +0530 in our format
    const formattedOffset = "+0530";
    
    return dateTime.format('YYYY-MM-DDTHH:mm:ss') + formattedOffset;
    // return moment(erpNextDateTime, 'YYYY-MM-DD HH:mm:ss').format('YYYY-MM-DDThh:mm:ss');
}
  
function products_in_shipment(frm) {
    let products = {};

    // Check if there are any attached sales invoices
    if (frm.doc.custom_sales_invoice && frm.doc.custom_sales_invoice.length > 0) {
        // Iterate through each attached sales invoice
        frm.doc.custom_sales_invoice.forEach(invoice => {
            if (invoice.sales_invoice) {
                // Fetch items from the sales invoice
                frappe.call({
                    method: 'frappe.client.get',
                    args: {
                        doctype: 'Sales Invoice',
                        name: invoice.sales_invoice
                    },
                    async: false, // Ensure synchronous execution to populate products array
                    callback: async function(response) {
                        if (response.message && response.message.items) {
                            // Add each item from the sales invoice to the products object
                            response.message.items.forEach(async item => {
                                const hsn_code = await get_hsn_code(item.item_code);
                                if (products[item.item_code]) {
                                    // If the product already exists, update the quantity
                                    products[item.item_code].sku_count += item.qty;
                                } else {
                                    // Otherwise, create a new entry for the product
                                    products[item.item_code] = {
                                        sku: item.item_code,
                                        sku_count: item.qty,
                                        description: item.description || "",
                                        product_category: item.item_group || "",
                                        manufacturer_country: item.country_of_origin || "",
                                        manufacturer_country_code: item.country_of_origin_code || "",
                                        hsn_code: hsn_code,
                                        price: item.rate || 0
                                    };
                                }
                            });
                        }
                    }
                });
            }
        });
    }

    // Convert the products object to an array
    return Object.values(products);
}

async function get_hsn_code(item){
    let data = await frappe.db.get_value("Item", item, "gst_hsn_code")
    return data.message.gst_hsn_code || ""
    
}

function calculate_total_weight(frm) {
    let total_weight = 0;
    frm.doc.shipment_parcel.forEach(item => {
        if(item.weight && item.count) {
            total_weight += (item.weight * item.count);
        }
    });
    
    // Default to 0g if no weight is calculated
    return total_weight || 0;
}

function calculate_total_height(frm) {
    let total_height = 0;
    frm.doc.shipment_parcel.forEach(item => {
        if(item.height && item.count) {
            total_height += (item.height * item.count);
        }
    });
    
    // Default to 0cm if no height is calculated
    return total_height || 0;
}

function calculate_total_length(frm) {
    let total_length = 0;
    frm.doc.shipment_parcel.forEach(item => {
        if(item.length && item.count) {
            total_length += (item.length * item.count);
        }
    });
    
    // Default to 0cm if no length is calculated
    return total_length || 0;
}
function calculate_total_breadth(frm) {
    let total_breadth = 0;
    frm.doc.shipment_parcel.forEach(item => {
        if(item.width && item.count) {
            total_breadth += (item.width * item.count);
        }
    });
    

    return total_breadth || 0;
}

function get_address_details(address_name) {
    return new Promise((resolve, reject) => {
        if (!address_name) {
            reject("Address name is required");
            return;
        }
        
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Address',
                name: address_name
            },
            callback: function(response) {
                if (response.message) {
                    const address = response.message;
                    const address_details = {
                        city: address.city || "",
                        state: address.state || "",
                        pincode: address.pincode || "",
                        country: get_country_code(address.country || "India"),
                        address: address.address_line1 + 
                                (address.address_line2 ? ", " + address.address_line2 : ""),
                        district: address.county || address.city || "",
                        location_code: address.custom_clickpost_location_id || "",
                        gstin: address.gstin || ""
                    };
                    resolve(address_details);
                } else {
                    reject("Address not found");
                }
            },
            error: function(err) {
                reject("Error fetching address: " + err);
            }
        });
    });
}


function recommendation_box(frm){
    return frm.doc.shipment_parcel.map(parcel => {
        return {
            "height": parcel.height || 10,
            "length": parcel.length || 10,
            "weight": parcel.weight || 10,
            "breadth": parcel.width || 10,
        };
    });
}

function get_box_info(frm) {
    // If there are no parcels, return a default box
    // Map each parcel to a box info object
    return frm.doc.shipment_parcel.map(parcel => {
        return {
            "count": parcel.count || 1,
            "reference_number_prefix": "",
            "box_master_code": "",
            "height": parcel.height || 10,
            "length": parcel.length || 10,
            "weight": parcel.weight || 10,
            "breadth": parcel.width || 10,
            "description": "",
            "purchase_order_info": [
                {
                    "number": ""
                }
            ],
            "invoice_info": [
                {
                    "number": ""
                }
            ],
            "product_info": [
                {
                    "sku": "",
                    "sku_count": parcel.count || 1,
                    "description": "",
                    "product_category": "",
                    "manufacturer_country": "",
                    "manufacturer_country_code": "",
                    "hsn_code": "",
                    "price": null
                },
            ]
        };
    });
}

function get_invoice_info(frm) {
    return frm.doc.custom_sales_invoice.map(invoice => {
        return {
            "number": invoice.sales_invoice,
            "value": invoice.grand_total,
            "date": invoice.posting_date,
            "base64": "",
            "ewaybill_serial_number": invoice.e_waybill_number || null,
            "ewaybill_expiry_date": invoice.e_waybill_expiry_date || null,
            "description": ""
        };
    });
}

function get_purchase_order_info(frm) {
    return new Promise((resolve, reject) => {
        if (!frm.doc.custom_sales_invoice || frm.doc.custom_sales_invoice.length === 0) {
            resolve([]);
            return;
        }

        const purchase_order_promises = frm.doc.custom_sales_invoice.map(invoice => {
            return new Promise((resolve, reject) => {
                frappe.call({
                    method: 'frappe.client.get_value',
                    args: {
                        doctype: 'Sales Invoice',
                        filters: {
                            name: invoice.sales_invoice
                        },
                        fieldname: ['po_no', 'po_date']
                    },
                    callback: function(response) {
                        if (response.message) {
                            resolve({
                                number: response.message.po_no || "",
                                expiry_date: response.message.po_date || null
                            });
                        } else {
                            resolve({
                                number: "",
                                expiry_date: null
                            });
                        }
                    },
                    error: function(err) {
                        console.error("Error fetching purchase order info:", err);
                        resolve({
                            number: "",
                            expiry_date: null
                        });
                    }
                });
            });
        });

        Promise.all(purchase_order_promises)
            .then(purchase_order_info => {
                resolve(purchase_order_info);
            })
            .catch(error => {
                console.error("Error fetching purchase order info:", error);
                reject(error);
            });
    });
}

function update_sales_invoice_shipment_reference(frm) {
    if (!frm.doc.custom_sales_invoice || frm.doc.custom_sales_invoice.length === 0) {
        return;
    }
    
    // Show a loading message
    frappe.show_alert({
        message: __('Updating Sales Invoice references...'),
        indicator: 'blue'
    });
    
    // Create an array of promises for each update
    const update_promises = frm.doc.custom_sales_invoice.map(invoice_row => {
        return new Promise((resolve, reject) => {
            frappe.call({
                method: 'frappe.client.set_value',
                args: {
                    doctype: 'Sales Invoice',
                    name: invoice_row.sales_invoice,
                    fieldname: 'custom_shipment_reference',
                    value: frm.doc.name
                },
                callback: function(response) {
                    if (response.exc) {
                        reject(response.exc);
                    } else {
                        resolve();
                    }
                }
            });
        });
    });
    
    // Wait for all updates to complete
    Promise.all(update_promises)
        .then(() => {
            frappe.show_alert({
                message: __('All Sales Invoices updated with shipment reference'),
                indicator: 'green'
            });
        })
        .catch(error => {
            frappe.show_alert({
                message: __('Error updating Sales Invoice references: ') + error,
                indicator: 'red'
            });
        });
}


frappe.ui.form.on('Shipment Delivery Note', {
    // When delivery_note is added/changed
    shipment_delivery_note_add: function(frm, cdt, cdn) {
        // Get the current row that was added
        let row = locals[cdt][cdn];
        
        // Check if custom_sales_invoice child table has items
        if (frm.doc.custom_sales_invoice && frm.doc.custom_sales_invoice.length > 0) {
            frappe.confirm(
                __('Adding a Delivery Note will clear existing Sales Invoice entries. Continue?'),
                function() {
                    // User clicked "Yes" - clear the Sales Invoice child table
                    frm.clear_table('custom_sales_invoice');
                    frm.refresh_field('custom_sales_invoice');
                    frappe.show_alert({
                        message: __('Sales Invoice entries have been cleared'),
                        indicator: 'yellow'
                    });
                },
                function() {
                    // User clicked "No" - remove the newly added delivery note row
                    frm.get_field('shipment_delivery_note').grid.grid_rows[
                        frm.get_field('shipment_delivery_note').grid.grid_rows.length - 1
                    ].remove();
                    frm.refresh_field('shipment_delivery_note');
                }
            );
        }
    }
});

frappe.ui.form.on('Sales Invoice Shipment', {
    // When custom_sales_invoice is added/changed
    custom_sales_invoice_add: function(frm, cdt, cdn) {
        
        // Get the current row that was added
        let row = locals[cdt][cdn];
        if (doc.shipment_parcel.length > 0) {
            frm.set_df_property("custom_map_items", "hidden", 0)
        }
        
        // Check if shipment_delivery_note child table has items
        if (frm.doc.shipment_delivery_note && frm.doc.shipment_delivery_note.length > 0) {
            frappe.confirm(
                __('Adding a Sales Invoice will clear existing Delivery Note entries. Continue?'),
                function() {
                    // User clicked "Yes" - clear the Delivery Note child table
                    frm.clear_table('shipment_delivery_note');
                    frm.refresh_field('shipment_delivery_note');
                    frappe.show_alert({
                        message: __('Delivery Note entries have been cleared'),
                        indicator: 'yellow'
                    });
                },
                function() {
                    // User clicked "No" - remove the newly added sales invoice row
                    frm.get_field('custom_sales_invoice').grid.grid_rows[
                        frm.get_field('custom_sales_invoice').grid.grid_rows.length - 1
                    ].remove();
                    frm.refresh_field('custom_sales_invoice');
                }
            );
        }
        check_duplicate_sales_invoice(frm, row);

        calculate_total_amount(frm);
        
    },
    custom_sales_invoice_remove: function(frm, cdt, cdn) {
        calculate_total_amount(frm);
    },
    
    sales_invoice: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        check_duplicate_sales_invoice(frm, row);
        
        // When a sales invoice is selected, fetch its grand total
        if(row.sales_invoice) {
            frappe.db.get_value('Sales Invoice', row.sales_invoice, 'grand_total')
                .then(r => {
                    if(r.message && r.message.grand_total) {
                        frappe.model.set_value(cdt, cdn, 'grand_total', r.message.grand_total);
                        calculate_total_amount(frm);
                    }
                });
            frappe.db.get_value('e-Waybill Log', { reference_name: row.sales_invoice, reference_doctype: "Sales Invoice" }, 'valid_upto')
            .then(r => {
                if (r.message && r.message.valid_upto) {
                    frappe.model.set_value(cdt, cdn, 'e_waybill_expiry_date', r.message.valid_upto);
                } else {
                    frappe.msgprint({
                        title: __('Warning'),
                        indicator: 'orange',
                        message: __('No E-Waybill Log found for Sales Invoice {0}', [row.sales_invoice])
                    });
                }
            });
        }
    },
    
    grand_total: function(frm, cdt, cdn) {
        calculate_total_amount(frm);
    }
});

// Function to check for duplicate sales invoice entries
function check_duplicate_sales_invoice(frm, current_row) {
    if (!current_row.sales_invoice) return;
    
    let duplicate_found = false;
    let duplicate_index = -1;
    
    // Check if this sales invoice already exists in the table
    frm.doc.custom_sales_invoice.forEach((row, index) => {
        if (row.name !== current_row.name && 
            row.sales_invoice === current_row.sales_invoice) {
            duplicate_found = true;
            duplicate_index = index + 1; // +1 for human-readable index
        }
    });
    
    if (duplicate_found) {
        frappe.msgprint({
            title: __('Duplicate Entry'),
            indicator: 'red',
            message: __('Sales Invoice {0} already exists at row {1}. Duplicate entries are not allowed.', 
                [current_row.sales_invoice, duplicate_index])
        });
        
        // Clear the sales invoice field in the current row
        frappe.model.set_value(current_row.doctype, current_row.name, 'sales_invoice', '');
        
        return false;
    }
    
    return true;
}

function get_and_print_document(frm, doc_type) {
    frappe.call({
        method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment.sync_shipment',
        args: {
            'reference_number': frm.doc.name,
            'courier_partner': frm.doc.custom_carrier_partner_id,
            'account_code': frm.doc.custom_carrier_partner_name,
        },
        freeze: true,
        freeze_message: __(`Getting ${doc_type.replace('_', ' ')}...`),
        callback: function(r) {
            if(r.message && r.message.status === 'success') {
                let url;
                
                if (doc_type === 'label') {
                    url = r.message.response.result.label;
                } else if (doc_type === 'box_sticker_a6' || doc_type === 'box_sticker_a8') {
                    const format = doc_type === 'box_sticker_a6' ? 'A6' : 'A8';
                    if (r.message.response.result.box_stickers && 
                        r.message.response.result.box_stickers[format]) {
                        url = r.message.response.result.box_stickers[format];
                    } else {
                        frappe.msgprint({
                            title: __('Error'),
                            indicator: 'red',
                            message: __(`${format.toUpperCase()} box sticker not available`)
                        });
                        return;
                    }
                }
                
                if (!url) {
                    frappe.msgprint({
                        title: __('Error'),
                        indicator: 'red',
                        message: __(`${doc_type.replace('_', ' ')} not available`)
                    });
                    return;
                }
                
                let d = new frappe.ui.Dialog({
                    title: __(`${doc_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} Preview`),
                    size: 'large', // large dialog
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'document_preview',
                            label: __('Preview')
                        }
                    ],
                    primary_action_label: __('Print'),
                    primary_action: function() {                        
                        // Open the print dialog
                        const printWindow = window.open(url);
                        printWindow.addEventListener('load', function() {
                            printWindow.print();
                        }, { once: true });
                        
                        d.hide();
                    },
                    secondary_action_label: __('Download'),
                    secondary_action: function() {
                        // Create a download link for the PDF
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `${doc_type}_${frm.doc.name}.pdf`;
                        a.target = '_blank';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                    }
                });
                
                // Set up the PDF viewer in the dialog
                d.fields_dict.document_preview.$wrapper.html(`
                    <div style="height: 600px; overflow: auto;">
                        <embed src="${url}" type="application/pdf" width="100%" height="100%">
                    </div>
                `);
                
                d.show();
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    indicator: 'red',
                    message: r.message.message || __(`Failed to get ${doc_type.replace('_', ' ')}`)
                });
            }
        }
    });
}

// Function to calculate total amount
function calculate_total_amount(frm) {
    let total_amount = 0;
    
    if(frm.doc.custom_sales_invoice && frm.doc.custom_sales_invoice.length > 0) {
        frm.doc.custom_sales_invoice.forEach(invoice => {
            if(invoice.grand_total) {
                total_amount += flt(invoice.grand_total);
            }
        });
    }
    
    // Set the calculated amount to the shipment amount field
    // Assuming the field name is 'amount' - adjust if it's different
    frm.set_value('shipment_amount', total_amount);
    frm.set_value('value_of_goods', total_amount);
    frm.set_value('custom_cod_value', total_amount);
    frm.refresh_field('shipment_amount');
    frm.refresh_field('value_of_goods');
    frm.refresh_field('custom_cod_value');
}

function proof_of_delivery(frm) {
    frappe.call({
        method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment.get_proof_of_delivery',
        args: {
            'waybill': frm.doc.awb_number,
            'cp_id': frm.doc.custom_carrier_partner_id,
        },
        freeze: true,
        freeze_message: __('Fetching Proof of Delivery...'),
        callback: function(r) {
            if(r.message && r.message.status === 'success' && r.message.response.meta.success) {
                const pod_url = r.message.response.result.pod_url;
                
                if (!pod_url) {
                    frappe.msgprint({
                        title: __('Error'),
                        indicator: 'red',
                        message: __('Proof of Delivery document not available')
                    });
                    return;
                }
                
                // Determine file extension from URL or default to pdf
                const url_parts = pod_url.split('?')[0].split('.');
                const file_extension = url_parts.length > 1 ? url_parts.pop().toLowerCase() : 'pdf';
                const supported_extensions = ['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'gif'];
                
                if (!supported_extensions.includes(file_extension)) {
                    frappe.msgprint({
                        title: __('Warning'),
                        indicator: 'orange',
                        message: __(`File format .${file_extension} may not be properly displayed. Supported formats are: ${supported_extensions.join(', ')}`)
                    });
                }
                
                // Attach the POD to the document first
                frappe.call({
                    method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.utils.download_and_attach_file',
                    args: {
                        'url': pod_url,
                        'doctype': 'Shipment',
                        'docname': frm.doc.name,
                        'filename': `pod_${frm.doc.name}.${file_extension}`
                    },
                    freeze: true,
                    freeze_message: __('Attaching Proof of Delivery...'),
                    callback: function(attach_r) {
                        if(attach_r.message && attach_r.message.success) {
                            // Get the local file URL from the attachment
                            const file_url = attach_r.message.file_url;
                            
                            // Update the custom_pod_file field with the file URL
                            frappe.db.set_value('Shipment', frm.doc.name, 'custom_pod_file', file_url)
                                .then(() => {
                                    // Update the local doc
                                    frm.doc.custom_pod_file = file_url;
                                    
                                    frappe.show_alert({
                                        message: __('Proof of Delivery attached successfully'),
                                        indicator: 'green'
                                    });
                                    
                                    // Show preview dialog with the local file URL
                                    let d = new frappe.ui.Dialog({
                                        title: __('Proof of Delivery Preview'),
                                        size: 'large',
                                        fields: [
                                            {
                                                fieldtype: 'HTML',
                                                fieldname: 'pod_preview',
                                                label: __('Preview')
                                            }
                                        ],
                                        primary_action_label: __('Print'),
                                        primary_action: function() {
                                            // Open the print dialog with the local file
                                            const printWindow = window.open(file_url);
                                            printWindow.addEventListener('load', function() {
                                                printWindow.print();
                                            }, { once: true });
                                            
                                            d.hide();
                                        }
                                    });
                                    
                                    // Set up the viewer in the dialog based on file type
                                    let preview_html = '';
                                    if (file_extension === 'pdf') {
                                        preview_html = `
                                            <div style="height: 600px; overflow: auto;">
                                                <embed src="${file_url}" type="application/pdf" width="100%" height="100%">
                                            </div>
                                        `;
                                    } else if (['png', 'jpg', 'jpeg', 'gif'].includes(file_extension)) {
                                        preview_html = `
                                            <div style="height: 600px; overflow: auto; text-align: center;">
                                                <img src="${file_url}" style="max-width: 100%; max-height: 100%;">
                                            </div>
                                        `;
                                    } else if (file_extension === 'tiff') {
                                        // TIFF files may not display in all browsers
                                        preview_html = `
                                            <div style="height: 600px; overflow: auto; text-align: center;">
                                                <p class="text-muted">${__('TIFF files may not display correctly in all browsers.')}</p>
                                                <img src="${file_url}" style="max-width: 100%; max-height: 100%;">
                                            </div>
                                        `;
                                    } else {
                                        preview_html = `
                                            <div style="height: 600px; overflow: auto; text-align: center;">
                                                <p>${__('Preview not available for this file type. Click "Print" to open the file in a new tab.')}</p>
                                            </div>
                                        `;
                                    }
                                    
                                    d.fields_dict.pod_preview.$wrapper.html(preview_html);
                                    d.show();
                                    
                                    // Reload the document to show the attachment in the sidebar
                                    frm.reload_doc();
                                });
                        } else {
                            frappe.msgprint({
                                title: __('Error'),
                                indicator: 'red',
                                message: attach_r.message.error || __('Failed to attach Proof of Delivery')
                            });
                        }
                    }
                });
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    indicator: 'red',
                    message: r.message && r.message.response && r.message.response.meta 
                        ? r.message.response.meta.message 
                        : __('Failed to fetch Proof of Delivery')
                });
            }
        }
    });
}

function get_clickpost_config() {
    return new Promise((resolve, reject) => {
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'ClickPost Configuration',
                fieldname: ['use_location_code_if_available']
            },
            callback: function(response) {
                if (response.message) {
                    resolve(response.message);
                } else {
                    resolve({ use_location_code_if_available: 0 });
                }
            },
            error: function(err) {
                console.error("Error fetching ClickPost settings:", err);
                resolve({ use_location_code_if_available: 0 });
            }
        });
    });
}

function formatAddress(address) {
    if (!address) return "";
    
    // Replace <br> tags with commas or spaces
    let formattedAddress = address
        .replace(/<br\s*\/?>/gi, ", ") // Replace <br> tags with comma and space
        .replace(/&nbsp;/gi, " ")      // Replace &nbsp; with space
        .replace(/<[^>]*>/g, "")       // Remove any other HTML tags
        .replace(/,\s*,/g, ",")        // Replace multiple commas with a single comma
        .replace(/\s+/g, " ")          // Replace multiple spaces with a single space
        .trim();                       // Remove leading/trailing whitespace
    
    // Remove trailing comma if exists
    if (formattedAddress.endsWith(",")) {
        formattedAddress = formattedAddress.slice(0, -1).trim();
    }
    
    return formattedAddress;
}

function get_country_code(country_name) {
    // return new Promise((resolve, reject) => {
        if (!country_name) {
             // Default to India if no country name provided
            return "IN"
        }
        
        frappe.db.get_value("Country", country_name, "code")
            .then(response => {
                if (response.message && response.message.code) {
                   return response.message.code;
                } else {
                    // If country code not found, default to India
                    console.warn(`Country code not found for ${country_name}, defaulting to IN`);
                    return "IN"
                }
            })
            .catch(error => {
                console.error("Error fetching country code:", error);
                return "IN"; // Default to India in case of error
            });
    // });
}

function calculate_total_item_count(frm) {
    let total_item_count = 0;

    if (frm.doc.custom_sales_invoice && frm.doc.custom_sales_invoice.length > 0) {
        frm.doc.custom_sales_invoice.forEach(invoice => {
            if (invoice.sales_invoice) {
                frappe.call({
                    method: 'frappe.client.get',
                    args: {
                        doctype: 'Sales Invoice',
                        name: invoice.sales_invoice
                    },
                    async: false, // Ensure synchronous execution to get item counts
                    callback: function(response) {
                        if (response.message && response.message.items) {
                            response.message.items.forEach(item => {
                                total_item_count += item.qty;
                            });
                        }
                    }
                });
            }
        });
    }

    return total_item_count;
}

async function fetch_recommendation(frm) {
    let pickpincode = await get_address_details(frm.doc.pickup_address_name);
    let droppincode = await get_address_details(frm.doc.delivery_address_name);
    const payload = [
        {
            "reference_number": frm.doc.name,
            "pickup_location_code": frm.doc.pickup_address_name,
            "pickup_name": frm.doc.custom_pickup_contact_person_name,
            "drop_location_code": frm.doc.delivery_address_name,
            "pickup_city": pickpincode.city,
            "is_restricted": "false",
            "drop_city": droppincode.city,
            "pickup_state": pickpincode.state,
            "drop_state": droppincode.state,
            "pickup_address": formatAddress(frm.doc.pickup_address),
            "drop_address": formatAddress(frm.doc.delivery_address),
            "zone": "WEST",
            "box_code": "Small-Box-01",
            "item_count": calculate_total_item_count(frm),
            "pickup_pincode": pickpincode.pincode,
            "drop_pincode": droppincode.pincode,
            "invoice_value": frm.doc.value_of_goods,
            "weight": calculate_total_weight(frm),
            // "length": calculate_total_length(frm),
            // "breadth": calculate_total_breadth(frm),
            // "height": calculate_total_height(frm),
            "delivery_type": frm.doc.custom_delivery_type,
            "order_type": frm.doc.custom_order_type,
            "boxes": recommendation_box(frm)
        }
    ]
    
    frappe.call({
        method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment.fetch_recommendation',
        args: {
            payload: payload //JSON.stringify(payload) // Convert payload to string if required by the API
        },
        freeze: true,
        freeze_message: __('Fetching Recommendations...'),
        callback: function(response) {
            if (response.message && response.message.status === 'success') {
                const recommendations = response.message.response.result[0].preference_array;
                // console.log(recommendations)
                // Create a table dialog to display the recommendations
                let table_html = `
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>Courier Partner Name</th>
                                <th>Account Code</th>
                                <th>Priority</th>
                                <th>Delivery Type</th>
                                <th>Shipping Charge</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                recommendations.forEach((rec, index) => {
                    table_html += `
                        <tr>
                            <td>${rec.cp_name || '-'}</td>
                            <td>${rec.account_code || '-'}</td>
                            <td>${rec.priority || '-'}</td>
                            <td>${rec.delivery_type || '-'}</td>
                            <td>${rec.shipping_charge !== null ? rec.shipping_charge : 'N/A'}</td>
                            <td>
                                <button class="btn btn-primary btn-sm select-recommendation" data-index="${index}">
                                    Select
                                </button>
                            </td>
                        </tr>
                    `;
                });

                table_html += `
                        </tbody>
                    </table>
                `;

                // Show the dialog
                let dialog = new frappe.ui.Dialog({
                    title: __('Recommendations'),
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'recommendations_table',
                            options: table_html
                        }
                    ],
                    primary_action_label: __('Close'),
                    primary_action: function() {
                        dialog.hide();
                    }
                });

                dialog.show();
                dialog.$wrapper.find('.select-recommendation').on('click', function() {
                    const index = $(this).data('index');
                    const selected_recommendation = recommendations[index];

                    // Perform an action with the selected recommendation
                    

                    // Example: Set selected recommendation details in the form
                    frm.set_value('custom_carrier_partner', `${selected_recommendation.cp_id}-${selected_recommendation.account_code}`)
                    frm.set_value('custom_carrier_partner_id', selected_recommendation.cp_id);
                    frm.set_value('custom_carrier_partner_name', selected_recommendation.account_code);

                    frappe.msgprint({
                        title: __('Selected Recommendation'),
                        message: `You selected: ${selected_recommendation.cp_name || '-'}`,
                        indicator: 'green'
                    });

                    dialog.hide();
                    frm.save("Update")

                });
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    indicator: 'red',
                    message: response.message.message || __('Failed to fetch recommendations')
                });
            }
        }
    });
}


function get_appointment(frm){
    frappe.call({
        method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment.get_appointment',
        args: {
            "awb_number": frm.doc.awb_number,
            "account_code": frm.doc.custom_carrier_partner_name,
            "courier_partner_id": frm.doc.custom_carrier_partner_id
        },
        freeze: true,
        freeze_message: __('Getting Appointment Details...'),
        callback: async function(r) {
            if(r.message.response.appointment_start_time) {
                const result = r.message.response;
                frm.set_value("custom_start_time", frappeDatetime(result.appointment_start_time));
                frm.set_value("custom_end_time", frappeDatetime(result.appointment_end_time));
                frm.set_value("custom_reason_for_appointment", result.reason_for_appointment_change);
                frm.set_value("custom_appointment_status", result.appointment_status);

                if (Array.isArray(result.appointment_documents) && result.appointment_documents.length > 0) {
                    let links = [];
                    for (let i = 0; i < result.appointment_documents.length; i++) {
                        const url = result.appointment_documents[i];
                        // Get file extension
                        const ext = url.split('?')[0].split('.').pop().toLowerCase();
                        const filename = `appointment_doc_${frm.doc.name}_${i+1}.${ext}`;
                        try {
                            // Download and attach the file using your backend API
                            const attach_r = await new Promise((resolve, reject) => {
                                frappe.call({
                                    method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.utils.download_and_attach_file',
                                    args: {
                                        url: url,
                                        doctype: 'Shipment',
                                        docname: frm.doc.name,
                                        filename: filename
                                    },
                                    freeze: true,
                                    freeze_message: __('Attaching appointment document...'),
                                    callback: function(r) {
                                        if (r.message && r.message.success && r.message.file_url) {
                                            console.log(r.message.file_url)
                                            resolve(r.message.file_url);
                                        } else {
                                            reject();
                                        }
                                    }
                                });
                            });
                            links.push(`<a href="${attach_r}" target="_blank">Appointment Document ${i+1}.${ext}</a>`);
                        } catch (e) {
                            frappe.show_alert({message: `Failed to attach Document ${i+1}`, indicator: 'red'});
                            links.push(`<span style="color:red">Failed to attach Document ${i+1}</span>`);
                        }
                    }
                    frm.set_value("custom_appointment_document", links.join("<br>"));
                    frm.refresh_field("custom_appointment_document");
                } else {
                    frm.set_value("custom_appointment_document", __("No appointment documents found."));
                    frm.refresh_field("custom_appointment_document");
                }

                await frm.save("Update");
                await frm.reload_doc();
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    indicator: 'red',
                    message: `${r.message.response.meta.message.toString()}`
                });
            }
        }
    });
}

function frappeDatetime(datetime) {
    // Check if it's in DD-MM-YYYY format
    const match = datetime.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})[+-]\d{4}$/);
    if (!match) throw new Error('Invalid datetime format');

    const [_, year, month, day, hour, minute, second] = match;
    return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
}

async function item_box_mapping(frm) {
    let all_items = [];
    let sales_invoice_map = {};

    async function get_hsn_code(item_code) {
        let data = await frappe.db.get_value("Item", item_code, "gst_hsn_code");
        return data.message.gst_hsn_code || "";
    }

    for (let invoice_row of (frm.doc.custom_sales_invoice || [])) {
        if (!invoice_row.sales_invoice) continue;
        let response = await frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Sales Invoice',
                name: invoice_row.sales_invoice
            }
        });

        let invoice_items = response.message?.items || [];
        for (let item of invoice_items) {
            let hsn_code = await get_hsn_code(item.item_code);
            let product_info = {
                sku: item.item_code,
                sku_count: item.qty,
                description: item.description || "",
                product_category: item.item_group || "",
                manufacturer_country: item.country_of_origin || "",
                manufacturer_country_code: item.country_of_origin_code || "",
                hsn_code: hsn_code,
                price: item.rate || 0
            };
            all_items.push({
                sales_invoice: invoice_row.sales_invoice,
                product_info
            });
            if (!sales_invoice_map[invoice_row.sales_invoice]) {
                sales_invoice_map[invoice_row.sales_invoice] = [];
            }
            sales_invoice_map[invoice_row.sales_invoice].push(product_info);
        }
    }

    let parcel_options = (frm.doc.shipment_parcel || []).map((parcel, idx) => {
        let name = parcel.custom_parcel || parcel.box_code || `Parcel`;
        return {
            label: `${name}-${idx + 1}`,
            value: idx
        };
    });

    let table_html = `
        <table class="table table-bordered">
            <thead>
                <tr>
                    <th>Sales Invoice</th>
                    <th>SKU</th>
                    <th>Description</th>
                    <th>Qty</th>
                    <th>Parcel</th>
                </tr>
            </thead>
            <tbody>
    `;

    all_items.forEach((item, idx) => {
        let parcel_select = `<select class="form-control parcel-select" data-idx="${idx}">`;
        parcel_options.forEach(opt => {
            parcel_select += `<option value="${opt.value}">${opt.label}</option>`;
        });
        parcel_select += `</select>`;

        table_html += `
            <tr>
                <td>${item.sales_invoice}</td>
                <td>${item.product_info.sku}</td>
                <td>${item.product_info.description}</td>
                <td>${item.product_info.sku_count}</td>
                <td>${parcel_select}</td>
            </tr>
        `;
    });

    table_html += `
            </tbody>
        </table>
        <div id="item-box-mapping-result"></div>
        <div class="text-right mt-3">
            <button class="btn btn-primary" id="map-all-btn">Map All</button>
        </div>
    `;

    let dialog = new frappe.ui.Dialog({
        title: __('Item Box Mapping'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'item_box_mapping_table',
                options: table_html
            }
        ],
        primary_action_label: __('Close'),
        primary_action: function () {
            dialog.hide();
        }
    });

    dialog.show();

    // Handle Map All button
    // dialog.$wrapper.find('#map-all-btn').on('click', function () {
    //     let result_html = "";
    //     all_items.forEach((item, idx) => {
    //         let parcel_idx = dialog.$wrapper.find(`.parcel-select[data-idx="${idx}"]`).val();
    //         let parcel_label = parcel_options[parcel_idx]?.label || "";

    //         let mapped_data = {
    //             sku: item.product_info.sku,
    //             sku_count: item.product_info.sku_count,
    //             description: item.product_info.description,
    //             product_category: item.product_info.product_category,
    //             manufacturer_country: item.product_info.manufacturer_country,
    //             manufacturer_country_code: item.product_info.manufacturer_country_code,
    //             hsn_code: item.product_info.hsn_code,
    //             price: item.product_info.price,
    //             sales_invoice: item.sales_invoice,
    //             box: parcel_label
    //         };

    //         let child = frm.add_child("custom_item_box_mapping");
    //         Object.keys(mapped_data).forEach(key => {
    //             child[key] = mapped_data[key];
    //         });

    //         result_html += `<pre>${JSON.stringify(mapped_data, null, 2)}</pre>`;
    //     });

    //     frm.refresh_field("custom_item_box_mapping");
    //     frm.save("Update");

    //     dialog.$wrapper.find('#item-box-mapping-result').html(`
            
    //         <div class="text-success">All items mapped successfully!</div>
    //     `);
    // });
    dialog.$wrapper.find('#map-all-btn').on('click', function () {
        let result_html = "";
        let duplicates = [];
        all_items.forEach((item, idx) => {
            let parcel_idx = dialog.$wrapper.find(`.parcel-select[data-idx="${idx}"]`).val();
            let parcel_label = parcel_options[parcel_idx]?.label || "";

            let mapped_data = {
                sku: item.product_info.sku,
                sku_count: item.product_info.sku_count,
                description: item.product_info.description,
                product_category: item.product_info.product_category,
                manufacturer_country: item.product_info.manufacturer_country,
                manufacturer_country_code: item.product_info.manufacturer_country_code,
                hsn_code: item.product_info.hsn_code,
                price: item.product_info.price,
                sales_invoice: item.sales_invoice,
                box: parcel_label
            };

            // Check for duplicate mapping in custom_item_box_mapping
            let already_mapped = (frm.doc.custom_item_box_mapping || []).some(row =>
                row.sales_invoice === mapped_data.sales_invoice && row.sku === mapped_data.sku
            );

            if (already_mapped) {
                duplicates.push(`${mapped_data.sales_invoice} - ${mapped_data.sku}`);
                return; // Skip adding duplicate
            }

            let child = frm.add_child("custom_item_box_mapping");
            Object.keys(mapped_data).forEach(key => {
                child[key] = mapped_data[key];
            });

            result_html += `<pre>${JSON.stringify(mapped_data, null, 2)}</pre>`;
        });

        frm.refresh_field("custom_item_box_mapping");
        frm.save("Update");

        let message = `<div class="text-success">All items mapped successfully!</div>`;
        if (duplicates.length > 0) {
            message += `<div class="text-danger mt-2">Skipped duplicates:<br>${duplicates.join('<br>')}</div>`;
        }

        dialog.$wrapper.find('#item-box-mapping-result').html(message);
    });
}


