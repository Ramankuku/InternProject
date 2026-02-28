import googlemaps
from geopy.distance import geodesic
import random
from dotenv import load_dotenv
import os
# load_dotenv()
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


gmaps = googlemaps.Client(key=GOOGLE_API_KEY)


def get_nearest_hospitals(user_location_name, radius=5000):
    geocode_result = gmaps.geocode(user_location_name)

    if not geocode_result:
        return "Location not found"

    user_latlng = geocode_result[0]['geometry']['location']
    user_coords = (user_latlng['lat'], user_latlng['lng'])

    places_result = gmaps.places_nearby(
        location=user_coords,
        radius=radius,
        type='hospital'
    )

    hospitals = []

    for place in places_result.get('results', []):
        hospital_lat = place['geometry']['location']['lat']
        hospital_lng = place['geometry']['location']['lng']
        hospital_coords = (hospital_lat, hospital_lng)

        distance_km = geodesic(user_coords, hospital_coords).km

        additional_info = {
                "icu_beds_available": random.randint(0, 20),
                "doctor_available": random.choice(["Yes", "No"]),
                "open_24x7": random.choice(["Yes", "No"])
            }

        photo_url = None
        if "photos" in place:
            photo_reference = place["photos"][0]["photo_reference"]
            photo_url = (
                "https://maps.googleapis.com/maps/api/place/photo"
                f"?maxwidth=400"
                f"&photo_reference={photo_reference}"
                f"&key={GOOGLE_API_KEY}"
            )
        place_id = place.get("place_id")
        url = f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else "N/A"

        hospitals.append({
            "name": place.get("name"),
            "address": place.get("vicinity"),
            "rating": place.get("rating", "No rating"),
            "distance_km": round(distance_km, 2),
            "photo_url": photo_url,
            "url": url,
            
            "icu_beds_available":additional_info["icu_beds_available"],
            "doctor_available":additional_info["doctor_available"],
            "open_24x7":additional_info["open_24x7"]
        })

    return hospitals

def get_speciality_hospitals(user_location_name, specialty=None, radius=5000):
    
    geocode_result = gmaps.geocode(user_location_name)

    if not geocode_result:
        return "Location not found"

    user_latlng = geocode_result[0]['geometry']['location']
    user_coords = (user_latlng['lat'], user_latlng['lng'])

    search_params = {
        "location": user_coords,
        "radius": radius,
        "type": "hospital"
    }

    if specialty:
        search_params["keyword"] = specialty

    places_result = gmaps.places_nearby(**search_params)

    hospitals = []

    for place in places_result.get('results', []):
        hospital_lat = place['geometry']['location']['lat']
        hospital_lng = place['geometry']['location']['lng']
        hospital_coords = (hospital_lat, hospital_lng)

        distance_km = geodesic(user_coords, hospital_coords).km
        additional_info = {
                "icu_beds_available": random.randint(0, 20),
                "doctor_available": random.choice(["Yes", "No"]),
                "open_24x7": random.choice(["Yes", "No"])
            }

        photo_url = None
        if "photos" in place:
            photo_reference = place["photos"][0]["photo_reference"]
            photo_url = (
                "https://maps.googleapis.com/maps/api/place/photo"
                f"?maxwidth=400"
                f"&photo_reference={photo_reference}"
                f"&key={GOOGLE_API_KEY}"
            )

        place_id = place.get("place_id")
        url = f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else "N/A"

        hospitals.append({
            "name": place.get("name"),
            "address": place.get("vicinity"),
            "rating": place.get("rating", "No rating"),
            "distance_km": round(distance_km, 2),
            "photo_url": photo_url,
            "url": url,

            "icu_beds_available":additional_info["icu_beds_available"],
            "doctor_available":additional_info["doctor_available"],
            "open_24x7":additional_info["open_24x7"]

        })

    return hospitals


def main():

    use1 = get_nearest_hospitals('gurugram sector 57')
    for i in use1:
        print(i['name'], i['address'], i['rating'], i['distance_km'], i['photo_url'], i['url'])





if __name__ == "__main__":
    main()