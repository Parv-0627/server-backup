// Copyright (c) 2025, nasirucode and contributors
// For license information, please see license.txt

frappe.ui.form.on("AWB Registration", {
    address_query: function (frm, link_doctype, link_name, is_your_company_address) {
		return {
			query: "frappe.contacts.doctype.address.address.address_query",
			filters: {
				link_doctype: link_doctype,
				link_name: link_name,
				is_your_company_address: is_your_company_address,
			},
		};
	},
	contact_query: function (frm, link_doctype, link_name) {
		return {
			query: "frappe.contacts.doctype.contact.contact.contact_query",
			filters: {
				link_doctype: link_doctype,
				link_name: link_name,
			},
		};
	},
    add_template: function(frm) {        
        if (frm.doc.parcel_template) {
            frappe.model.with_doc("Shipment Parcel Template", frm.doc.parcel_template, () => {
                let parcel_template = frappe.model.get_doc(
                    "Shipment Parcel Template",
                    frm.doc.parcel_template
                );
                // if (frm.doc.shipment_parcel && frm.doc.shipment_parcel.length > 0) {
                //     frm.doc.shipment_parcel.pop();
                // }
                let row = frappe.model.add_child(frm.doc, "Shipment Parcel", "shipment_parcel");
                row.length = parcel_template.length;
                row.width = parcel_template.width;
                row.height = parcel_template.height;
                row.weight = parcel_template.weight;
                
                // Set the custom_parcel field to the name of the parcel template
                row.custom_parcel = frm.doc.parcel_template;
                console.log(row)
                
                frm.refresh_fields("shipment_parcel");
                frm.set_value('parcel_template', '');
            });
        }
        
    },
    setup: function(frm) {
        frm.set_query("carrier_partner", function() {
            return {
                "filters": {
                    "active": 1
                }
            };
        });
        frm.set_query("sales_invoice", "sales_invoice", function() {
            return {
                "filters": [
                    ["Sales Invoice", "docstatus", "=", 1],
                    
                    ["Sales Invoice", "custom_shipment_reference", "=", ""],
                ],
                // "query": "clickpost_erpnext_integration.clickpost_erpnext_integration.utils.get_unshipped_sales_invoices"
            };
        });
    },
    onload: function (frm) {
		frm.set_query("delivery_address_name", () => {
			let delivery_to = `delivery_${frappe.model.scrub(frm.doc.delivery_to_type)}`;
			return frm.events.address_query(
				frm,
				frm.doc.delivery_to_type,
				frm.doc[delivery_to],
				frm.doc.delivery_to_type === "Company" ? 1 : 0
			);
		});
		frm.set_query("pickup_address_name", () => {
			let pickup_from = `pickup_${frappe.model.scrub(frm.doc.pickup_from_type)}`;
			return frm.events.address_query(
				frm,
				frm.doc.pickup_from_type,
				frm.doc[pickup_from],
				frm.doc.pickup_from_type === "Company" ? 1 : 0
			);
		});
		// frm.set_query("delivery_contact_name", () => {
		// 	let delivery_to = `delivery_${frappe.model.scrub(frm.doc.delivery_to_type)}`;
		// 	return frm.events.contact_query(frm, frm.doc.delivery_to_type, frm.doc[delivery_to]);
		// });
		// frm.set_query("pickup_contact_name", () => {
		// 	let pickup_from = `pickup_${frappe.model.scrub(frm.doc.pickup_from_type)}`;
		// 	return frm.events.contact_query(frm, frm.doc.pickup_from_type, frm.doc[pickup_from]);
		// });
		frm.set_query("delivery_note", "shipment_delivery_note", function () {
			let customer = "";
			if (frm.doc.delivery_to_type == "Customer") {
				customer = frm.doc.delivery_customer;
			}
			if (frm.doc.delivery_to_type == "Company") {
				customer = frm.doc.delivery_company;
			}
			if (customer) {
				return {
					filters: {
						customer: customer,
						docstatus: 1,
						status: ["not in", ["Cancelled"]],
					},
				};
			}
		});
	},
	refresh: async function(frm) {
        const doc = frm.doc;
        $("div[data-fieldname=pickup_address] > div > .clearfix").hide();
		$("div[data-fieldname=pickup_contact] > div > .clearfix").hide();
		$("div[data-fieldname=delivery_address] > div > .clearfix").hide();
		$("div[data-fieldname=delivery_contact] > div > .clearfix").hide();

        if(doc.amended_from && frm.is_new()) {
            frm.set_value("shipment_id", "")
            frm.set_value("status", "Draft")
            frm.set_value("clickpost_status", "")
        }

        if(frm.is_new() && frm.doc.value_of_good){
            frm.set_value("cod_value", frm.doc.value_of_good)
        }
       
        if(doc.docstatus === 1 && !doc.shipment_id) {  
            frm.add_custom_button(__('Create AWB Registration'), function() {
                // Button click action here
                create_clickpost_awb(frm)
            }).css({
                'background-color': 'purple', 
                'color': 'white'
            });

        }
        if(doc.docstatus === 1 && doc.shipment_id && doc.awb_number && doc.clickpost_status !== "Cancelled") {
            
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
        if (doc.docstatus === 1 && doc.shipment_id && doc.awb_number && doc.clickpost_status !== "Cancelled" && doc.tracking_status === "Delivered") {
            frm.add_custom_button(__('Proof Of Delivery'), function() {
                // Button click action here
                proof_of_delivery(frm)
            }).css({
                'background-color': 'rgb(37, 114, 208)', 
                'color': 'white'
            });
        }
 
    },
    before_save: function (frm) {
		let delivery_to = `delivery_${frappe.model.scrub(frm.doc.delivery_to_type)}`;
		frm.set_value("delivery_to", frm.doc[delivery_to]);
		let pickup_from = `pickup_${frappe.model.scrub(frm.doc.pickup_from_type)}`;
		frm.set_value("pickup", frm.doc[pickup_from]);
	},
	set_pickup_company_address: function (frm) {
		frappe.db.get_value(
			"Address",
			{
				address_title: frm.doc.pickup_company,
				is_your_company_address: 1,
			},
			"name",
			(r) => {
				frm.set_value("pickup_address_name", r.name);
			}
		);
	},
	set_delivery_company_address: function (frm) {
		frappe.db.get_value(
			"Address",
			{
				address_title: frm.doc.delivery_company,
				is_your_company_address: 1,
			},
			"name",
			(r) => {
				frm.set_value("delivery_address_name", r.name);
			}
		);
	},
	pickup_from_type: function (frm) {
		if (frm.doc.pickup_from_type == "Company") {
			frm.set_value("pickup_company", frappe.defaults.get_default("company"));
			frm.set_value("pickup_customer", "");
			frm.set_value("pickup_supplier", "");
		} else {
			frm.trigger("clear_pickup_fields");
		}
		if (frm.doc.pickup_from_type == "Customer") {
			frm.set_value("pickup_company", "");
			frm.set_value("pickup_supplier", "");
		}
		if (frm.doc.pickup_from_type == "Supplier") {
			frm.set_value("pickup_customer", "");
			frm.set_value("pickup_company", "");
		}
	},
	delivery_to_type: function (frm) {
		if (frm.doc.delivery_to_type == "Company") {
			frm.set_value("delivery_company", frappe.defaults.get_default("company"));
			frm.set_value("delivery_customer", "");
			frm.set_value("delivery_supplier", "");
		} else {
			frm.trigger("clear_delivery_fields");
		}
		if (frm.doc.delivery_to_type == "Customer") {
			frm.set_value("delivery_company", "");
			frm.set_value("delivery_supplier", "");
		}
		if (frm.doc.delivery_to_type == "Supplier") {
			frm.set_value("delivery_customer", "");
			frm.set_value("delivery_company", "");
			frm.toggle_display("shipment_delivery_note", false);
		} else {
			frm.toggle_display("shipment_delivery_note", true);
		}
	},
	delivery_address_name: function (frm) {
		if (frm.doc.delivery_to_type == "Company") {
			erpnext.utils.get_address_display(frm, "delivery_address_name", "delivery_address", true);
		} else {
			erpnext.utils.get_address_display(frm, "delivery_address_name", "delivery_address", false);
		}
	},
	pickup_address_name: function (frm) {
		if (frm.doc.pickup_from_type == "Company") {
			erpnext.utils.get_address_display(frm, "pickup_address_name", "pickup_address", true);
		} else {
			erpnext.utils.get_address_display(frm, "pickup_address_name", "pickup_address", false);
		}
	},
	get_contact_display: function (frm, contact_name, contact_type) {
		frappe.call({
			method: "frappe.contacts.doctype.contact.contact.get_contact_details",
			args: { contact: contact_name },
			callback: function (r) {
				if (r.message) {
					if (!(r.message.contact_email && (r.message.contact_phone || r.message.contact_mobile))) {
						if (contact_type == "Delivery") {
							frm.set_value("delivery_contact_name", "");
							frm.set_value("delivery_contact", "");
						} else {
							frm.set_value("pickup_contact_name", "");
							frm.set_value("pickup_contact", "");
						}
						frappe.throw(
							__("Email or Phone/Mobile of the Contact are mandatory to continue.") +
								"</br>" +
								__("Please set Email/Phone for the contact") +
								` <a href='/app/contact/${contact_name}'>${contact_name}</a>`
						);
					}
					let contact_display = r.message.contact_display;
					if (r.message.contact_email) {
						contact_display += "<br>" + r.message.contact_email;
					}
					if (r.message.contact_phone) {
						contact_display += "<br>" + r.message.contact_phone;
					}
					if (r.message.contact_mobile && !r.message.contact_phone) {
						contact_display += "<br>" + r.message.contact_mobile;
					}
					if (contact_type == "Delivery") {
						frm.set_value("delivery_contact", contact_display);
						if (r.message.contact_email) {
							frm.set_value("delivery_contact_email", r.message.contact_email);
						}
					} else {
						frm.set_value("pickup_contact", contact_display);
						if (r.message.contact_email) {
							frm.set_value("pickup_contact_email", r.message.contact_email);
						}
					}
				}
			},
		});
	},
	delivery_contact_name: function (frm) {
		if (frm.doc.delivery_contact_name) {
			frm.events.get_contact_display(frm, frm.doc.delivery_contact_name, "Delivery");
		}
	},
	pickup_contact_name: function (frm) {
		if (frm.doc.pickup_contact_name) {
			frm.events.get_contact_display(frm, frm.doc.pickup_contact_name, "Pickup");
		}
	},
	pickup_contact_person: function (frm) {
		if (frm.doc.pickup_contact_person) {
			frappe.call({
				method: "erpnext.stock.doctype.shipment.shipment.get_company_contact",
				args: { user: frm.doc.pickup_contact_person },
				callback: function ({ message }) {
					const r = message;
					let contact_display = `${r.first_name} ${r.last_name}`;
					if (r.email) {
						contact_display += `<br>${r.email}`;
						frm.set_value("pickup_contact_email", r.email);
					}
					if (r.phone) {
						contact_display += `<br>${r.phone}`;
					}
					if (r.mobile_no && !r.phone) {
						contact_display += `<br>${r.mobile_no}`;
					}
					frm.set_value("pickup_contact", contact_display);
				},
			});
		} else {
			if (frm.doc.pickup_from_type === "Company") {
				frappe.call({
					method: "erpnext.stock.doctype.shipment.shipment.get_company_contact",
					args: { user: frappe.session.user },
					callback: function ({ message }) {
						const r = message;
						let contact_display = `${r.first_name} ${r.last_name}`;
						if (r.email) {
							contact_display += `<br>${r.email}`;
							frm.set_value("pickup_contact_email", r.email);
						}
						if (r.phone) {
							contact_display += `<br>${r.phone}`;
						}
						if (r.mobile_no && !r.phone) {
							contact_display += `<br>${r.mobile_no}`;
						}
						frm.set_value("pickup_contact", contact_display);
					},
				});
			}
		}
	},
	set_company_contact: function (frm, delivery_type) {
		frappe.db.get_value(
			"User",
			{ name: frappe.session.user },
			["full_name", "last_name", "email", "phone", "mobile_no"],
			(r) => {
				if (!(r.last_name && r.email && (r.phone || r.mobile_no))) {
					if (delivery_type == "Delivery") {
						frm.set_value("delivery_company", "");
						frm.set_value("delivery_contact", "");
					} else {
						frm.set_value("pickup_company", "");
						frm.set_value("pickup_contact", "");
					}
					frappe.throw(
						__("Last Name, Email or Phone/Mobile of the user are mandatory to continue.") +
							"</br>" +
							__("Please first set Last Name, Email and Phone for the user") +
							` <a href="/app/user/${frappe.session.user}">${frappe.session.user}</a>`
					);
				}
				let contact_display = r.full_name;
				if (r.email) {
					contact_display += "<br>" + r.email;
				}
				if (r.phone) {
					contact_display += "<br>" + r.phone;
				}
				if (r.mobile_no && !r.phone) {
					contact_display += "<br>" + r.mobile_no;
				}
				if (delivery_type == "Delivery") {
					frm.set_value("delivery_contact", contact_display);
					if (r.email) {
						frm.set_value("delivery_contact_email", r.email);
					}
				} else {
					frm.set_value("pickup_contact", contact_display);
					if (r.email) {
						frm.set_value("pickup_contact_email", r.email);
					}
				}
			}
		);
		frm.set_value("pickup_contact_person", frappe.session.user);
	},
	pickup_company: function (frm) {
		if (frm.doc.pickup_from_type == "Company" && frm.doc.pickup_company) {
			frm.trigger("set_pickup_company_address");
			frm.events.set_company_contact(frm, "Pickup");
		}
	},
	delivery_company: function (frm) {
		if (frm.doc.delivery_to_type == "Company" && frm.doc.delivery_company) {
			frm.trigger("set_delivery_company_address");
			frm.events.set_company_contact(frm, "Delivery");
		}
	},
	delivery_customer: function (frm) {
		frm.trigger("clear_delivery_fields");
		if (frm.doc.delivery_customer) {
			frm.events.set_address_name(frm, "Customer", frm.doc.delivery_customer, "Delivery");
			frm.events.set_contact_name(frm, "Customer", frm.doc.delivery_customer, "Delivery");
		}
	},
	delivery_supplier: function (frm) {
		frm.trigger("clear_delivery_fields");
		if (frm.doc.delivery_supplier) {
			frm.events.set_address_name(frm, "Supplier", frm.doc.delivery_supplier, "Delivery");
			frm.events.set_contact_name(frm, "Supplier", frm.doc.delivery_supplier, "Delivery");
		}
	},
	pickup_customer: function (frm) {
		if (frm.doc.pickup_customer) {
			frm.events.set_address_name(frm, "Customer", frm.doc.pickup_customer, "Pickup");
			frm.events.set_contact_name(frm, "Customer", frm.doc.pickup_customer, "Pickup");
		}
	},
	pickup_supplier: function (frm) {
		if (frm.doc.pickup_supplier) {
			frm.events.set_address_name(frm, "Supplier", frm.doc.pickup_supplier, "Pickup");
			frm.events.set_contact_name(frm, "Supplier", frm.doc.pickup_supplier, "Pickup");
		}
	},
	set_address_name: function (frm, ref_doctype, ref_docname, delivery_type) {
		frappe.call({
			method: "erpnext.stock.doctype.shipment.shipment.get_address_name",
			args: {
				ref_doctype: ref_doctype,
				docname: ref_docname,
			},
			callback: function (r) {
				if (r.message) {
					if (delivery_type == "Delivery") {
						frm.set_value("delivery_address_name", r.message);
					} else {
						frm.set_value("pickup_address_name", r.message);
					}
				}
			},
		});
	},
	set_contact_name: function (frm, ref_doctype, ref_docname, delivery_type) {
		frappe.call({
			method: "erpnext.stock.doctype.shipment.shipment.get_contact_name",
			args: {
				ref_doctype: ref_doctype,
				docname: ref_docname,
			},
			callback: function (r) {
				if (r.message) {
					if (delivery_type == "Delivery") {
						frm.set_value("delivery_contact_name", r.message);
					} else {
						frm.set_value("pickup_contact_name", r.message);
					}
				}
			},
		});
	},
    pickup_date: function (frm) {
		if (frm.doc.pickup_date < frappe.datetime.get_today()) {
			frappe.throw(__("Pickup Date cannot be before this day"));
		}
	},
	clear_pickup_fields: function (frm) {
		let fields = [
			"pickup_address_name",
			"pickup_contact_name",
			"pickup_address",
			"pickup_contact",
			"pickup_contact_email",
			"pickup_contact_person",
		];
		for (let field of fields) {
			frm.set_value(field, "");
		}
	},
	clear_delivery_fields: function (frm) {
		let fields = [
			"delivery_address_name",
			"delivery_contact_name",
			"delivery_address",
			"delivery_contact",
			"delivery_contact_email",
		];
		for (let field of fields) {
			frm.set_value(field, "");
		}
	},
	remove_email_row: function (frm, table, fieldname) {
		$.each(frm.doc[table] || [], function (i, detail) {
			if (detail.email === fieldname) {
				cur_frm.get_field(table).grid.grid_rows[i].remove();
			}
		});
	},
    carrier_partner_id: function(frm) {
        if(frm.doc.carrier_partner_id && frm.doc.carrier_account_name) {
            frm.set_value('carrier_partner', `${frm.doc.carrier_partner_id}-${frm.doc.carrier_account_name}`);    
        }
    },
    carrier_account_name: function(frm) {
        if(frm.doc.carrier_partner_id && frm.doc.carrier_account_name) {
            frm.set_value('carrier_partner', `${frm.doc.carrier_partner_id}-${frm.doc.carrier_account_name}`);    
        }
    },
    on_submit: function(frm) {
        const required_fields = [
            { field: 'carrier_partner', label: 'Carrier Partner' },
            { field: 'carrier_partner_id', label: 'Carrier Partner ID' },
            { field: 'carrier_account_name', label: 'Carrier Account Name' },
        ];
        
        let missing_fields = [];
        
        required_fields.forEach(field => {
            if (!frm.doc[field.field]) {
                missing_fields.push(field.label);
            }
        });
        
        
        if (missing_fields.length > 0) {
            frappe.throw(__(`The following fields are required when uploading to ClickPost, please fille them before submnitting: ${missing_fields.join(', ')}`));
        }
        // Update all linked Sales Invoices with the shipment reference
        // frm.set_value("status", "Submitted")
        update_sales_invoice_shipment_reference(frm);
        // frm.save("Update");

    },
   
    delivery_customer: function(frm) {
        // Refresh the sales_invoice table when delivery_customer changes
        frm.refresh_field('sales_invoice');
    }
});

//Create AWb Registration
async function create_clickpost_awb(frm) {
    let shipment_data = await prepare_shipment_payload(frm) || {};
    console.log(shipment_data)

    frappe.call({
        method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment.create_clickpost_awb_order',
        args: {
            'shipment_data': JSON.stringify(shipment_data)  // Convert to string for API call if needed
        },
        freeze: true,
        freeze_message: __('Creating ClickPost AWB Order...'),
        callback: function(r) {
            if(r.message && r.message.status === 'success') {
                if(r.message.response.meta.success == true) {
                    

                    let update_data = {
                       'shipment_id': r.message.response.result.tracking_id
                    };
                  
                    frappe.db.set_value('AWB Registration', frm.doc.name, update_data)
                    .then(() => {

                        frm.reload_doc();
                        
                        frappe.msgprint({
                            title: __('Success'),
                            indicator: 'green',
                            message: __('ClickPost AWB Registration created successfully')
                        });
                    });
                }else{
                    frappe.msgprint({
                        title: __('Error'),
                        indicator: 'red',
                        message: r.message.response.meta.error || r.message.response.meta.message
                    });
                }
                
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    indicator: 'red',
                    message: r.message.message || __('Failed to create ClickPost AWB Registration')
                });
            }
        }
    });
}

