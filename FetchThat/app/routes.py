from flask import Flask, render_template, request, jsonify, redirect
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
import time
import requests
from io import BytesIO
from PIL import Image, UnidentifiedImageError

# Flask App Setup
app = Flask(__name__)

# Load Student Data
data_path = r'C:\Users\User\Work\Self\FetchThat\databases\dtu2023\file0816.csv'
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
    roll_number = data['roll_no']  # Keep the space in the column name
    
    # Debugging: Print the roll number and first few records
    print(f"Received roll number: '{roll_number}'")

    # Search for student using roll number
    selected_student = students_df[students_df['Roll No'] == roll_number]
    
    if selected_student.empty:
        print("No matching student found.")
        return jsonify({'error': 'Student not found'}), 404

    # Extract the application number for backend use (don't expose to frontend)
    application_number = selected_student.iloc[0]['Application Number']
    
    # Debugging: Show the application number found in the backend
    print(f"Found application number: {application_number}")

    # Extract student details to show on frontend
    student_name = selected_student.iloc[0]['Candidate Name']
    branch = selected_student.iloc[0]['Branch']

    # Initialize WebDriver for Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Headless mode (no browser UI)
    driver = webdriver.Chrome(options=chrome_options)

    # Open the external website
    driver.get("https://cnr.nic.in/resultservices/JEEMAINauth23s2p1")

    # Extract CAPTCHA image URL from the page source
    captcha_image_element = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_captchaimg')
    captcha_image_url = captcha_image_element.get_attribute('src')

    # Debugging: Print CAPTCHA URL
    print(f"CAPTCHA URL: {captcha_image_url}")

    # Fetch CAPTCHA image from the URL
    response = requests.get(captcha_image_url)
    
    # Check for a valid response
    if response.status_code == 200:
        content_type = response.headers.get('Content-Type', '').lower()
        
        if 'image' in content_type:  # Ensure the response is an image
            try:
                # Try to open the image from the response content
                img = Image.open(BytesIO(response.content))
                captcha_image_path = 'static/captcha.jpg'
                img.save(captcha_image_path)
            except UnidentifiedImageError:
                print("Error: The fetched content is not a valid image.")
                driver.quit()
                return jsonify({'error': 'Failed to retrieve CAPTCHA image'}), 500
        else:
            print(f"Error: Received content is not an image. Content-Type: {content_type}")
            driver.quit()
            return jsonify({'error': 'CAPTCHA image not found'}), 500
    else:
        print(f"Error: Unable to fetch CAPTCHA image. Status code: {response.status_code}")
        driver.quit()
        return jsonify({'error': 'Failed to fetch CAPTCHA image'}), 500

    # Return the page for the user to enter DOB and CAPTCHA
    driver.quit()
    return render_template('captcha_input.html', roll_number=roll_number, student_name=student_name, branch=branch, captcha_image_path=captcha_image_path, application_number=application_number)

@app.route('/submit_form', methods=['POST'])
def submit_form():
    application_number = request.form['application_number']
    dob = request.form['dob']
    captcha = request.form['captcha']

    # Initialize WebDriver for Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Headless mode (no browser UI)
    driver = webdriver.Chrome(options=chrome_options)

    # Open the external website
    driver.get("https://cnr.nic.in/resultservices/JEEMAINauth23s2p1")

    # Fill the Application Number
    application_field = driver.find_element(By.NAME, 'application_no')
    application_field.send_keys(application_number)

    # Fill Date of Birth (DOB)
    dob_dropdown = Select(driver.find_element(By.NAME, 'dob'))
    dob_dropdown.select_by_value(dob)

    # Fill CAPTCHA
    captcha_field = driver.find_element(By.NAME, 'captcha')
    captcha_field.send_keys(captcha)

    # Submit the form
    submit_button = driver.find_element(By.NAME, 'submit')
    submit_button.click()

    # Wait for the result page to load
    time.sleep(5)

    # Optionally, you can scrape the result page content or redirect the user directly
    result_url = driver.current_url
    driver.quit()

    # Redirect user to the final results page
    return redirect(result_url)

if __name__ == '__main__':
    app.run(debug=True)
