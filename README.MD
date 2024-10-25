# CSIT OCT 2024 - Mini Challenge

## Table of Content
- [Introduction](#introduction)
- [API Endpoints](#api-endpoints)
- [Build](#build)
- [Run](#run)
- [Test](#test)

## Introduction

[CSIT OCT 2024 - Mini Challenge](https://oct-2024-mini-challenge.csit-events.sg/)

### API Endpoints

API_URL:
```text
https://u8whitimu7.execute-api.ap-southeast-1.amazonaws.com/prod/{ENDPOINT}
```

### Program 1

> **_Important!:_**
There is a rate limit in place for downloading data, requiring a 10-second wait between each request.

Download the dataset from Victor's server and discard any broken records.

| Key                | Type                                      | Description                                   |
|--------------------|-------------------------------------------|-----------------------------------------------|
| `id`               | integer                                   | Identifier of the restaurant                  |
| `restaurant_name`  | string (alphabets and spaces only)        | Name of the restaurant                        |
| `rating`           | float (range: 1.00 to 10.00)              | Rating of the restaurant                      |
| `distance_from_me` | float (range: 10.00 to 1000.00)           | Distance from me to the restaurant            |

Save the resulting cleaned dataset to a JSON file named **validated_dataset.json**.

### Program 2

Write an algorithm to sort the cleaned data from program 1 according to the following criteria, in order of priority:
- Score (Sort in descending order)
- Rating (Sort in descending order)
- Distance (Sort in descending order)
- Restaurant name (Sort alphabetically in ascending order)

Calculate the score for each restaurant, using the formula below:
```
score = (rating x 10 - distance x 0.5 + sin(id) x 2) x 100 + 0.5
final_score = round(score / 100, 2)
  
Ensure to round the score to 2 decimal places.
```

Select the top 10 entries and save it to a JSON file named **topk_results.json**.
The output of the JSON file should be in the following structure.

```json
[
    {
      "id": 1,
      "restaurant_name": "The Great Restaurant",
      "rating": 9.94,
      "distance_from_me": 150.31,
      "score": 94.53
    },
    {
      "id": 2,
      "restaurant_name": "Cuisine Delight",
      "rating": 9.20,
      "distance_from_me": 120.00,
      "score": 91.25
    },
    {
      "id": 3,
      "restaurant_name": "The Amazing Eatery",
      "rating": 8.76,
      "distance_from_me": 200.45,
      "score": 89.10
    }
    // There should be 10 restaurant entries in total.
]
```

## Build

### Program 1

```bash
docker build -t program_one:latest -f .docker/Dockerfile_ProgramOne .
```

### Program 2
```bash
docker build -t program_two:latest -f .docker/Dockerfile_ProgramTwo .
```

## Run

### Program 1

*For mac*
```bash
docker run -it -v /tmp/data:/app/data program_one:latest
```

*For Windows*
```bash
docker run -it -v ${pwd}/data:/app/data program_one:latest
```

### Program 2

*For mac*
```bash
docker run -it -v /tmp/data:/app/data program_two:latest
```

*For Windows*
```bash
docker run -it -v ${pwd}/data:/app/data program_two:latest
```

## Test

### Program 1

> POST /test/check-data-validation

```json
[
    {
        "id": 1,
        "restaurant_name": "Delectable Riley Elsinore Spot",
        "rating": 1.28,
        "distance_from_me": 340.26
    },
    {
        "id": 4,
        "restaurant_name": "Briny Dorcas Neverland Place",
        "rating": 2.01,
        "distance_from_me": 663.46
    },
    {
        "id": 6,
        "restaurant_name": "Fresh Rachel Xanadu Bar",
        "rating": 1.03,
        "distance_from_me": 659.4
    },
    {
        "id": 7,
        "restaurant_name": "Buttery Eunice Bandle City Corner",
        "rating": 8.68,
        "distance_from_me": 270.48
    },
    ...
]
```

Result: 413 Request entity too large
```json
{
    "message": "Request Too Long"
}
```

*Comments:*

*I don't know why I'm unable to validate this part. Based on the 
API description, I'm supposed to "Submit the final results from 
Program 1 to validate against. Use this API to test your program 
before submitting".*

*There are total of 5 pages of datasets. If I combined all 5 pages
and cleaned the data, I will still get around 6.58MB of json data..
thus the 413 error.*

*It will be good if there's more information provided on this.*

### Program 2

> POST /test/check-topk-sort

POST Body: Final sorted dataset
```json
{
    "data": [
    {
        "id": 7353,
        "restaurant_name": "Buttery Anna Bilgewater Inn",
        "rating": 9.97,
        "distance_from_me": 11.94,
        "score": 95.72
    },
    {
        "id": 92698,
        "restaurant_name": "Sour Logan Noxus Joint",
        "rating": 9.79,
        "distance_from_me": 11.61,
        "score": 93.75
    },
    {
        "id": 11619,
        "restaurant_name": "Fresh Gideon Brigadoon Shed",
        "rating": 9.92,
        "distance_from_me": 14.95,
        "score": 93.7
    },
    {
        "id": 26587,
        "restaurant_name": "Succulent Rebecca Thedas Inn",
        "rating": 9.93,
        "distance_from_me": 13.24,
        "score": 93.27
    },
    {
        "id": 50701,
        "restaurant_name": "Bland Tryphena Summerset Stand",
        "rating": 9.72,
        "distance_from_me": 13.9,
        "score": 92.09
    },
    {
        "id": 65446,
        "restaurant_name": "Lively Joel Gotham City Shop",
        "rating": 9.77,
        "distance_from_me": 12.73,
        "score": 92.01
    },
    {
        "id": 77962,
        "restaurant_name": "Bitter Amelia Kalimdor Shop",
        "rating": 9.71,
        "distance_from_me": 11.41,
        "score": 91.87
    },
    {
        "id": 22658,
        "restaurant_name": "Creamy Elijah Oz Depot",
        "rating": 9.92,
        "distance_from_me": 18.43,
        "score": 91.47
    },
    {
        "id": 59126,
        "restaurant_name": "Refreshing David Pandaria Spot",
        "rating": 9.76,
        "distance_from_me": 16.18,
        "score": 91.4
    },
    {
        "id": 68733,
        "restaurant_name": "Gourmet Tryphosa Dalaran Cantina",
        "rating": 9.73,
        "distance_from_me": 17.14,
        "score": 90.62
    }
]
}
```

```json
{
    "status": 200,
    "error": "",
    "message": "Success! Results matched"
}
```