async function prepare_shipment_payload(frm) {
    let pickup_date = frm.doc.pickup_date;
    let pickup_time = frm.doc.pickup_from;
    let formatted_pickup_time = "";
    if (pickup_time && pickup_date) {
        formatted_pickup_time = pickup_date 
        ? moment(
            pickup_time 
                ? `${pickup_date} ${pickup_time}` 
                : pickup_date, 
            pickup_time 
                ? 'YYYY-MM-DD hh:mm:ss' 
                : 'YYYY-MM-DD'
        ).format('YYYY-MM-DDThh:mm:ss')
        : moment().format('YYYY-MM-DDThh:mm:ss');
    }
    
    

    const pickup_address_details = await get_address_details(frm.doc.pickup_address_name) || {};
    const delivery_address_details = await get_address_details(frm.doc.delivery_address_name) || {};
    
    let pickup_info = {};

    // let enterprise_gstin = "";
    // // If location_code exists, only include that
   
    pickup_info.name= frm.doc.pickup_contact_person_name || "",
    pickup_info.phone= frm.doc.pickup_contact_phone || "",
    pickup_info.organisation= frm.doc.pickup_company || frm.doc.pickup_customer || frm.doc.pickup_supplier || "",
    pickup_info.email= frm.doc.pickup_contact_email || "",
    pickup_info.vendor_code= "",
    // pickup_info.time = formatted_pickup_time.toString() || "",
    // Otherwise include all the address details
    pickup_info.district = pickup_address_details.district || "";
    pickup_info.city = pickup_address_details.city || "";
    pickup_info.landmark = "";
    pickup_info.state = pickup_address_details.state || "";
    pickup_info.pincode = pickup_address_details.pincode || "";
    pickup_info.country = pickup_address_details.country || "IN";
    pickup_info.address_type = "";
    pickup_info.address = formatAddress(frm.doc.pickup_address) || "";
    enterprise_gstin = pickup_address_details.gstin || "";

    
    
    // // Do the same for drop_info
    let drop_info = {};

    let drop_info_name = "";
    if (frm.doc.delivery_contact_name) {
        drop_info_name = frm.doc.delivery_contact_name.split("-")[0] || frm.doc.delivery_contact_name || "";
    } 
    
    drop_info.name = drop_info_name;
    drop_info.phone = frm.doc.delivery_contact_phone || "";
    drop_info.email = frm.doc.delivery_contact_email || "";
    drop_info.organisation = frm.doc.delivery_customer || "";
    drop_info.vendor_code = "";
    // // Otherwise include all the address details
    drop_info.district = delivery_address_details.district || "";
    drop_info.address_type = "";
    drop_info.landmark = "";
    drop_info.city = delivery_address_details.city || "";
    drop_info.state = delivery_address_details.state || "";
    drop_info.pincode = delivery_address_details.pincode || "";
    drop_info.country = delivery_address_details.country || "IN";
    drop_info.address = formatAddress(frm.doc.delivery_address) || "";
    consignee_gstin = delivery_address_details.gstin || "";
    const purchase_order_info =  await get_purchase_order_info(frm) || {};

    return {
        "pickup_info": pickup_info,
        "drop_info": drop_info,
        "shipment_info": {
            "reference_number": frm.doc.name,
            "waybill": frm.doc.awb_number,
            "courier_partner": frm.doc.carrier_partner_id,
            "account_code": frm.doc.carrier_account_name,
            "description": frm.doc.description_of_content || "",
            "cod_value": frm.doc.order_type === "PREPAID" ? 0 : frm.doc.cod_value,
            "order_type": frm.doc.order_type,
            "order_id": "",
            "delivery_type": frm.doc.delivery_type || "",
            "weight": calculate_total_weight(frm) || 0,
            "invoice_info": get_invoice_info(frm) || {},
            "purchase_order_info": purchase_order_info || {},
            "box_info": get_box_info(frm) || {},
            "gst_info": {
                "seller_gstin": "",
                // "enterprise_gstin": pickup_address_details.gstin || "",
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
                // "consignee_gstin": delivery_address_details.gstin || "",
                "sgst_total_tax": 0
            }
        },
        "appointment_info": {
            "start_time": formatAppointmentDateTime(frm.doc.start_time) || null,
            "end_time": formatAppointmentDateTime(frm.doc.end_time) || null,
            "id": ""
        },
        "additional_info": {
            "return_info": pickup_info,
        
        }
    }      
}

