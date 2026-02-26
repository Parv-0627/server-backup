frappe.listview_settings['Shipment'] = {
    
    onload: function(listview) {

        let getAppointment = listview.page.add_inner_button(__('Get Appointment Details'), async function() {
            check_selection(listview)
            const selected = listview.get_checked_items();
            const uncreated = selected.filter(item => !item.awb_number);
            if (uncreated.length > 0) {
                frappe.throw(__('All selected Shipments must be created in clickpost.'));
            }

            for (const frm of selected) {
                try{
                    get_appointment(frm)
                    listview.refresh();
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
            'color': 'white',
        });

        // let createShipment = listview.page.add_inner_button(__('Create Shipment'), async function() {
        //     check_selection(listview)
        //     const selected = listview.get_checked_items();
        //     const created = selected.filter(item => item.awb_number);
        //     if (created.length > 0) {
        //         frappe.throw(__('All selected Shipments must not have AWB Number.'));
        //     }

        //     for (const frm of selected) {
        //         try{
        //             create_shipment(frm)
        //         }catch (error) {
        //             frappe.msgprint({
        //                 title: __('Error'),
        //                 indicator: 'red',
        //                 message: __('Failed to get create shipment for {0}: {1}', [frm.name, error.message])
        //             });
        //         }
        //     }
        // }).css({
        //     'background-color': 'blue', 
        //     'color': 'white',
        // });



        getAppointment.hide()
        // createShipment.hide()
        listview.$page.on('change', '.list-row-checkbox', function() {
            const selected = listview.get_checked_items();
            if (selected.length > 0){
                getAppointment.show()
                // createShipment.show()
            }else{
                getAppointment.hide()
                // createShipment.hide()
            }
        });
        
    }
};


async function create_shipment(frm){
    await frappe.call({
        method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.custom_scripts.shipment.create_clickpost_shipment_api',
        args: {
            'name': frm.name  // Convert to string for API call if needed
        },
        freeze: freeze,
        freeze_message: freeze_message,
        callback: function(r) {
            if(r.message.success){
                frappe.msgprint({
                    title: "Clickpost Shipment Creation",
                    indicator: "green",
                    message: (`Clickpost shipment successfully created for ${frm.name}`)
                });
                frm.reload_doc()
            }
        }
    });
}

function check_selection(listview){
    const selected = listview.get_checked_items();

    if (selected.length === 0) {
        frappe.msgprint(__('Please select at least one Shipment.'));
        return;
    }

    // Check if all selected Shipments are submitted
    const unsubmitted = selected.filter(item => item.docstatus !== 1);
    if (unsubmitted.length > 0) {
        frappe.throw(__('All selected Shipments must be submitted.'));
    }
}

async function get_appointment(frm){
    
    frappe.call({
        method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment.get_appointment',
        args: {
            "awb_number": frm.awb_number,
            "account_code": frm.custom_carrier_partner_name,
            "courier_partner_id": frm.custom_carrier_partner_id
        },
        freeze: true,
        freeze_message: __('Getting Appointment Details...'),
        callback: async function(r) {
            if(r.message.response.appointment_start_time) {
                const result = r.message.response;
                const update_data = {
                    custom_start_time: frappeDatetime(result.appointment_start_time),
                    custom_end_time: frappeDatetime(result.appointment_end_time),
                    reason_for_appointment: result.reason_for_appointment_change

                };
                await frappe.db.set_value('Shipment', frm.name, update_data);

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
                                        doctype: 'Shipment',
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
                        custom_appointment_document: links.join("<br>"),
                    };
                    await frappe.db.set_value('Shipment', frm.name, update_attachment);
                    frappe.msgprint({
                        title: __('Success'),
                        indicator: 'green',
                        message: __(`Appointment details updated successfully for ${frm.name}`)
                    });
                    // frm.refresh();
                    
                } else {
                    const update_attachment = {
                        custom_appointment_document: "No appointment documents available",
                    };
                    await frappe.db.set_value('Shipment', frm.name, update_attachment);
                    frappe.show_alert(
                       `No appointment documents found for ${frm.name}`, 5
                    );
                }

                // await frm.save("Update");
                // await frm.reload_doc();
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
    let match = datetime.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})[+-]\d{4}$/);
    if (!match) throw new Error('Invalid datetime format');

    const [_, year, month, day, hour, minute, second] = match;
    return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
}