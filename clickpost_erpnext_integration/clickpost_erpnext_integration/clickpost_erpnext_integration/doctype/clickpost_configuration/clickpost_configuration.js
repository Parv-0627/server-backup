// Copyright (c) 2025, nasirucode and contributors
// For license information, please see license.txt

frappe.ui.form.on("Clickpost Configuration", {
	refresh(frm) {
		if(frm.doc.enable){
			frm.add_custom_button(__('Get Carrier'), function() {
				get_carrier(frm);
			}).css({
				'background-color': 'rgb(29, 160, 142)', 
				'color': 'white'
			});
		}
		
	},

	enable: function(frm) {
		if(frm.doc.enable !== 0){
			frm.add_custom_button(__('Get Carrier'), function() {
				get_carrier(frm);
			}).css({
				'background-color': 'rgb(29, 160, 142)', 
				'color': 'white'
			});
		}
		
	},
	
	// before_save: function(frm) {
	// 	if (frm.doc.enable) {
	// 		frappe.call({
	// 			method: "clickpost_erpnext_integration.clickpost_erpnext_integration.apis.connection.test_clickpost_connection",
	// 			freeze: true,
	// 			callback: function(r) {
	// 				if (r.message.status === "success") {
	// 					frappe.show_alert({
	// 						title: __('Success'),
	// 						indicator: 'green',
	// 						message: __('Clickpost connection is successfully authorized')
	// 					}, 10);
    //                     // frm.save()
	// 				} else {
	// 					frm.set_value('enable', 0);
	// 					frappe.show_alert({
	// 						title: __('Connection Failed'),
	// 						indicator: 'red',
	// 						message: __(r.message.message || 'Invalid API Credentials')
	// 					}, 10);
	// 				}
	// 			},
	// 			error: function(r) {
	// 				frm.set_value('enable', 0);
	// 				frappe.show_alert({
	// 					title: __('Error'),
	// 					indicator: 'red',
	// 					message: __('ClickPost API Connection Failed. Please check your credentials.')
	// 				}, 10);
	// 			}
	// 		});
	// 	}
	// }
});

function get_carrier(frm) {
	if (!frm.doc.enable) {
		frappe.throw(__('Please enable the Clickpost Configuration first'));
		return;
	}

	frappe.call({
		method: "clickpost_erpnext_integration.clickpost_erpnext_integration.apis.carrier.get_carrier",
		freeze: true,
		freeze_message: __('Fetching carriers from Clickpost...'),
		callback: function(r) {
			if (r.message && r.message.status === "success") {
				const carriers = r.message.response.result || [];
				if (carriers.length === 0) {
					frappe.show_alert({
						title: __('No Carriers'),
						indicator: 'orange',
						message: __('No carriers found in Clickpost')
					}, 5);
					return;
				}

				// Process carriers
				process_carriers(carriers);
				
				frappe.show_alert({
					title: __('Success'),
					indicator: 'green',
					message: __('Carriers fetched and updated successfully')
				}, 5);
			} else {
				frappe.show_alert({
					title: __('Failed'),
					indicator: 'red',
					message: __(r.message?.message || 'Failed to fetch carriers from Clickpost')
				}, 10);
			}
		},
		error: function(err) {
			frappe.show_alert({
				title: __('Error'),
				indicator: 'red',
				message: __('An error occurred while fetching carriers')
			}, 10);
			console.error('Error fetching carriers:', err);
		}
	});
}

function process_carriers(carriers) {
	frappe.call({
		method: "clickpost_erpnext_integration.clickpost_erpnext_integration.apis.carrier.update_carrier_partners",
		args: {
			carriers: carriers
		},
		freeze: true,
		freeze_message: __('Updating carrier partners...'),
		callback: function(r) {
			if (r.message) {
				const result = r.message;
				frappe.show_alert({
					title: __('Carriers Updated'),
					indicator: 'green',
					message: __(`${result.created} carriers created, ${result.updated} carriers updated`)
				}, 5);
			}
		},
		error: function(err) {
			frappe.show_alert({
				title: __('Error'),
				indicator: 'red',
				message: __('Failed to update carrier partners')
			}, 10);
			console.error('Error updating carrier partners:', err);
		}
	});
}
