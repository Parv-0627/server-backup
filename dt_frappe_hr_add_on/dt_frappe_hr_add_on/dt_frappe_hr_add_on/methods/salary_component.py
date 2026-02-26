import frappe
from frappe.utils import ceil
from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip

def validate_base(doc):
    if doc.base <= 0:
        frappe.throw(msg = 'Please set the Base for the Salary Structure assignment greater than 0',
                    title='Base Value Not Set')

def add_component(doc,method):
    # check = frappe.db.get_single_value('DT-Frappe-HR Customization Settings', 's_slip')
    check = 1
    if check == 1:
        print ('\n\n\n\nIn salary slip\n\n\n\n')
        doc.add_structure_components('custom_contributions')
    


def add_salary_component(doc, method):
    # check = frappe.db.get_single_value('DT-Frappe-HR Customization Settings', 's_st_assign')
    # frappe.throw('test_starts')
    check = 1
    if check == 1:
        # print ('\n\n\n\nIn salary structure assignment\n\n\n\n')
        validate_base(doc)
        # print ('\n\n\n')
        doc.custom_earnings = []
        doc.custom_deductions = []
        doc.custom_contributions = []
        sal_doc = make_salary_slip(doc.salary_structure, employee=doc.employee, for_preview=1, ignore_permissions=True)
        sal_doc.add_structure_components('custom_contributions')

        # print(sal_doc.total_working_days)
        # for d in sal_doc.earnings:
        #     print (d.salary_component , '    ', d.amount)
        # for d in sal_doc.deductions:
        #     print (d.salary_component , '    ', d.amount)
        # for d in sal_doc.custom_contributions:
        #     print (d.salary_component , '    ', d.amount)
        total_contribution = 0

        for d in sal_doc.earnings:
            doc.append('custom_earnings', d)
        for d in sal_doc.deductions:
            doc.append('custom_deductions', d)
        for d in sal_doc.custom_contributions:
            total_contribution += d.amount
            doc.append('custom_contributions', d)
        
        doc.custom_ctc_monthly = sal_doc.gross_pay + total_contribution
        doc.custom_total_deductions = sal_doc.total_deduction
        doc.custom_gross_pay = sal_doc.gross_pay
        doc.custom_total_employer_contributions = total_contribution
        doc.custom_net_pay = sal_doc.net_pay
        doc.save()
        

def change_component_details(components):
    for d in components:
        d.depends_on_payment_days = 0

def add_to_sal_struct_assignment(components, doc):
    if len(components)>0:
        if doc.get(components[0].get('parentfield')):
            return 0
        total = 0   
        for component in components:
            if component.amount > 0:
                row = doc.append(component.get('parentfield'),{})
                row.salary_component = component.salary_component
                row.amount = ceil(component.amount)
                total += ceil(row.amount)
        doc.save()
        return total
    else:
        return 0


def view_components(components):
    for component in components:
        print(f'\n{component.salary_component} - {component.amount}  |||||| \n')
        
    print('\n\n\nBREAK')
        
def get_tds_value_from_salary_slip(doc):
    for d in doc.get('deductions'):
        if d.component == 'TDS On salary':
            return d.amount
    return 0