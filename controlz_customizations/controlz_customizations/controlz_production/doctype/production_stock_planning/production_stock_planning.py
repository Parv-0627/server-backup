# Copyright (c) 2024, Controlz Customizations and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.stock.utils import get_stock_balance
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.doctype.item.item import get_last_purchase_details

class ProductionStockPlanning(Document):
    def validate(self):
        self.caluclate_stock()
    
    def caluclate_stock(self):
        self.production_part_table = []
        self.production_stock_planning_table = []
        self.estimated_purchase_cost = 0
        for item_group_row in self.item_group_wise_table:
            item_group = frappe.get_doc("Item Group", item_group_row.item_group )
            for items_to_add in item_group.item_group_percentage:
                self.append("production_stock_planning_table",{
                    "item_to_produce": items_to_add.item,
                    "qty_to_produce": item_group_row.qty_to_produce * items_to_add.qty_percentage /100,
                    "controlz_bom": frappe.db.get_value("Controlz BOM", {"item":items_to_add.item}, "name")
                })
        for row in self.production_stock_planning_table:
            if not row.warehouse:
                row.warehouse = self.warehouse
            row.balance_in_warehouse = get_stock_balance(row.item_to_produce,row.warehouse )
            row.final_qty = row.qty_to_produce - row.balance_in_warehouse
            row.projected_qty = frappe.db.get_value(
                "Bin", {"item_code": row.item_to_produce, "warehouse": row.warehouse}, "projected_qty"
            )
            
            controlz_bom = frappe.get_doc("Controlz BOM", row.controlz_bom)
            for part_item in controlz_bom.bom_raw_material_table:
                part_warehouse = frappe.db.get_value("Item",part_item.item, "part_warehouse" )
                part_warehouse = part_warehouse if part_warehouse else self.part_warehouse
                qty_needed = row.qty_to_produce * part_item.qty_percentage /100
                qty_in_warehouse = get_stock_balance(part_item.item,part_warehouse )
                final_qty = qty_needed - qty_in_warehouse
                projected_qty = frappe.db.get_value(
                    "Bin", {"item_code": part_item.item, "warehouse": part_warehouse}, "projected_qty"
                )
                last_purchase_details =  get_last_purchase_details(part_item.item)
                self.estimated_purchase_cost += last_purchase_details.get("rate",0) * final_qty
                self.append("production_part_table",{
                    "item_to_produce": row.item_to_produce,
                    "qty_to_produce": row.qty_to_produce,
                    "part_item": part_item.item,
                    "qty_percentage": part_item.qty_percentage,
                    "qty_needed": qty_needed,
                    "part_warehouse": part_warehouse,
                    "qty_in_warehouse": qty_in_warehouse, 
                    "final_qty": final_qty,
                    "projected_qty": projected_qty,
                    "last_purchase_rate": last_purchase_details.get("rate",0)
                })


@frappe.whitelist()
def make_part_material_request_from_psp(source_name,target_doc=None):
    def set_missing_values(source, target):
        
        psp = frappe.get_doc("Production Stock Planning", source_name)
        target.material_request_type = "Purchase"
        target.set_warehouse = psp.part_warehouse
        for row in psp.production_part_table:
            target.append("items",{
                "item_code": row.part_item,
                "parts_for": row.item_to_produce,
                "qty": row.final_qty,
                "warehouse": row.part_warehouse
            })
        target.run_method("set_missing_values")
        

    doclist = get_mapped_doc("Production Stock Planning", source_name,
    {
        "Production Stock Planning": {
            "doctype": "Material Request",
            "field_map": {
                "name":"production_stock_planning",
            }
        },

    }, target_doc,set_missing_values)

    return doclist

@frappe.whitelist()
def make_fg_material_request_from_psp(source_name,target_doc=None):
    def set_missing_values(source, target):
        
        psp = frappe.get_doc("Production Stock Planning", source_name)
        target.material_request_type = "Purchase"
        target.set_warehouse = psp.part_warehouse
        for row in psp.production_stock_planning_table:
            target.append("items",{
                "item_code": row.item_to_produce,
                "qty": row.final_qty,
                "warehouse": row.warehouse
            })
        target.run_method("set_missing_values")
        

    doclist = get_mapped_doc("Production Stock Planning", source_name,
    {
        "Production Stock Planning": {
            "doctype": "Material Request",
            "field_map": {
                "name":"production_stock_planning",
            }
        },

    }, target_doc,set_missing_values)


    return doclist