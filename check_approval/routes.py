from . import check_aprvl
from flask import current_app,request,jsonify
import os
from werkzeug.utils import secure_filename
from flask_cors import cross_origin
import csv
from sendgrid import SendGridAPIClient, Attachment
from sendgrid.helpers.mail import Mail
from base64 import b64encode

@check_aprvl.route('/check_approval/csv_file', methods=['POST', 'GET'])
@cross_origin()
def check_aprvl_csv():
    if 'csv_file' not in request.files:
        return 'No file part', 400
    
    file = request.files['csv_file']

    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        return 'No selected file', 400

    if file and allowed_file(file.filename):
        # Secure the filename before using it
        filename = secure_filename(file.filename)
        # Save file to the uploads folder
        print(filename)
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        # Process the file here
        # ...
        results = process_csv_file(os.path.join(current_app.config['UPLOAD_FOLDER'], filename),"./output_file.txt")
        return {"results":results}
    else:
        return 'Invalid file type', 400
    
@check_aprvl.route('/check_approval/one_row', methods=['POST', 'GET'])
@cross_origin()
def check_aprvl_one():
    try:
        # Make sure to only proceed if method is POST
        if request.method == 'POST':
            # Parse the JSON payload from the request
            data = request.get_json()
            # Validate the input data if needed
            
            # Call the process_one_row function with the received row data
            result = process_one_row(data,"./output_file_one_row")

            # Return the result as a JSON response
            return jsonify(result), 200
    except Exception as e:
        # Log the error for debugging purposes, and/or handle it as required
        print(f"An error occurred: {e}")
        # Return a generic error response
        return jsonify({'error': 'An error occurred processing your request.'}), 500



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'csv'}



def process_csv_file(file_path, output_file_path):
    results = []
    accepted_count=0
    rejected_count=0
    LTV_count=0
    DTI_count=0
    FEDTI_count=0
    credit_rating_count=0
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)

            for row in csv_reader:
                id = row['ID']
                credit_score = int(row['CreditScore'])
                appraised_value = float(row['AppraisedValue'])
                down_payment = float(row['DownPayment'])
                loan_amount = float(row['LoanAmount'])
                gross_income = float(row['GrossMonthlyIncome'])
                total_debt_payments = sum(float(row[k]) for k in ['CreditCardPayment', 'CarPayment', 'StudentLoanPayments'])
                mortgage = float(row['MonthlyMortgagePayment'])

                ltv = ((appraised_value-down_payment) / (appraised_value)) * 100
                dti = ((total_debt_payments + mortgage) / gross_income) * 100
                fedti = (mortgage / gross_income) * 100

                approved = True
                reasons = []
                conditions = []

                # Check the criteria for approval
                if credit_score < 640:
                    approved = False
                    credit_rating_count+=1
                    reasons.append("Credit score below 640.")
                if ltv > 95:
                    approved = False
                    LTV_count+=1
                    reasons.append(f"LTV ratio too high: {ltv:.2f}%.")

                # Additional DTI and FEDTI checks for conditions
                if dti > 43:
                    DTI_count+=1
                    approved = False
                    reasons.append(f"DTI ratio too high: {dti:.2f}%.")
                elif dti > 36:
                    conditions.append("DTI ratio above preferred level of 36%.")

                if fedti > 28:
                    FEDTI_count+=1
                    approved = False
                    reasons.append(f"FEDTI ratio above preferred level of 28%.")

                # Check for LTV-based PMI condition
                if 80 <= ltv <= 95:
                    conditions.append("PMI required due to LTV ratio between 80% and 95%.")

                results.append({
                    'id': id,
                    'approved': approved,
                    'reason_for_rejection': reasons if not approved else [],
                    'accepted_under_conditions': conditions if approved and conditions else []
                })
                if approved:
                    accepted_count += 1
                else:
                    rejected_count += 1

        # Write to the output file, overwriting any existing content
        with open(output_file_path, mode='w', newline='', encoding='utf-8') as output_file:
            fieldnames = ['id', 'approved', 'reason_for_rejection', 'accepted_under_conditions']
            writer = csv.DictWriter(output_file, fieldnames=fieldnames)

            writer.writeheader()
            for result in results:
                # Convert the list of reasons and conditions to a string
                result['reason_for_rejection'] = result['reason_for_rejection']
                result['accepted_under_conditions'] = result['accepted_under_conditions']
                
                writer.writerow(result)
        print(f"Accepted: {accepted_count}")
        print(f"Rejected: {rejected_count}")
        results.append(accepted_count)
        results.append(rejected_count)
        results.append(credit_rating_count)
        results.append(LTV_count)
        results.append(DTI_count)
        results.append(FEDTI_count)
        return results
    except Exception as e:
        print(f"Error processing the CSV file: {e}")
        return []
    
