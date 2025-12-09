import frappe
from datetime import date
from frappe.utils import nowdate


def gnerate_payment_entry(doc, method):

    frappe.flags.ignore_permissions = True
    # Ensure the Sales Order is submitted
    if doc.docstatus != 1:
        return

    # if doc.get("custom_mode_of_payment") == "UPI":
    #     if doc.custom_transaction_id == "":
    #         print("Transaction Id")
    #         print(doc.custom_transaction_id)
    #         frappe.msgprint(('Transaction Id is mandatory for UPI'))
        
    # Fetch customer details from the sales order
    customer = doc.customer
    posting_date = doc.transaction_date

    # Create a Payment Entry (advance payment for the Sales Order)
    payment_entry = frappe.get_doc({
        "doctype": "Payment Entry",
        "payment_type": "Receive",
        "party_type": "Customer",
        "party": customer,
        "posting_date": posting_date,
        "company": doc.company,
        "mode_of_payment": doc.get("custom_mode_of_payment"),
        "custom_store": doc.get("set_warehouse"),
        "paid_from": frappe.get_value('Company', doc.company, 'default_receivable_account'),
        "paid_to": frappe.get_value('Company', doc.company, 'default_cash_account'),
        "paid_amount": doc.get("custom_advanced_payment"),
        "received_amount": doc.get("custom_advanced_payment"),
        "target_exchange_rate": 1,
        "source_exchange_rate": 1,
        "reference_no": doc.custom_transaction_id
    })

    # Append the Sales Order reference correctly
    payment_entry.append('references', {
        'reference_doctype': 'Sales Order',  # Ensure this is correctly set
        'reference_name': doc.name,          # Sales Order name
        'due_date': doc.delivery_date,       # Delivery Date of Sales Order
        'total_amount': doc.grand_total,     # Grand Total from Sales Order
        'outstanding_amount': doc.grand_total,  # This is necessary for linking
        'allocated_amount': doc.custom_advanced_payment  # Amount being allocated from payment
    })

    # Insert the Payment Entry into the system
    payment_entry.insert(ignore_permissions=True)
    payment_entry.submit()
    frappe.db.commit()



def gnerate_sales_invoices(doc, method):
    frappe.flags.ignore_permissions = True
    # Ensure the Sales Order is submitted
    if doc.docstatus != 1:
        return

    # Check if Sales Invoice already exists for this Sales Order
    existing_invoices = frappe.get_all("Sales Invoice", filters={"sales_order": doc.name, "docstatus": ["<", 2]})
    if existing_invoices:
        return

   # Create a new Sales Invoice
    sales_invoice = frappe.new_doc('Sales Invoice')

    # Set fields from the Sales Order
    sales_invoice.customer = doc.customer
    sales_invoice.company = doc.company
    # Transfer items from Sales Order to Sales Invoice
    for item in doc.items:
        sales_invoice.append("items", {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "description": item.description,
            "uom": item.uom,
            "qty": item.qty,
            "rate": item.rate,
            "warehouse": item.warehouse,
            "sales_order": doc.name,  # Link to Sales Order
            "so_detail": item.name  # Reference to Sales Order Item
        })

    # Optionally, set other fields
    sales_invoice.set_posting_time = 1
    sales_invoice.posting_date = doc.transaction_date
    sales_invoice.sales_order = doc
    sales_invoice.set_warehouse = doc.set_warehouse



    # Save the Sales Invoice
    sales_invoice.insert(ignore_permissions=True)
    sales_invoice.submit()  # Submit if you want it to be finalized

    frappe.msgprint(f"Sales Invoice {sales_invoice.name} has been created for Sales Order {doc.name}")


def gnerate_delivery_note(doc, method):
    frappe.flags.ignore_permissions = True
    # Create a new Delivery Note document
    delivery_note = frappe.get_doc({
        "doctype": "Delivery Note",
        "customer": doc.customer,
        "posting_date": doc.transaction_date,
        "company": doc.company,
        "set_warehouse": doc.set_warehouse,
        "items": []
    })

    # Iterate over Sales Order items and add them to the Delivery Note
    for item in doc.items:
        delivery_note.append("items", {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "description": item.description,
            "qty": item.qty,  # Use qty from Sales Order
            "rate": item.rate,
            "uom": item.uom,
            "warehouse": item.warehouse,
            "against_sales_order": doc.name,  # Link to Sales Order
            "so_detail": item.name,  # Link the specific Sales Order item
        })

    # Insert the Delivery Note document into the database
    delivery_note.insert(ignore_permissions=True)

    # Submit the Delivery Note to complete the transaction
    delivery_note.submit()

# def mark_sales_order_as_complete(sales_order_name):
#     sales_order = frappe.get_doc('Sales Order', sales_order_name)
#     sales_order.status = 'Completed'
#     sales_order.save(ignore_permissions=True)
#     # Commit the changes to the database
#     frappe.db.commit()
#     frappe.msgprint(f"Sales Order {sales_order.name} has been marked as Completed.")
   
def gnerate_connected_documents(doc, method):
    frappe.flags.ignore_permissions = True
    if(doc.custom_sales_channel != "Web"):
        gnerate_payment_entry(doc, method)
        print("Generate Sales Invoice: ")
        print(doc.custom_generate_invoice)
        if doc.custom_generate_invoice :
            gnerate_delivery_note(doc, method)
            gnerate_sales_invoices(doc, method)
            #mark_sales_order_as_complete(doc.name)



def update_last_visited(doc, method):
    """Update the custom_last_visited field on the Customer when a Sales Order is created."""
    if not doc.customer:
        return

    frappe.db.set_value(
        "Customer",
        doc.customer,
        "custom_last_visited",
        nowdate()
    )