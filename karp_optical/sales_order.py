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


def gnerate_payment_entry(doc, method):
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
    posting_date = frappe.utils.nowdate()

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
        "reference_no": "1234"
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
    for item in doc.items:
        # Assuming item.item_code exists

        # Now you can set this rate in your sales invoice item
        sales_invoice.append('items', {
            'item_code': item.item_code,
            'qty': item.qty,
            'rate': item.rate,  # You can set the incoming_rate here if needed
            # Set other fields as necessary
        })

    # Optionally, set other fields
    sales_invoice.set_posting_time = 1
    sales_invoice.posting_date = frappe.utils.nowdate()

    # Append reference to the Sales Order
    sales_invoice.append('references', {
        'reference_doctype': 'Sales Order',
        'reference_name': doc.name,
        'due_date': doc.delivery_date,
        'total_amount': doc.grand_total
    })

    # Save the Sales Invoice
    sales_invoice.insert(ignore_permissions=True)
    sales_invoice.submit()  # Submit if you want it to be finalized

    frappe.msgprint(f"Sales Invoice {sales_invoice.name} has been created for Sales Order {doc.name}")


def gnerate_connected_documents(doc, method):
    gnerate_payment_entry(doc, method)
    # print("Generate Sales Invoice: ")
    # print(doc.custom_generate_invoice)
    # if doc.custom_generate_invoice :
    #     gnerate_sales_invoices(doc, method)
