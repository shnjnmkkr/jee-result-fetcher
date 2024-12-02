import requests
from PIL import Image
from io import BytesIO
from PIL import UnidentifiedImageError

# CAPTCHA image URL
captcha_image_url = 'https://cnr.nic.in/resultservices/JEEMAINauth23s2p1/captcha.jpg'

# Step 1: Fetch the CAPTCHA image from the external website
response = requests.get(captcha_image_url)

# Step 2: Check if the response status is 200 (OK)
if response.status_code != 200:
    print(f"Error: Failed to fetch CAPTCHA image. Status Code: {response.status_code}")
else:
    print("Successfully fetched the CAPTCHA image.")

    # Step 3: Check if the response content is an image
    if 'image' not in response.headers['Content-Type']:
        print("Error: Response is not an image.")
    else:
        # Step 4: Try opening the image with PIL
        try:
            img = Image.open(BytesIO(response.content))
            print("Successfully opened the CAPTCHA image.")
            
            # Optionally, save the image to check it
            img.save('test_captcha.jpg')
            print("Image saved as 'test_captcha.jpg'.")
        except UnidentifiedImageError:
            print("Error: The image could not be identified.")