def process_one_row(row, output_file_path):
    # Convert string values to the appropriate type
    row['CreditScore'] = int(row['CreditScore'])
    row['AppraisedValue'] = float(row['AppraisedValue'])
    row['DownPayment'] = float(row['DownPayment'])
    row['LoanAmount'] = float(row['LoanAmount'])
    row['GrossMonthlyIncome'] = float(row['GrossMonthlyIncome'])
    row['CreditCardPayment'] = float(row['CreditCardPayment'])
    row['CarPayment'] = float(row['CarPayment'])
    row['StudentLoanPayments'] = float(row['StudentLoanPayments'])
    row['MonthlyMortgagePayment'] = float(row['MonthlyMortgagePayment'])

    # Perform the calculations
    row['LTV'] = ((row['AppraisedValue'] - row['DownPayment']) / row['AppraisedValue']) * 100
    total_debt_payments = row['CreditCardPayment'] + row['CarPayment'] + row['StudentLoanPayments']
    row['DTI'] = ((total_debt_payments + row['MonthlyMortgagePayment']) / row['GrossMonthlyIncome']) * 100
    row['FEDTI'] = (row['MonthlyMortgagePayment'] / row['GrossMonthlyIncome']) * 100

    approved = True
    credit_score_approved = True
    ltv_approved = True
    dti_approved = True
    fedti_approved = True

    reasons = []
    conditions = []

    # Check the criteria for approval
    if row['CreditScore'] < 640:
        credit_score_approved = False
        reasons.append("Credit score below 640.")
    if row['LTV'] > 95:
        ltv_approved = False
        reasons.append(f"LTV ratio too high: {row['LTV']:.2f}%.")
    if row['DTI'] > 43:
        dti_approved = False
        reasons.append(f"DTI ratio too high: {row['DTI']:.2f}%.")
    elif row['DTI'] > 36:
        conditions.append("DTI ratio above preferred level of 36%.")
    if row['FEDTI'] > 28:
        fedti_approved = False
        reasons.append(f"FEDTI ratio above preferred level of 28%.")

    # Check for LTV-based PMI condition
    if 80 <= row['LTV'] <= 95:
        conditions.append("PMI required due to LTV ratio between 80% and 95%.")

    # Determine overall approval based on individual criteria
    approved = credit_score_approved and ltv_approved and dti_approved and fedti_approved

    result = {
        'id': 1,
        'approved': approved,
        'reason_for_rejection': ";".join(reasons) if not approved else [],
        'accepted_under_conditions': ";".join(conditions) if approved and conditions else [],
        'credit_score_approved': credit_score_approved,
        'ltv_approved': ltv_approved,
        'dti_approved': dti_approved,
        'fedti_approved': fedti_approved
    }

    # Write to the output file, overwriting any existing content
    with open(output_file_path, mode='w', newline='', encoding='utf-8') as output_file:
        fieldnames = ['id', 'approved', 'reason_for_rejection', 'accepted_under_conditions', 
                      'credit_score_approved', 'ltv_approved', 'dti_approved', 'fedti_approved']
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerow(result)
    
    return result

@check_aprvl.route('/sendemail', methods=['POST'])
@cross_origin()
def send_email():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email is required."}), 400
    
    ltv = data.get('ltv')
    dti = data.get('dti')
    credit = data.get('credit')
    fedti = data.get('fedti')

    # Create the HTML content for the email
    html_content = f"""
    <html>
        <body>
            <p>This is your home purchase report from EDA:</p>
            <table border="1">
                <tr>
                    <th>Metric</th>
                    <th>Status</th>
                </tr>
                <tr>
                    <td>LTV (Loan to Value)</td>
                    <td>{"Approved" if ltv else "Not Approved"}</td>
                </tr>
                <tr>
                    <td>DTI (Debt to Income)</td>
                    <td>{"Approved" if dti else "Not Approved"}</td>
                </tr>
                <tr>
                    <td>Credit Score</td>
                    <td>{"Approved" if credit else "Not Approved"}</td>
                </tr>
                <tr>
                    <td>FeDTI (Federal Debt to Income)</td>
                    <td>{"Approved" if fedti else "Not Approved"}</td>
                </tr>
            </table>
        </body>
    </html>
    """

    # Create a plain text file with the information
    file_content = f"LTV (Loan to Value): {'Approved' if ltv else 'Not Approved'}\n" \
                   f"DTI (Debt to Income): {'Approved' if dti else 'Not Approved'}\n" \
                   f"Credit Score: {'Approved' if credit else 'Not Approved'}\n" \
                   f"FeDTI (Federal Debt to Income): {'Approved' if fedti else 'Not Approved'}\n"

    # Save the file temporarily
    filename = "Home_Purchase_Report.txt"
    with open(filename, 'w') as file:
        file.write(file_content)

    # Encode the file content
    with open(filename, 'rb') as f:
        data = f.read()
        f.close()
    encoded_file = b64encode(data).decode()

    # Create a SendGrid Attachment
    attachment = Attachment()
    attachment.file_content = encoded_file
    attachment.file_type = 'text/plain'
    attachment.file_name = filename
    attachment.disposition = 'attachment'
    attachment.content_id = 'Home Purchase Report'

    message = Mail(
        from_email='ameyshinde11111@gmail.com',
        to_emails=email,
        subject='Home Purchase Report from EDA',
        html_content=html_content
    )
    message.attachment = attachment

    try:
        sendgrid_client = SendGridAPIClient('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')
        response = sendgrid_client.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)
        return jsonify({"message": "Error while sending email using SendGrid"}), 500
    finally:
        # Clean up the file
        os.remove(filename)

    return jsonify({"message": "Email successfully sent. Please check your email."}), 200
