# Copyright (c) 2024, Controlz Customizations and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.stock.utils import get_stock_balance
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.doctype.item.item import get_uom_conv_factor


class ProductionPlanningRecord(Document):
    def validate(self):
        self.balance = get_stock_balance(self.item_to_produce, self.warehouse)
        self.final_qty = self.qty_to_produce - self.balance
        for row in self.production_planning_raw_material:
            row.qty = self.final_qty * row.qty_percentage /100
        self.set_default_warehouse()
    
    def set_default_warehouse(self):
        if not self.work_in_progress_warehouse :
            self.work_in_progress_warehouse = frappe.db.get_single_value("Manufacturing Settings", "default_wip_warehouse")
        if not self.finished_goods_warehouse:
            self.finished_goods_warehouse = frappe.db.get_single_value("Manufacturing Settings", "default_fg_warehouse")

@frappe.whitelist()
def get_raw_materials(controlz_bom):
    controlz_bom_doc = frappe.get_doc("Controlz BOM",controlz_bom )
    return controlz_bom_doc.bom_raw_material_table

@frappe.whitelist()
def make_material_issue_from_ppr(source_name,target_doc=None):
    def set_missing_values(source, target):
        
        ppr = frappe.get_doc("Production Planning Record", source_name)
        target.stock_entry_type = "Material Transfer for Manufacture"
        # target.from_warehouse = ppr.
        target.to_warehouse = ppr.work_in_progress_warehouse
        for row in ppr.production_planning_raw_material:
            target.append("items",{
                "t_warehouse": ppr.work_in_progress_warehouse,
                "item_code": row.item,
                "qty": row.qty,
                "uom": row.uom, 
                "stock_uom": row.uom,
                "conversion_factor": 1
            })
        target.run_method("set_missing_values")
        

    doclist = get_mapped_doc("Production Planning Record", source_name,
    {
        "Production Planning Record": {
            "doctype": "Stock Entry",
            "field_map": {
                "name":"production_planning_record",
            }
        },

    }, target_doc,set_missing_values)

    return doclist

@frappe.whitelist()
def make_fg_from_ppr(source_name,target_doc=None):
    def set_missing_values(source, target):
        
        ppr = frappe.get_doc("Production Planning Record", source_name)
        target.stock_entry_type = "Manufacture"
        target.from_warehouse = ppr.work_in_progress_warehouse
        target.to_warehouse = ppr.finished_goods_warehouse
        for row in ppr.production_planning_raw_material:
            target.append("items",{
                "s_warehouse": ppr.work_in_progress_warehouse,
                # "t_warehouse": ppr.finished_goods_warehouse,
                "item_code": row.item,
                "qty": row.transfered_qty,
                "uom": row.uom, 
                "stock_uom": row.uom,
                "conversion_factor": 1
            })
        
        target.append("items",{
            # "s_warehouse": ppr.work_in_progress_warehouse,
            "t_warehouse": ppr.finished_goods_warehouse,
            "item_code": ppr.item_to_produce,
            "qty": ppr.final_qty,
            "uom": ppr.uom, 
            "stock_uom": ppr.uom,
            "conversion_factor": 1,
            "is_finished_item": True
        })
        target.run_method("set_missing_values")
        

    doclist = get_mapped_doc("Production Planning Record", source_name,
    {
        "Production Planning Record": {
            "doctype": "Stock Entry",
            "field_map": {
                "name":"production_planning_record",
            }
        },

    }, target_doc,set_missing_values)

    return doclist