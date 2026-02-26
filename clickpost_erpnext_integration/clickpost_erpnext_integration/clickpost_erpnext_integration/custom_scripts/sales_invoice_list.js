frappe.listview_settings["Sales Invoice"] = {
    onload: function (listview) {
        listview.page.add_action_item(__('Create Shipment'), function() {
            const selected_docs = listview.get_checked_items();
            
            if (selected_docs.length === 0) {
                frappe.msgprint(__('Please select at least one Sales Invoice'));
                return;
            }
            
            // Check if all selected invoices are submitted
            const all_submitted = selected_docs.every(doc => doc.docstatus === 1);
            if (!all_submitted) {
                frappe.msgprint(__('All selected Sales Invoices must be submitted'));
                return;
            }
            
            // First, check if any of the selected invoices are already used in shipments
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Shipment',
                    filters: [
                        ['Sales Invoice Shipment', 'sales_invoice', 'in', selected_docs.map(doc => doc.name)],
                        ['docstatus', '!=', 2]
                    ],
                    fields: ['name']
                },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        
                        // Some invoices are already used in shipments
                        const used_shipments = r.message;
                        let promises = [];
                        used_shipments.forEach(shipment => {
                            // Get the full shipment document with child table data
                            promises.push(
                                new Promise((resolve) => {
                                    frappe.call({
                                        method: 'frappe.client.get',
                                        args: {
                                            doctype: 'Shipment',
                                            name: shipment.name
                                        },
                                        callback: function(result) {
                                            if (result.message && result.message.custom_sales_invoice) {
                                                // Find which of our selected invoices are in this shipment
                                                const invoices_in_shipment = [];
                                                result.message.custom_sales_invoice.forEach(row => {
                                                    if (selected_docs.some(doc => doc.name === row.sales_invoice)) {
                                                        invoices_in_shipment.push({
                                                            invoice: row.sales_invoice,
                                                            shipment: shipment.name
                                                        });
                                                    }
                                                });
                                                resolve(invoices_in_shipment);
                                            } else {
                                                resolve([]);
                                            }
                                        }
                                    });
                                })
                            );
                        });
                        
                        // Wait for all the shipment data to be fetched
                        Promise.all(promises).then(results => {
                            // Flatten the array of arrays
                            const used_invoices = [].concat(...results);
                                                        
                            if (used_invoices.length > 0) {
                                let message = __('The following invoices are already used in shipments:') + '<br>';
                                used_invoices.forEach(item => {
                                    message += `${item.invoice} (${__('Shipment')}: <a href="/app/shipment/${item.shipment}">${item.shipment}</a>)<br>`;
                                });
                                frappe.msgprint({
                                    title: __('Invoices Already in Shipments'),
                                    indicator: 'red',
                                    message: message
                                });
                                return;
                            } else {
                                // If no selected invoices are used in shipments, proceed with creating a new one
                                createShipment();
                            }
                        });
                    } else {
                        // If no shipments were found, proceed with creating a new one
                        createShipment();
                    }
                    
                   
                }
            });
             //create shipment function
            async function createShipment(){
                frappe.call({
                    method: 'frappe.client.get_list',
                    args: {
                        doctype: 'Sales Invoice',
                        filters: {
                            'name': ['in', selected_docs.map(doc => doc.name)],
                        },
                        fields: ['name', 'customer', 'docstatus', 'grand_total', 'posting_date', 'shipping_address_name', 'dispatch_address_name', 'company_address', 'ewaybill', 'transporter']
                    },
                    callback: async function(response) {
                        const invoices = response.message;
                        
                        // Check if all invoices have the same customer
                        const customers = [...new Set(invoices.map(invoice => invoice.customer))];
                        if (customers.length > 1) {
                            frappe.msgprint(__('All selected Sales Invoices must belong to the same customer'));
                            return;
                        }


                        const transporters = [...new Set(invoices.map(invoice => invoice.transporter))];
                        
                        if (transporters.length > 1) {
                            frappe.msgprint(__('All selected Sales Invoices must have the same transporter'));
                            return;
                        }

                        const carrier_partner = await frappe.db.get_value('Carrier Partner', { 'supplier': transporters[0] }, 'name');

                        // Create a new shipment
                        const customer = customers[0];

                         // Check if all invoices have the same company address
                        const company_addresses = [...new Set(invoices.map(invoice => invoice.shipping_address_name))];
                    
                        if (company_addresses.length > 1) {
                            frappe.msgprint(__('All selected Sales Invoices must have the same Shipping address'));
                            return;
                        }
                        
                        // Check if all invoices have the same shipping address
                        const dispatch_addresses = [...new Set(invoices.map(invoice => invoice.dispatch_address_name))];
                        if (dispatch_addresses.length > 1) {
                            frappe.msgprint(__('All selected Sales Invoices must have the same Dispatch address'));
                            return;
                        }

                         // Calculate the total value of goods from all invoices
                        const value_of_goods = invoices.reduce((total, invoice) => {
                            return total + flt(invoice.grand_total);
                        }, 0);

                        // Fetch e-waybill expiry dates for each invoice
                        const ewaybill_expiry_dates = await Promise.all(
                            invoices.map(invoice => {
                                return frappe.db.get_value('e-Waybill Log', { reference_name: invoice.sales_invoice, reference_doctype: "Sales Invoice" }, 'valid_upto')
                                    .then(r => r.message ? r.message.valid_upto : null);
                            })
                        );
                        // console.log(ewaybill_expiry_dates)
                        
                        // Create a new document and manually set values after it's loaded
                        frappe.run_serially([
                            () => frappe.new_doc('Shipment'),
                            (doc) => {
                                // Set the customer
                                cur_frm.set_value('delivery_customer', customer);
                                cur_frm.set_value('delivery_address_name', company_addresses[0]);
                                cur_frm.set_value('pickup_address_name', dispatch_addresses[0]);
                                cur_frm.set_value('custom_carrier_partner', carrier_partner.message.name);
                                cur_frm.set_value('value_of_goods', value_of_goods);

                                // Add each invoice to the child table with additional fields
                                invoices.forEach(async (invoice, index) => {
                                    const child = cur_frm.add_child('custom_sales_invoice');
                                    child.sales_invoice = invoice.name;
                                    child.grand_total = invoice.grand_total;
                                    child.posting_date = invoice.posting_date;
                                    child.e_waybill_number = invoice.ewaybill;
                                    // console.log(await getEwaybillExpiryDate(invoice.name))
                                    child.e_waybill_expiry_date =invoice.ewaybill ? await getEwaybillExpiryDate(invoice.name) : null; // Set e-waybill expiry date
                                });
                                
                                // Refresh the child table
                                cur_frm.refresh_field('custom_sales_invoice');
                                cur_frm.refresh_field('delivery_address_name');
                                cur_frm.refresh_field('pickup_address_name');
                                cur_frm.refresh_field('custom_carrier_partner');
                                cur_frm.refresh_field('value_of_goods');
                            }
                        ]);
                    }
                });
            }
        });
        

        async function getEwaybillExpiryDate(invoiceName) {
            const result = await frappe.db.get_value(
                'e-Waybill Log',
                { reference_name: invoiceName, reference_doctype: "Sales Invoice" },
                'valid_upto'
            );
            return result.message ? result.message.valid_upto : null;
        }
    }
    
}

