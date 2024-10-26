from datetime import datetime, timezone, timedelta
from typing import Dict, List
import math
import json
import os
import logging
import requests
import time

# logging Configuration
logger = logging.getLogger("[Program 2]")
logger.setLevel(logging.INFO)
# Use a StreamHandler for console output - faster than FileHandler
console_handler = logging.StreamHandler()
# Use a simple formatter - faster than verbose formatting
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.propagate = False

# Global Variables
if "API_URL" in os.environ:
    BASE_URL = os.environ['API_URL']
else:
    BASE_URL = "https://u8whitimu7.execute-api.ap-southeast-1.amazonaws.com/prod/"
MAX_SIZE = 10
if "INPUT_FILE" in os.environ:
    INPUT_FILE = os.environ['INPUT_FILE']
else:
    INPUT_FILE = 'validated_dataset.json'
if "OUTPUT_DIR" in os.environ:
    OUTPUT_DIR = os.environ['OUTPUT_DIR']
else:
    # for local dev environment testing
    OUTPUT_DIR = './'

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

# obj for managing the Min-Heap
class MinHeap:
    def __init__(self, max_size):
        self.heap = []
        self.max_size = max_size

    def calculate_score(self, restaurant):
        """
        Calculates the score for a restaurant based on the following.

        score = (rating x 10 - distance x 0.5 + sin(id) x 2) x 100 + 0.5
        final_score = round(score / 100, 2)

        Ensure to round the score to 2 decimal places.
        """
        id = restaurant["id"]
        rating = restaurant["rating"]
        distance = restaurant["distance_from_me"]

        # calculate the final score using the formula given
        score = (rating * 10 - distance * 0.5 + math.sin(id) * 2) * 100 + 0.5
        final_score = round(score / 100, 2)

        restaurant["score"] = final_score
        return final_score

    def compare_restaurants(self, a: Dict, b: Dict) -> bool:
        """
        Returns True if restaurant a should be considered "smaller" than restaurant b
        for min heap purposes. Remember we want to keep the largest values.
        """
        if a['score'] != b['score']:
            return a['score'] < b['score']
        if a['rating'] != b['rating']:
            return a['rating'] < b['rating']
        if a['distance_from_me'] != b['distance_from_me']:
            return a['distance_from_me'] < b['distance_from_me']
        return a['restaurant_name'] > b['restaurant_name']

    def heapify_up(self, index: int) -> None:
        """O(log K) operation to maintain heap property upwards"""
        parent = (index - 1) // 2
        while index > 0 and self.compare_restaurants(self.heap[index], self.heap[parent]):
            self.heap[index], self.heap[parent] = self.heap[parent], self.heap[index]
            index = parent
            parent = (index - 1) // 2

    def heapify_down(self, index: int) -> None:
        """O(log K) operation to maintain heap property downwards"""
        min_index = index
        size = len(self.heap)

        while True:
            left = 2 * index + 1
            right = 2 * index + 2

            if left < size and self.compare_restaurants(self.heap[left], self.heap[min_index]):
                min_index = left
            if right < size and self.compare_restaurants(self.heap[right], self.heap[min_index]):
                min_index = right

            if min_index == index:
                break

            self.heap[index], self.heap[min_index] = self.heap[min_index], self.heap[index]
            index = min_index

    def add(self, restaurant: Dict) -> None:
        """O(log K) operation to add a new restaurant"""
        # Calculate score first
        self.calculate_score(restaurant)

        if len(self.heap) < self.max_size:
            # If heap is not full, add and heapify up
            self.heap.append(restaurant)
            self.heapify_up(len(self.heap) - 1)
        else:
            # If heap is full, only add if better than current minimum
            if not self.compare_restaurants(restaurant, self.heap[0]):
                self.heap[0] = restaurant
                self.heapify_down(0)

    def get_top_k(self) -> List[Dict]:
        """O(K log K) operation to sort final results"""
        # Sort by our criteria in reverse order
        return sorted(
            self.heap,
            key=lambda x: (
                x['score'],
                x['rating'],
                x['distance_from_me'],
                x['restaurant_name']
            ),
            reverse=True
        )

def process_top_restaurants(data: List[Dict]) -> List[Dict]:
    """
    Main processing function
    Time Complexity: O(N log K) where N is input size and K is max_size (10)
    Space Complexity: O(K) where K is max_size (10)
    """
    min_heap = MinHeap(MAX_SIZE)

    # Process each restaurant: O(N log K)
    for restaurant in data:
        min_heap.add(restaurant)

    # Get final sorted result: O(K log K) where K = 10, so effectively O(1)
    return min_heap.get_top_k()

def save_results(top_restaurants, output_file):
    # save the top restaurants to topk_results.json file
    with open(output_file, 'w') as f:
        json.dump(top_restaurants, f, indent=4)

    logger.info(f"Top 10 restaurants saved to {output_file}!")


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
        response = api_client.make_request('POST', BASE_URL + '/test/check-topk-sort', headers=headers,
                                           json=payload)
        response.raise_for_status()
        logger.info(f"API Response (/test/check-topk-sort): {response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error in request: {str(e)}")


# main method
def main():
    # load the cleaned dataset from the JSON file
    output_file = os.path.join(OUTPUT_DIR, 'topk_results.json')

    # ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # dataset
    with open(INPUT_FILE, 'r') as file:
        data = json.load(file)

    # process and get top 10 restaurants
    top_restaurants = process_top_restaurants(data)

    # save the results
    save_results(top_restaurants, output_file)

    # validate the results
    check_data_validation(output_file)


if __name__ == '__main__':
    # initialize API client
    logger.info("Initializing API Client..")
    api_client = APIClient()

    # run the main method
    main()
