import frappe

def add_contributions_to_jv(doc, method):

    # hr_doc = frappe.get_last_doc('DT- HR Settings', filters = {'company' : doc.company})
    if doc.custom_employer_contribution_added == 0:
        # frappe.throw('test')
        for d in doc.get('accounts'):
            if d.party_type == 'Employee' and d.reference_type == 'Payroll Entry':
                payroll_entry_name = d.reference_name
                emp_salary_slip = frappe.get_last_doc('Salary Slip',filters = {'employee' : d.party, 'payroll_entry':payroll_entry_name })
                
                if emp_salary_slip.get('custom_contributions'):
                    for contribution in emp_salary_slip.get('custom_contributions'):
                        if frappe.db.exists('Contribution Map',{'salary_component': contribution.salary_component}) != None:
                            row_debit = {
                                'account' : frappe.get_value('Contribution Map',{'salary_component': contribution.salary_component}, "expense_account"),
                                'debit_in_account_currency': contribution.amount ,
                                'cost_center': frappe.db.get_single_value('DT-Frappe HR Add-on Settings', 'cost_center')
                            }
                            row_credit = {
                                'account' : frappe.get_value('Contribution Map',{'salary_component': contribution.salary_component}, "payable_account"),
                                'credit_in_account_currency': contribution.amount ,
                                'cost_center': frappe.db.get_single_value('DT-Frappe HR Add-on Settings', 'cost_center')
                            }
                            doc.append('accounts', row_debit)
                            doc.append('accounts', row_credit)
                            doc.custom_employer_contribution_added = 1
