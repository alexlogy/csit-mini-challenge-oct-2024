from datetime import datetime, timezone, timedelta
import json
import os
import re
import requests
import time
import logging


# Logging Configuration
logger = logging.getLogger("[Program 1]")
logging.basicConfig(level=logging.INFO)


# Global Variables
if "API_URL" in os.environ:
    BASE_URL = os.environ['API_URL']
else:
    BASE_URL = "https://u8whitimu7.execute-api.ap-southeast-1.amazonaws.com/prod/"
if "OUTPUT_DIR" in os.environ:
    OUTPUT_DIR = os.environ['OUTPUT_DIR']
else:
    # for local dev environment testing
    OUTPUT_DIR = "datasets/"
if "CLEAN_DIR" in os.environ:
    CLEAN_DIR = os.environ['CLEAN_DIR']
else:
    # for local dev environment testing
    CLEAN_DIR = "clean/"
if "VALIDATED_DIR" in os.environ:
    VALIDATED_DIR = os.environ['VALIDATED_DIR']
else:
    # for local dev environment testing
    VALIDATED_DIR = "validated/"

class APIClient:
    """API Client.

    This function encapsulate the python requests library to include
    checking authorization token
    """
    def __init__(self):
        self.token = None
        self.token_expiry = None

    def get_auth_token(self):
        """
        Get Authorization Token
        """
        response = requests.get(BASE_URL + '/register')

        if response.status_code == 200:
            json_response = response.json()
            self.token = json_response['data']['authorizationToken']
            self.token_expiry = datetime.strptime(json_response['data']['tokenExpiryAt'], "%Y-%m-%d %H:%M:%S%z")
        else:
            logger.error("Failed to get auth token")

    def is_token_valid(self):
        """
        Check if the token is valid (i.e., not expired).
        """

        if self.token and self.token_expiry:
            return datetime.now(timezone(timedelta(hours=8))) < self.token_expiry
        return False

    def make_request(self, method, url, **kwargs):
        """
        Make an HTTP request with token validation check.
        This function automatically checks and renews the token if necessary.
        """
        # Check if token is valid, or fetch a new one
        if not self.is_token_valid():
            self.get_auth_token()

        # Add token to the headers
        headers = kwargs.get('headers', {})
        headers['authorizationToken'] = self.token
        kwargs['headers'] = headers

        # Make the actual request
        response = requests.request(method, url, **kwargs)
        return response


# methods

def download_dataset(page_id:str) -> str:
    """Returns next_id aka page number of the results

    This function calls the download-dataset API to download the JSON files
    """

    # request headers
    headers = {
        'Content-Type': 'application/json',
    }

    # json payload
    payload = {
        "next_id": page_id
    }

    try:
        response = api_client.make_request('POST', BASE_URL + '/download-dataset', headers=headers, json=payload)
        # response = requests.post(BASE_URL + '/download-dataset', headers=headers, json=payload)
        response.raise_for_status()

        json_response = response.json()
        # print(json_response)

        # url of dataset
        url = json_response['data']['dataset_url']
        logger.info("Dataset URL: " + url)

        # Use regex to extract the filename
        match = re.search(r"([^/]+\.json)(?=\?)", url)
        if match:
            filename = match.group(1)
            logger.info(f"Dataset Filename: {filename}")

        # create the output directory if it doesn't exist
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        # Construct the full path for the file
        file_path = os.path.join(OUTPUT_DIR, filename)

        json_file_request = api_client.make_request('GET', url)
        json_file_request.raise_for_status()

        if json_file_request.status_code == 200:
            json_file_content = json_file_request.json()

            # Save the JSON data to a file
            with open(file_path, 'w') as json_file:
                json.dump(json_file_content, json_file, indent=4)

            logger.info(f"JSON file downloaded and saved as {filename} in datasets/")

        return json_response['data']['next_id']
    except requests.exceptions.RequestException as e:
        logger.error("Error in request: " + str(e))


