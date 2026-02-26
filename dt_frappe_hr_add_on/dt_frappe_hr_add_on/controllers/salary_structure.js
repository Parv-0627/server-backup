frappe.ui.form.on('Salary Structure', {
    onload: function(frm) {
        frm.fields_dict.custom_contributions.grid.get_field('salary_component').get_query = function(doc, cdt, cdn) {
            // var child = locals[cdt][cdn];
            // console.log(child.amount  )
            return {
                filters: {
                    'custom_is_company_contribution': 1
                }
            };
        };
    }
});