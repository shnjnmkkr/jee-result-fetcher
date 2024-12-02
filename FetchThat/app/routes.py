from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service  # Added import for Service
from webdriver_manager.chrome import ChromeDriverManager  # Added import for ChromeDriverManager
import time

# Flask App Setup
app = Flask(__name__)

# Load Student Data
data_path = #REDACTED
students_df = pd.read_csv(data_path, on_bad_lines='skip')
students_df.columns = students_df.columns.str.strip()  # Clean up column names

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search_students():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])  # Only return results for queries with 2 or more characters
    
    # Ensure no NaN values in the 'Candidate Name' column
    students_df['Candidate Name'] = students_df['Candidate Name'].fillna('')

    # Search for students whose names match the query
    matching_students = students_df[students_df['Candidate Name'].str.contains(query, case=False)]
    
    # Create a list of dictionaries with student details for frontend suggestions
    student_suggestions = matching_students[['Candidate Name', 'Roll No', 'Branch']].to_dict(orient='records')
    
    return jsonify(student_suggestions)

@app.route('/select_student', methods=['POST'])
def select_student():
    data = request.get_json()
    roll_number = data['roll_no']

    # Search for student using roll number
    selected_student = students_df[students_df['Roll No'] == roll_number]

    if selected_student.empty:
        return jsonify({'error': 'Student not found'}), 404

    # Extract the application number for backend use (don't expose to frontend)
    application_number = selected_student.iloc[0]['Application Number']

    # Extract student details to show on frontend
    student_name = selected_student.iloc[0]['Candidate Name']
    branch = selected_student.iloc[0]['Branch']

    # Generate dynamic year and month dropdowns
    current_year = datetime.now().year
    years = [year for year in range(1900, current_year + 1)]  # Years from 1900 to current year
    months = [month for month in range(1, 13)]  # Months from 1 to 12

    # Return the page for the user to enter DOB and CAPTCHA
    return render_template(
        'captcha_input.html',
        roll_number=roll_number,
        student_name=student_name,
        branch=branch,
        application_number=application_number,
        years=years,
        months=months
    )

@app.route('/submit_form', methods=['POST'])
def submit_form():
    # Initialize the WebDriver
    options = Options()
    options.headless = True  # Run headless for background operation
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # Navigate to the external website
        driver.get('URL_OF_THE_EXTERNAL_WEBSITE')

        # Wait for the page to load and dropdowns to be available
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_ddlday"))
        )

        # Locate the day, month, and year dropdowns using their IDs
        day_dropdown = Select(driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_ddlday"))
        month_dropdown = Select(driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_ddlmonth"))
        year_dropdown = Select(driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_ddlyear"))

        # Select a value for day, month, and year (you can change these values based on your form data)
        day_dropdown.select_by_value('15')   # Example: Select day "15"
        month_dropdown.select_by_value('05') # Example: Select May (05)
        year_dropdown.select_by_value('1995') # Example: Select year "1995"

        # Optionally, if there's a submit button on the form, you can submit it
        submit_button = driver.find_element(By.ID, 'submit_button_id')  # Change to actual submit button ID
        submit_button.click()

        # Wait for any result or confirmation (optional)
        time.sleep(5)

        # Process the response or continue with the flow
        # For instance, capture the result after form submission
        # result = driver.find_element(By.ID, 'result_id')  # If there's a result to capture

        # Return a success response or continue with your workflow
        return "Form submitted successfully"

    except Exception as e:
        # Handle exceptions and errors
        print(f"Error during form submission: {e}")
        return "There was an error submitting the form."

    finally:
        # Close the driver
        driver.quit()

    # Redirect user to the final results page
    return redirect(result_url)

if __name__ == '__main__':
    app.run(debug=True)



