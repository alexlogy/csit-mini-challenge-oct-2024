from datetime import datetime, timezone, timedelta
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

    def heapify(self, index, heap_size):
        """
        restores the min-heap property by ensuring the smallest element
        is always at the root. This method compares the current node with
        its children and swaps them if necessary, then recurses down the heap.

        param index: index of the current node
        param heap_size: size of the heap
        """
        smallest = index
        left = 2 * index + 1    # left child index
        right = 2 * index + 2   # right child index

        def compare_restaurants(a, b):
            if a['score'] != b['score']:
                return a['score'] < b['score']
            if a['rating'] != b['rating']:
                return a['rating'] < b['rating']
            if a['distance_from_me'] != b['distance_from_me']:
                return a['distance_from_me'] < b['distance_from_me']
            return a['restaurant_name'] > b['restaurant_name']

        # check if the left child is smaller than the current node
        if left < heap_size and self.heap[left]['score'] < self.heap[smallest]['score']:
            smallest = left
        # check if the right child is smaller than the current node
        if right < heap_size and self.heap[right]['score'] < self.heap[smallest]['score']:
            smallest = right

        if smallest != index:
            self.heap[index], self.heap[smallest] = self.heap[smallest], self.heap[index]
            self.heapify(smallest, heap_size)

    def add(self, restaurant):
        """
        adds a new restaurant to the heap and maintains the heap property. If the heap exceeds
        the maximum size (10), the smallest element is removed to keep only the top 10 entries.

        param restaurant: restaurant data
        """

        # calculate the score for the restaurant and add it to the heap
        self.calculate_score(restaurant)
        self.heap.append(restaurant)

        # maintain heap property upwards
        i = len(self.heap) - 1

        def compare_restaurants(a, b):
            if a['score'] != b['score']:
                return a['score'] < b['score']
            if a['rating'] != b['rating']:
                return a['rating'] < b['rating']
            if a['distance_from_me'] != b['distance_from_me']:
                return a['distance_from_me'] < b['distance_from_me']
            return a['restaurant_name'] > b['restaurant_name']

        while i > 0 and self.heap[i]['score'] < self.heap[(i - 1) // 2]['score']:
            # swap with parent if the current score is smaller
            self.heap[i], self.heap[(i - 1) // 2] = self.heap[(i - 1) // 2], self.heap[i]
            i = (i - 1) // 2    # move up to the parent

        # remove smallest element if heap exceeds max size
        if len(self.heap) > self.max_size:
            self.heap[0] = self.heap.pop()  # replace root element with last element and pop last element
            self.heapify(0, len(self.heap))  # restore heap property from the root element down

    def get_top_k(self):
        '''
        sort the cleaned data from program 1 according to the following criteria, in order of priority:
        1. Score (Sort in descending order)
        2. Rating (Sort in descending order)
        3. Distance (Sort in descending order)
        4. Restaurant name (Sort alphabetically in ascending order)
        '''
        def custom_sort_key(restaurant):
            return (
                restaurant['score'],  # sort by score (descending)
                restaurant['rating'],  # sort by rating (descending)
                restaurant['distance_from_me'],  # sort by distance (descending)
                -ord(restaurant['restaurant_name'][0])  # sort by restaurant name (ascending)
            )

        # sort the heap using the custom sorting function above
        self.heap.sort(key=custom_sort_key, reverse=True)
        return self.heap


# method to load the restaurant data, process, and save top 10 results
def process_top_restaurants(data):
    """
    processes the restaurant data to find the top 10 restaurants based on the
    calculated score, rating, distance, and name using a Min-Heap. The results
    are saved to a JSON file.

    param data: list of restaurant dictionaries
    param max_size: mMaximum size of the heap (default is 10)
    """

    # initialize the MinHeap with the specified max size
    min_heap = MinHeap(MAX_SIZE)

    # add each restaurant to the heap
    for restaurant in data:
        min_heap.add(restaurant)

    # get the top 10 restaurants sorted by score, rating, distance, and name
    top_restaurants = min_heap.get_top_k()

    return top_restaurants

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
