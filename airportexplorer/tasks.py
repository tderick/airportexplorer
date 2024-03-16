from celery import shared_task
from airportexplorer.database import get_database


def countries_ident():
    pipeline = [
        { "$unwind": "$regions" },  # Unwind the regions array
        { "$unwind": "$regions.airports" },  # Unwind the airports array within each region
        { 
            "$match": { 
                "regions.airports.fivebestreviews": { "$exists": False },  # Filter airports without the "fivebestreviews" array
                "regions.airports.fiveworstreview": { "$exists": False }  # Filter airports without the "fiveworstreview" array
            } 
        },
        { "$project": { "_id": 0, "ident": "$regions.airports.ident" } }  # Project the airport ident field
    ]

    return get_database().countries.aggregate(pipeline)

@shared_task(ignore_result=False)
def compute_reviews_and_rating():
    countries = countries_ident()
    
    for country in countries:
        try:
            airport_ident = country["ident"]
            best_reviews = top_5_best_review(airport_ident)
            worst_reviews = top_5_worst_review(airport_ident)
            average_rating = airport_average_rating(airport_ident)

            get_database().countries.update_one(
                {"regions.airports.ident": airport_ident},
                {
                    "$unset": {
                    "regions.$[].airports.$[].fivebestreviews": "",
                        "regions.$[].airports.$[].fiveworstreview": "",
                        "regions.$[].airports.$[].average_rating": ""
                    }
                }
            )
            
            get_database().countries.update_one(
                {"regions.airports.ident": airport_ident},
                {
                    "$push": {
                        "regions.$[].airports.$[].fivebestreviews": best_reviews,
                        "regions.$[].airports.$[].fiveworstreview": worst_reviews,
                        "regions.$[].airports.$[].average_rating": average_rating
                    }
                }
            )
            # update_result = database.countries.update_many(
            #     {"regions.airports.name": {"$regex": name, "$options": 'i'}},
            #     {"$push": {"regions.$[].airports.$[].reviews": review['_id']}}
            # )
            #    get_database().countries.update_one(
            #                     {"code": country_code, "regions.code": region_code},
            #                     {"$push": {"regions.$.airports": airport_data}},
            #                 )
            print(airport_ident, best_reviews, worst_reviews, average_rating)
        
        except Exception as e:
            print("Error", e)
            continue

def top_5_best_review(airport_code):
    pipeline = [
        {"$match": {"airport": airport_code}},  # Match reviews for the specific airport
        {"$sort": {"overall_rating": -1}},  # Sort reviews by overall rating in descending order
        {"$limit": 5},  # Limit the results to 5
        {
            "$project": {
                "_id": 1,
                "title": 1,
                "content": 1,
                "author": 1,
                "author_country": 1,
                "date": 1
            }
        }
    ]

    return list(get_database().reviews.aggregate(pipeline))

def top_5_worst_review(airport_code: str):
    pipeline = [
        {"$match": {"airport": airport_code}},
        {"$sort": {"overall_rating": 1}}, 
        {"$limit": 5},
        {
            "$project": {
                "_id": 1,
                "title": 1,
                "content": 1,
                "author": 1,
                "author_country": 1,
                "date": 1
            }
        }
    ]

    return list(get_database().reviews.aggregate(pipeline))


def airport_average_rating(airport_code: str):
    pipeline = [
    {"$match": {"airport": airport_code}},  # Match reviews for the specific airport
    {"$group": {
        "_id": "$airport",
        "average_queuing_rating": {"$avg": "$queuing_rating"},
        "average_terminal_cleanliness_rating": {"$avg": "$terminal_cleanliness_rating"},
        "average_terminal_seating_rating": {"$avg": "$terminal_seating_rating"},
        "average_terminal_signs_rating": {"$avg": "$terminal_signs_rating"},
        "average_food_beverages_rating": {"$avg": "$food_beverages_rating"},
        "average_airport_shopping_rating": {"$avg": "$airport_shopping_rating"},
        "average_wifi_connectivity_rating": {"$avg": "$wifi_connectivity_rating"},
        "average_airport_staff_rating": {"$avg": "$airport_staff_rating"}
    }}
    ]

    return list(get_database().reviews.aggregate(pipeline))
