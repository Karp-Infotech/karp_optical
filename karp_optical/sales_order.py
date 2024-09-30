import frappe

def sync_store_to_customer(doc, method):
    # Get the customer linked to the sales order
    customer = frappe.get_doc("Customer", doc.customer)

    # Set the warehouse field in the Customer doctype based on the Sales Order warehouse
    customer.custom_store_association = doc.set_warehouse
    
    # Save the customer record
    customer.save()

    # Commit the changes to the database
    frappe.db.commit()