frappe.listview_settings['AWB Registration'] = {
    onload: function(listview) {
        let getAppointment = listview.page.add_inner_button(__('Create AWB Registration'), async function() {
            // Get selected AWB Registrations
            const selected = listview.get_checked_items();

            if (selected.length === 0) {
                frappe.msgprint(__('Please select at least one AWB Registration.'));
                return;
            }

            // Check if all selected AWB Registrations are submitted
            const unsubmitted = selected.filter(item => item.docstatus !== 1);
            if (unsubmitted.length > 0) {
                frappe.throw(__('All selected AWB Registrations must be submitted.'));
            }

            const createdAWB = selected.filter(item => item.shipment_id);
            if (createdAWB.length > 0) {
                frappe.throw(__('AWB Registration already created for {0}', [createdAWB.map(item => item.name).join(', ')]));
            }

            // Create AWB on ClickPost for each selected AWB Registration
            for (const item of selected) {
                try {
                    // Prepare shipment data
                    const shipment_data = await prepare_shipment_payload(item) || {};
            
                    // Call the API to create ClickPost AWB Order
                    const response = await frappe.call({
                        method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment.create_clickpost_awb_order',
                        args: {
                            shipment_data: JSON.stringify(shipment_data) // Convert to string for API call if needed
                        },
                        freeze: true,
                        freeze_message: __('Creating ClickPost AWB Order...')
                    });
            
                    // Handle API response
                    if (response.message && response.message.status === 'success') {
                        const meta = response.message.response.meta;
            
                        if (meta.success === true) {
                            const update_data = {
                                shipment_id: response.message.response.result.tracking_id
                            };
                            
                            // Update the Shipment document
                            const exists = await frappe.db.exists('AWB Registration', item.name);
                            if (!exists) {
                                frappe.msgprint({
                                    title: __('Error'),
                                    indicator: 'red',
                                    message: __('AWB Registration {0} not found.', [item.name])
                                });
                                continue;
                            }
            
                            await frappe.db.set_value('AWB Registration', item.name, update_data);
            
                            frappe.msgprint({
                                title: __('Success'),
                                indicator: 'green',
                                message: __('ClickPost AWB order created successfully')
                            });
                        } else {
                            frappe.msgprint({
                                title: __('Error'),
                                indicator: 'red',
                                message: meta.error || meta.message
                            });
                        }
                    } else {
                        frappe.msgprint({
                            title: __('Error'),
                            indicator: 'red',
                            message: response.message.message || __('Failed to create ClickPost AWB Order')
                        });
                    }
                } catch (error) {
                    frappe.msgprint({
                        title: __('Error'),
                        indicator: 'red',
                        message: __('Failed to create AWB for {0}: {1}', [item.name, error.message])
                    });
                }
            }

            // Refresh the list view after processing
            listview.refresh();
        }).css({
            'background-color': 'rgb(37, 114, 208)', 
            'color': 'white'
        });
        let createShipment = listview.page.add_inner_button(__('Get Appointment Details'), async function() {
            const selected = listview.get_checked_items();

            if (selected.length === 0) {
                frappe.msgprint(__('Please select at least one AWB Registration.'));
                return;
            }

            // Check if all selected AWB Registrations are submitted
            const unsubmitted = selected.filter(item => item.docstatus !== 1);
            if (unsubmitted.length > 0) {
                frappe.throw(__('All selected AWB Registrations must be submitted.'));
            }

            const uncreated = selected.filter(item => !item.shipment_id);
            if (uncreated.length > 0) {
                frappe.throw(__('All selected AWB Registrations must be created in clickpost.'));
            }

            for (const frm of selected) {
                try{
                    get_appointment(frm)
                }catch (error) {
                    frappe.msgprint({
                        title: __('Error'),
                        indicator: 'red',
                        message: __('Failed to get appointment details for {0}: {1}', [frm.name, error.message])
                    });
                }
            }
        }).css({
            'background-color': 'Purple', 
            'color': 'white'
        });

        getAppointment.hide()
        createShipment.hide()
        listview.$page.on('change', '.list-row-checkbox', function() {
            const selected = listview.get_checked_items();
            if (selected.length > 0){
                getAppointment.show()
                createShipment.show()
            }else{
                getAppointment.hide()
                createShipment.hide()
            }
        });
    }
};


async function prepare_shipment_payload(item) {
    return {
        "shipment_info": {
            "reference_number": item.name,
            "waybill": item.awb_number,
            "courier_partner": item.carrier_partner_id,
            "account_code": item.carrier_account_name,
        }
    }      
}


async function get_appointment(frm){
    frappe.call({
        method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment.get_appointment',
        args: {
            "awb_number": frm.awb_number,
            "account_code": frm.carrier_account_name,
            "courier_partner_id": frm.carrier_partner_id
        },
        freeze: true,
        freeze_message: __('Getting Appointment Details...'),
        callback: async function(r) {
            if(r.message.response.appointment_start_time)  {
                const result = r.message.response;
                const update_data = {
                    start_time: frappeDatetime(result.appointment_start_time),
                    end_time: frappeDatetime(result.appointment_end_time),
                    reason_for_appointment: result.reason_for_appointment_change,
                    appointment_status: result.appointment_status,
                };
                await frappe.db.set_value('AWB Registration', frm.name, update_data);
                
                if (Array.isArray(result.appointment_documents) && result.appointment_documents.length > 0) {
                    let links = [];
                    for (let i = 0; i < result.appointment_documents.length; i++) {
                        const url = result.appointment_documents[i];
                        // Get file extension
                        const ext = url.split('?')[0].split('.').pop().toLowerCase();
                        const filename = `appointment_doc_${frm.name}_${i+1}.${ext}`;
                        try {
                            // Download and attach the file using your backend API
                            const attach_r = await new Promise((resolve, reject) => {
                                frappe.call({
                                    method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.utils.download_and_attach_file',
                                    args: {
                                        url: url,
                                        doctype: 'AWB Registration',
                                        docname: frm.name,
                                        filename: filename
                                    },
                                    freeze: true,
                                    freeze_message: __('Attaching appointment document...'),
                                    callback: function(r) {
                                        if (r.message && r.message.success && r.message.file_url) {
                                            // console.log(r.message.file_url)
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
                    const update_attachment = {
                        appointment_attachments: links.join("<br>"),
                        
                    };
                    await frappe.db.set_value('AWB Registration', frm.name, update_attachment);
                    
                    frappe.show_alert(
                       `Appointment details updated successfully for ${frm.name}`, 5
                    );
                } else {
                   const update_attachment = {
                        appointment_attachments: "No appointment documents found",
                        
                    };
                    await frappe.db.set_value('AWB Registration', frm.name, update_attachment);
                    frappe.show_alert(
                       `No appointment documents found for ${frm.name}`, 5
                    );
                }

               
            }else{
                frappe.msgprint({
                    title: __('Error'),
                    indicator: 'red',
                    message: __('Failed to get appointment details for {0}: {1}', [frm.name, r.message.response.meta.message.toString()])
                });
            }
            
        }
    });
}

function frappeDatetime(datetime) {
    // Check if it's in DD-MM-YYYY format
    let match = datetime.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})[+-]\d{4}$/);
    if (!match) throw new Error('Invalid datetime format');

    const [_, year, month, day, hour, minute, second] = match;
    return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
}