function formatAppointmentDateTime(erpNextDateTime) {
    if (!erpNextDateTime) {
        return null;
    }
    // Parse the ERPNext datetime
    const dateTime = moment(erpNextDateTime);

    // Format to DD-MM-YYYY hh:mm
    return dateTime.format('DD-MM-YYYY HH:mm');
}
//Track AWB Registration
function track_shipment(frm){
    frappe.call({
        method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment.track_shipment',
        args: {
            'waybill': frm.doc.awb_number,
            'cp_id': frm.doc.carrier_partner_id,
        },
        freeze: true,
        freeze_message: __('Tracking AWB Registration...'),
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
                        // Instead of directly manipulating the form, use a server-side method to update the AWB
                        frappe.call({
                            method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.utils.update_awb_tracking',
                            args: {
                                'shipment_name': frm.doc.name,
                                'tracking_data': shipment
                            },
                            freeze: true,
                            freeze_message: __('Updating AWB tracking data...'),
                            callback: function(update_r) {
                                if(update_r.message && update_r.message.success) {
                                    // Reload the document to show the updated data
                                    frm.reload_doc();
                                    frappe.model.with_doc("AWB Registration", frm.doc.name, function() {
                                        var doc = frappe.model.get_doc("AWB Registration", frm.doc.name);
                                    });
                                    
                                    frappe.msgprint({
                                        title: __('Success'),
                                        message: __(`${r.message.response.meta.message.toString()}, AWB Registration tracked successfully`),
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
//Proof of delivery
function proof_of_delivery(frm) {
    frappe.call({
        method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment.get_proof_of_delivery',
        args: {
            'waybill': frm.doc.awb_number,
            'cp_id': frm.doc.carrier_partner_id,
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
                        'doctype': 'AWB Registration',
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
                            frappe.db.set_value('AWB Registration', frm.doc.name, 'pod_file', file_url)
                                .then(() => {
                                    // Update the local doc
                                    frm.doc.pod_file = file_url;
                                    
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

frappe.ui.form.on("Shipment Delivery Note", {
    shipment_delivery_note_add: function(frm, cdt, cdn) {
        // Get the current row that was added
        let row = locals[cdt][cdn];
        
        // Check if sales_invoice child table has items
        if (frm.doc.sales_invoice && frm.doc.sales_invoice.length > 0) {
            frappe.confirm(
                __('Adding a Delivery Note will clear existing Sales Invoice entries. Continue?'),
                function() {
                    // User clicked "Yes" - clear the Sales Invoice child table
                    frm.clear_table('sales_invoice');
                    frm.refresh_field('sales_invoice');
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
    },
	delivery_note: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.delivery_note) {
			let row_index = row.idx - 1;
			if (validate_duplicate(frm, "shipment_delivery_note", row.delivery_note, row_index)) {
				frappe.throw(
					__("You have entered a duplicate Delivery Note on Row") +
						` ${row.idx}. ` +
						__("Please rectify and try again.")
				);
			}
		}
	},
	grand_total: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.grand_total) {
			var value_of_goods = parseFloat(frm.doc.value_of_goods) + parseFloat(row.grand_total);
			frm.set_value("value_of_goods", Math.round(value_of_goods));
			frm.refresh_fields("value_of_goods");
		}
	},
});

var validate_duplicate = function (frm, table, fieldname, index) {
	return table === "shipment_delivery_note"
		? frm.doc[table].some((detail, i) => detail.delivery_note === fieldname && !(index === i))
		: frm.doc[table].some((detail, i) => detail.email === fieldname && !(index === i));
};

function update_sales_invoice_shipment_reference(frm) {
    if (!frm.doc.sales_invoice || frm.doc.sales_invoice.length === 0) {
        return;
    }
    
    // Show a loading message
    frappe.show_alert({
        message: __('Updating Sales Invoice references...'),
        indicator: 'blue'
    });
    
    // Create an array of promises for each update
    const update_promises = frm.doc.sales_invoice.map(invoice_row => {
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

frappe.ui.form.on('Sales Invoice Shipment', {
    // When sales_invoice is added/changed
    sales_invoice_add: function(frm, cdt, cdn) {
        
        // Get the current row that was added
        let row = locals[cdt][cdn];
        
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
                    frm.get_field('sales_invoice').grid.grid_rows[
                        frm.get_field('sales_invoice').grid.grid_rows.length - 1
                    ].remove();
                    frm.refresh_field('sales_invoice');
                }
            );
        }
        check_duplicate_sales_invoice(frm, row);

        calculate_total_amount(frm);
        
    },
    sales_invoice_remove: function(frm, cdt, cdn) {
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
    frm.doc.sales_invoice.forEach((row, index) => {
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

// Function to calculate total amount
function calculate_total_amount(frm) {
    let total_amount = 0;
    
    if(frm.doc.sales_invoice && frm.doc.sales_invoice.length > 0) {
        frm.doc.sales_invoice.forEach(invoice => {
            if(invoice.grand_total) {
                total_amount += flt(invoice.grand_total);
            }
        });
    }
    
    // Set the calculated amount to the shipment amount field
    // Assuming the field name is 'amount' - adjust if it's different
    frm.set_value('shipment_amount', total_amount);
    frm.set_value('value_of_goods', total_amount);
    // frm.set_value('cod_value', total_amount);
    frm.refresh_field('shipment_amount');
    frm.refresh_field('value_of_goods');
    // frm.refresh_field('cod_value');
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

function get_address_details(address_name) {
    return new Promise((resolve, reject) => {
        if (!address_name) {
            // reject("Address name is required");
            resolve({
                city: "",
                state: "",
                pincode: "",
                country: "IN",
                address: "",
                district: "",
                location_code: "",
                gstin: ""
            });
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
                    resolve({
                        city: "",
                        state: "",
                        pincode: "",
                        country: "IN",
                        address: "",
                        district: "",
                        location_code: "",
                        gstin: ""
                    });
                }
            },
            error: function(err) {
                return
                // reject("Error fetching address: " + err);
            }
        });
    });
}

function get_box_info(frm) {
    // If there are no parcels, return a default box
    
    // Map each parcel to a box info object
    return frm.doc.shipment_parcel.map(parcel => {
        return {
            "count": parcel.count || 1,
            "reference_number_prefix": "",
            "box_master_code": parcel.box_code || "",
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
    return frm.doc.sales_invoice.map(invoice => {
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
        if (!frm.doc.sales_invoice || frm.doc.sales_invoice.length === 0) {
            resolve([]);
            return;
        }

        const purchase_order_promises = frm.doc.sales_invoice.map(invoice => {
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


function get_appointment(frm){
    frappe.call({
        method: 'clickpost_erpnext_integration.clickpost_erpnext_integration.apis.shipment.get_appointment',
        args: {
            "awb_number": frm.doc.awb_number,
            "account_code": frm.doc.carrier_account_name,
            "courier_partner_id": frm.doc.carrier_partner_id
        },
        freeze: true,
        freeze_message: __('Getting Appointment Details...'),
        callback: async function(r) {
            if(r.message.response.appointment_start_time) {
                const result = r.message.response;
                frm.set_value("start_time", frappeDatetime(result.appointment_start_time))
                frm.set_value("end_time", frappeDatetime(result.appointment_end_time))
                frm.set_value("reason_for_appointment", result.reason_for_appointment_change)
                frm.set_value("appointment_status", result.appointment_status)
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
                                        doctype: 'AWB Registration',
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
                    frm.set_value("appointment_attachments", links.join("<br>"));
                    frm.refresh_field("appointment_attachments");
                    frappe.show_alert(
                       `Appointment details updated successfully for ${frm.doc.name}`, 5
                    );
                } else {
                    frm.set_value("appointment_attachments", __("No appointment documents found."));
                    frm.refresh_field("appointment_attachments");
                }

                await frm.save("Update");
                await frm.reload_doc();
            }else{
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


