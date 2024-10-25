import math
import json
import os
import logging

# Logging Configuration
logger = logging.getLogger("[Program 2]")
logging.basicConfig(level=logging.INFO)

# Global Variables
MAX_SIZE = 10
if "INPUT_FILE" in os.environ:
    INPUT_FILE = os.environ['INPUT_FILE']
else:
    INPUT_FILE = '../program_one/validated/validated_dataset.json'
if "OUTPUT_DIR" in os.environ:
    OUTPUT_DIR = os.environ['OUTPUT_DIR']
else:
    # for local dev environment testing
    OUTPUT_DIR = 'output'

# Class for managing the Min-Heap
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
        while i > 0 and self.heap[i]['score'] < self.heap[(i - 1) // 2]['score']:
            # swap with parent if the current score is smaller
            self.heap[i], self.heap[(i - 1) // 2] = self.heap[(i - 1) // 2], self.heap[i]
            i = (i - 1) // 2    # move up to the parent

        # remove smallest element if heap exceeds max size
        if len(self.heap) > self.max_size:
            self.heap[0] = self.heap.pop()  # replace root element with last element and pop last element
            self.heapify(0, len(self.heap))  # restore heap property from the root element down

    def get_top_k(self):
        """
        returns the top K restaurants sorted by score.
        Since the heap is only partially sorted (smallest on top), we sort
        the heap before returning the top entries.
        """
        self.heap.sort(key=lambda x: x['score'], reverse=True)

        return self.heap


# Function to load the restaurant data, process, and save top 10 results
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
    # Save the top restaurants to a JSON file
    with open(output_file, 'w') as f:
        json.dump(top_restaurants, f, indent=4)

    logger.info(f"Top 10 restaurants saved to {output_file}!")


def main():
    # load the cleaned dataset from the JSON file
    output_file = os.path.join(OUTPUT_DIR, 'topk_results.json')

    # ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # dataset
    with open(INPUT_FILE, 'r') as file:
        data = json.load(file)

    # Process and get top 10 restaurants
    top_restaurants = process_top_restaurants(data)
    # save the results
    save_results(top_restaurants, output_file)


if __name__ == '__main__':
    main()