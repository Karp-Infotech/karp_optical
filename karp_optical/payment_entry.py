import frappe

def copy_warehouse_from_sales_order(doc, method):
    # Check if the Payment Entry is linked to a Sales Order
    if doc.references:
        for ref in doc.references:
            if ref.reference_doctype == "Sales Order" and ref.reference_name:
                # Fetch the Sales Order
                sales_order = frappe.get_doc("Sales Order", ref.reference_name)

                doc.custom_store = sales_order.set_warehouse
            elif ref.reference_doctype == "Sales Invoice" and ref.reference_name:
                # Fetch the Sales Order
                sales_invoice = frappe.get_doc("Sales Invoice", ref.reference_name)

                doc.custom_store = sales_invoice.set_warehouse



