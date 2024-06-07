from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options

# Setup Edge options
edge_options = Options()
edge_options.add_argument("--headless")  # Ensure GUI is off
edge_options.add_argument("--no-sandbox")
edge_options.add_argument("--disable-dev-shm-usage")

# Set path to msedgedriver as per your configuration
webdriver_service = EdgeService(r"C:\Users\Developer\Downloads\edgedriver_win64\msedgedriver.exe")  # Change this to your actual path

# Choose Edge Browser
driver = webdriver.Edge(service=webdriver_service, options=edge_options)

# URL of the HelloFresh recipe page
url = "https://www.hellofresh.com/recipes/when-steak-met-potatoes-5857fcd16121bb11c124f383"
driver.get(url)

# Allow some time for the page to load
driver.implicitly_wait(10)

# Find all image elements on the page
all_images = driver.find_elements(By.TAG_NAME, "img")

# Extract the URLs of the images that are in the /ingredient/ folder
ingredient_image_urls = []
for img in all_images:
    src = img.get_attribute('src')
    if src and '/ingredient/' in src:
        ingredient_image_urls.append(src)

# Close the browser
driver.quit()

# Print the URLs
for url in ingredient_image_urls:
    print(url)
