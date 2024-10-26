from datetime import datetime, timezone, timedelta
import json
import os
import re
import requests
import time
import logging

# Logging Configuration - Optimized for performance
logger = logging.getLogger("[Program 1]")
# Only log INFO and above, skip DEBUG
logger.setLevel(logging.INFO)
# Use a StreamHandler for console output - faster than FileHandler
console_handler = logging.StreamHandler()
# Use a simple formatter - faster than verbose formatting
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
# Remove the root logger handler to avoid duplicate logs
logger.propagate = False

# Global Variables
if "API_URL" in os.environ:
    BASE_URL = os.environ['API_URL']
else:
    BASE_URL = "https://u8whitimu7.execute-api.ap-southeast-1.amazonaws.com/prod/"
if "VALIDATED_DIR" in os.environ:
    VALIDATED_DIR = os.environ['VALIDATED_DIR']
else:
    # for local dev environment testing
    VALIDATED_DIR = "validated/"


class APIClient:
    def __init__(self):
        self.token = None
        self.token_expiry = None

    def get_auth_token(self):
        response = requests.get(BASE_URL + '/register')

        if response.status_code == 200:
            json_response = response.json()
            self.token = json_response['data']['authorizationToken']
            self.token_expiry = datetime.strptime(json_response['data']['tokenExpiryAt'], "%Y-%m-%d %H:%M:%S%z")
        else:
            logger.error("Failed to get auth token")

    def is_token_valid(self):
        if self.token and self.token_expiry:
            return datetime.now(timezone(timedelta(hours=8))) < self.token_expiry
        return False

    def make_request(self, method, url, **kwargs):
        if not self.is_token_valid():
            self.get_auth_token()

        headers = kwargs.get('headers', {})
        headers['authorizationToken'] = self.token
        kwargs['headers'] = headers

        response = requests.request(method, url, **kwargs)
        return response


def download_dataset(page_id: str) -> tuple:
    """Returns tuple of (next_id, dataset_content)"""
    headers = {
        'Content-Type': 'application/json',
    }

    payload = {
        "next_id": page_id
    }

    try:
        response = api_client.make_request('POST', BASE_URL + '/download-dataset', headers=headers, json=payload)
        response.raise_for_status()

        json_response = response.json()
        url = json_response['data']['dataset_url']
        logger.info(f"Dataset URL: {url}")

        json_file_request = api_client.make_request('GET', url)
        json_file_request.raise_for_status()

        if json_file_request.status_code == 200:
            json_file_content = json_file_request.json()
            logger.info("Dataset content retrieved successfully")
            return json_response['data']['next_id'], json_file_content

        return json_response['data']['next_id'], None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error in request: {str(e)}")
        return None, None


def retrieve_all_datasets():
    """Retrieve all available datasets and process them in memory."""
    all_records = []
    page_number = ""
    total_valid_records = 0

    logger.info("Page Number: 0")

    while True:
        logger.info("Downloading dataset..")
        next_id, dataset_content = download_dataset(page_number)

        if dataset_content:
            # Clean the current batch of records
            cleaned_records = [record for record in dataset_content if is_valid_record(record)]
            records_count = len(cleaned_records)
            all_records.extend(cleaned_records)
            total_valid_records += records_count
            logger.info(f"Added {records_count} valid records from current batch")

        page_number = next_id

        if next_id == "":
            logger.info(f"No more pages to fetch! Total valid records: {total_valid_records}")
            break
        else:
            logger.info(f"Next Page Number: {next_id}")
            time.sleep(10)

    output_file = VALIDATED_DIR + "validated_dataset.json"
    save_combined_json(all_records, output_file)
    logger.info(f"Validated dataset saved to {output_file}")

    return output_file


def is_valid_record(record):
    """Check if a restaurant record is valid according to the specified criteria."""
    if not isinstance(record.get("id"), int):
        return False
    restaurant_name = record.get("restaurant_name", "")
    if not isinstance(restaurant_name, str):
        return False
    if not re.match(r"^[A-Za-z\s]+$", restaurant_name):
        return False
    rating = record.get("rating")
    if not isinstance(rating, float) or not (1.00 <= rating <= 10.00):
        return False
    distance = record.get("distance_from_me")
    if not isinstance(distance, float) or not (10.00 <= distance <= 1000.00):
        return False
    return True


def save_combined_json(data, output_file: str):
    """Save the combined data to a JSON file."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)


def check_data_validation(file_path):
    """Validate the data using the API's validation endpoint."""
    with open(file_path, 'r') as f:
        data = json.load(f)

    headers = {
        'Content-Type': 'application/json'
    }

    payload = {
        "data": data
    }

    try:
        response = api_client.make_request('POST', BASE_URL + '/test/check-data-validation', headers=headers,
                                           json=payload)
        response.raise_for_status()
        logger.info(f"API Response (/test/check-data-validation): {response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error in request: {str(e)}")


if __name__ == '__main__':
    # initialize API client
    logger.info("Initializing API Client..")
    api_client = APIClient()

    # retrieve and process all datasets
    logger.info("Retrieving and processing datasets from API..")
    validated_file = retrieve_all_datasets()

    # check data validation
    logger.info("Validating Data with API..")
    check_data_validation(validated_file)

    # end the program
    logger.info("Program 1 Completed!")