def retrieve_all_datasets():
    """
    Retrieve all available datasets.
    """
    # start with initial page
    page_number = ""
    logger.info("Page Number: 0")
    while True:
        logger.info("Downloading dataset..")
        # Download Dataset
        next_id = download_dataset(page_number)

        # set page_number to next_id returned
        page_number = next_id

        if not next_id:
            # End of Dataset, end the loop
            logger.info("No more pages of dataset to fetch!")
            break
        else:
            logger.info("Next Page Number: " + next_id)

            # Wait for 10 seconds before the next request to avoid hitting rate limits
            logger.info("Waiting 10s before next request to avoid hitting rate limits..")
            time.sleep(10)


# Function to check if a restaurant record is valid
def is_valid_record(record):
    # Check if ID is an integer
    if not isinstance(record.get("id"), int):
        return False
    # Check if restaurant_name is a non-empty string containing only alphabetic characters and spaces
    restaurant_name = record.get("restaurant_name", "")
    if not isinstance(restaurant_name, str) or not restaurant_name.strip():
        return False
    if not re.match("^[A-Za-z ]+$", restaurant_name):
        return False
    # Check if rating is a float within the valid range
    rating = record.get("rating")
    if not isinstance(rating, (float, int)) or not (1.00 <= rating <= 10.00):
        return False
    # Check if distance_from_me is a float within the valid range
    distance = record.get("distance_from_me")
    if not isinstance(distance, (float, int)) or not (10.00 <= distance <= 1000.00):
        return False
    return True


def load_and_clean_json(files):
    combined_data = []
    unique_ids = set()

    # Regex to match restaurant_name (alphabets and spaces only)
    name_pattern = re.compile(r"^[A-Za-z\s]+$")

    for file in files:
        logger.info("Cleaning data in File: " + file)
        cleaned_data = []
        with open(file, 'r') as f:
            try:
                data = json.load(f)
                for record in data:
                    # Validate record
                    if is_valid_record(record):
                        # If all checks pass

                        cleaned_data.append(record)
                        combined_data.append(record)
                        unique_ids.add(record['id'])
            except json.JSONDecodeError as e:
                logger.error(f"Error reading {file}: {e}")

        # remove datasets/ folder from filename
        cleaned_file_name = re.sub(r'^.*/', '', file)
        cleaned_file_path = CLEAN_DIR + cleaned_file_name

        # save the cleaned data individually
        logger.info("Saving cleaned data in File: " + cleaned_file_path)
        save_combined_json(cleaned_data, cleaned_file_path)

    return combined_data


def save_combined_json(data, output_file:str):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)


def get_files_list(directory:str):
    # Get all files in the specified directory
    files = [os.path.join(directory, file) for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]
    # Sort the files list by the filename in alphabetical ascending order
    files_sorted = sorted(files, key=lambda x: os.path.basename(x))

    return files_sorted


def check_data_validation(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    # request headers
    headers = {
        'Content-Type': 'application/json'
    }

    # payload
    payload = {
        "Data": data
    }

    try:
        response = api_client.make_request('POST', BASE_URL + 'test/check-data-validation', json=payload)
        response.raise_for_status()

        print(response.json())
    except requests.exceptions.RequestException as e:
        logger.error("Error in request: " + str(e))


if __name__ == '__main__':
    # initialize API client
    logger.info("Initializing API Client and Retrieving Authorization Token..")
    api_client = APIClient()

    # retrieve all datasets first
    logger.info("Retrieving datasets from API..")
    retrieve_all_datasets()

    # combine all datasets json files
    logger.info("Gathering list of datasets JSON files..")
    files_list = get_files_list(OUTPUT_DIR)

    # Load, clean, and combine the JSON files
    logger.info("Cleaning and combining the datasets..")
    cleaned_data = load_and_clean_json(files_list)

    # Save the combined and cleaned JSON to a file
    output_file = VALIDATED_DIR + "validated_dataset.json"
    save_combined_json(cleaned_data, output_file)

    logger.info(f"Validated datasets saved to {output_file}!")

    # # check data validation
    # check_data_validation(output_file)

    # end the program
    logger.info("Program 1 Completed all Operations!")
    logger.info("Exiting..")