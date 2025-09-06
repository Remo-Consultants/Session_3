from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import re
import requests
from datetime import datetime, timedelta
import base64
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

# Amadeus API credentials
AMADEUS_API_KEY = os.getenv('AMADEUS_API_KEY')
AMADEUS_API_SECRET = os.getenv('AMADEUS_API_SECRET')

# OpenWeatherMap API key
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

# Google Maps API key
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

@app.route('/')
def index():
    return render_template('index.html', google_maps_api_key=GOOGLE_MAPS_API_KEY)

def clean_and_parse_response(text):
    """Clean and parse the Gemini response to extract JSON, handling trailing commas."""
    try:
        # Remove markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        # Aggressively find JSON object and clean trailing commas
        json_match = re.search(r'\{[\s\S]*\}', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            # Remove trailing commas from objects and arrays
            json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
            return json.loads(json_str)
        else:
            print("No JSON object found in Gemini response.")
            # Fallback for when no JSON is found
            return {
                "destination": "Paris, France",
                "itinerary": "1. Arrive and explore the city center.\n2. Visit famous landmarks.\n3. Enjoy local cuisine and culture.",
                "cuisine": "1. Try local specialties and traditional dishes.",
                "fun_fact": "This destination has amazing culture!",
                "estimated_cost": {
                    "Accommodation": "$100-200/night",
                    "Food": "$50-100/day",
                    "Activities": "$30-80/day",
                    "Transportation": "$20-50/day",
                    "Total": "$500-1000 for 5 days"
                },
                "best_time_to_visit": "Spring and fall offer the best weather",
                "packing_tips": "1. Comfortable walking shoes.\n2. Weather-appropriate clothing.\n3. Essential travel items."
            }
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error in clean_and_parse_response: {e}")
        print(f"Problematic JSON string: {json_str[:500]}...") # Log beginning of problematic string
        # Fallback for JSON decoding errors
        return {
            "destination": "Paris, France",
            "itinerary": "1. Arrive and explore the city center.\n2. Visit famous landmarks.\n3. Enjoy local cuisine and culture.",
            "cuisine": "1. Try local specialties and traditional dishes.",
            "fun_fact": "This destination has amazing culture!",
            "estimated_cost": {
                "Accommodation": "$100-200/night",
                "Food": "$50-100/day",
                "Activities": "$30-80/day",
                "Transportation": "$20-50/day",
                "Total": "$500-1000 for 5 days"
            },
            "best_time_to_visit": "Spring and fall offer the best weather",
            "packing_tips": "1. Comfortable walking shoes.\n2. Weather-appropriate clothing.\n3. Essential travel items."
        }
    except Exception as e:
        print(f"General Error in clean_and_parse_response: {e}")
        # Fallback for any other unexpected errors
        return {
            "destination": "Paris, France",
            "itinerary": "1. Arrive and explore the city center.\n2. Visit famous landmarks.\n3. Enjoy local cuisine and culture.",
            "cuisine": "1. Try local specialties and traditional dishes.",
            "fun_fact": "This destination has amazing culture!",
            "estimated_cost": {
                "Accommodation": "$100-200/night",
                "Food": "$50-100/day",
                "Activities": "$30-80/day",
                "Transportation": "$20-50/day",
                "Total": "$500-1000 for 5 days"
            },
            "best_time_to_visit": "Spring and fall offer the best weather",
            "packing_tips": "1. Comfortable walking shoes.\n2. Weather-appropriate clothing.\n3. Essential travel items."
        }

def get_amadeus_token():
    """Get access token from Amadeus API"""
    try:
        if not AMADEUS_API_KEY or not AMADEUS_API_SECRET:
            print("Amadeus API credentials not found")
            return None
            
        url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'client_credentials',
            'client_id': AMADEUS_API_KEY,
            'client_secret': AMADEUS_API_SECRET
        }
        response = requests.post(url, headers=headers, data=data)
        print(f"Amadeus token response: {response.status_code}")
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            print(f"Token request failed: {response.text}")
            return None
    except Exception as e:
        print(f"Error getting Amadeus token: {e}")
        return None

def search_city_code(city_name):
    """Search for city code using Amadeus API with better error handling and logging"""
    try:
        token = get_amadeus_token()
        if not token:
            print(f"No Amadeus token available for city code search for {city_name}.")
            return None
            
        url = "https://test.api.amadeus.com/v1/reference-data/locations"
        headers = {
            'Authorization': f'Bearer {token}'
        }
        params = {
            'subType': 'CITY',
            'keyword': city_name,
            # 'max': 1 # REMOVED: This parameter is causing the 400 error for this endpoint
        }
        
        response = requests.get(url, headers=headers, params=params)
        print(f"City search response for '{city_name}': {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                print(f"Found IATA code for {city_name}: {data['data'][0]['iataCode']}")
                return data['data'][0]['iataCode']
            else:
                print(f"No IATA code found for {city_name} in Amadeus response data.")
        else:
            print(f"Amadeus City Search API returned non-200 status for {city_name}. Response: {response.text}")
        return None
    except Exception as e:
        print(f"Error searching city code for {city_name}: {e}")
        return None

def search_flights(origin, destination, departure_date, return_date):
    """Search for flights using Amadeus API with fallback data"""
    try:
        token = get_amadeus_token()
        if not token:
            print("No Amadeus token available for flight search. Returning fallback data.")
            return get_fallback_flights(origin, destination, departure_date, return_date)
            
        # Get city codes
        origin_code = search_city_code(origin)
        dest_code = search_city_code(destination)
        
        if not origin_code or not dest_code:
            print(f"Could not find city codes for {origin} ({origin_code}) or {destination} ({dest_code}). Returning fallback flight data.")
            return get_fallback_flights(origin, destination, departure_date, return_date)
            
        print(f"Searching flights: {origin_code} to {dest_code} on {departure_date} to {return_date}")
        
        url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
        headers = {
            'Authorization': f'Bearer {token}'
        }
        params = {
            'originLocationCode': origin_code,
            'destinationLocationCode': dest_code,
            'departureDate': departure_date,
            'returnDate': return_date,
            'adults': 1,
            'max': 5
        }
        
        response = requests.get(url, headers=headers, params=params)
        print(f"Flight search API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            flights = []
            if data.get('data'):
                for offer in data['data'][:3]:
                    price = offer['price']['total']
                    currency = offer['price']['currency']
                    itineraries = offer.get('itineraries', [])
                    if itineraries:
                        segments = itineraries[0].get('segments', [])
                        if segments:
                            airline_code = segments[0].get('carrierCode', 'N/A')
                            airline_name = data.get('dictionaries', {}).get('carriers', {}).get(airline_code, 'Multiple Airlines')
                            
                            departure_airport = segments[0].get('departure', {}).get('iataCode', origin_code)
                            arrival_airport = segments[-1].get('arrival', {}).get('iataCode', dest_code)
                            
                            flights.append({
                                'airline': airline_name,
                                'route': f"{departure_airport} → {arrival_airport}",
                                'price': f"{currency} {price}",
                                'departure': departure_date,
                                'return': return_date,
                                'note': 'Direct flight' if len(segments) == 1 else 'Connecting flight'
                            })
                        else:
                             flights.append({
                                'airline': 'Multiple Airlines',
                                'route': f"{origin_code} → {dest_code}",
                                'price': f"{currency} {price}",
                                'departure': departure_date,
                                'return': return_date,
                                'note': 'Itinerary details not fully available'
                            })
                    else:
                        flights.append({
                            'airline': 'Multiple Airlines',
                            'route': f"{origin_code} → {dest_code}",
                            'price': f"{currency} {price}",
                            'departure': departure_date,
                            'return': return_date,
                            'note': 'Itinerary details not fully available'
                        })
            return flights if flights else get_fallback_flights(origin, destination, departure_date, return_date)
        else:
            print(f"Amadeus Flight Search API returned non-200 status. Response: {response.text}")
            return get_fallback_flights(origin, destination, departure_date, return_date)
    except Exception as e:
        print(f"Error searching flights: {e}")
        return get_fallback_flights(origin, destination, departure_date, return_date)

def get_fallback_flights(origin, destination, departure_date, return_date):
    """Provide fallback flight data when API fails"""
    return [
        {
            'airline': 'Generic Airlines',
            'route': f"{origin} → {destination}",
            'price': '$400-800',
            'departure': departure_date,
            'return': return_date,
            'note': 'Prices vary by airline and booking time. (Fallback Data)'
        },
        {
            'airline': 'Budget Carrier',
            'route': f"{origin} → {destination}",
            'price': '$300-600',
            'departure': departure_date,
            'return': return_date,
            'note': 'Check for additional fees. (Fallback Data)'
        },
        {
            'airline': 'Premium Flights',
            'route': f"{origin} → {destination}",
            'price': '$600-1200',
            'departure': departure_date,
            'return': return_date,
            'note': 'Includes meals and baggage. (Fallback Data)'
        }
    ]

def search_hotels(city_name, check_in, check_out):
    """Search for hotels using Amadeus API with fallback data"""
    try:
        token = get_amadeus_token()
        if not token:
            print("No Amadeus token available for hotel search. Returning fallback data.")
            return get_fallback_hotels(city_name)
            
        # Get city code
        city_code = search_city_code(city_name)
        if not city_code:
            print(f"Could not find city code for {city_name}. Returning fallback hotel data.")
            return get_fallback_hotels(city_name)
            
        print(f"Searching hotels in {city_code} from {check_in} to {check_out}")

        # First, get hotel IDs in the city
        hotel_list_url = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"
        hotel_list_params = {
            'cityCode': city_code,
            'radius': 20, # 20km radius
            'radiusUnit': 'KM'
        }
        hotel_list_response = requests.get(hotel_list_url, headers={'Authorization': f'Bearer {token}'}, params=hotel_list_params)
        print(f"Hotel list by city API response status: {hotel_list_response.status_code} - {hotel_list_response.text}")

        hotel_ids = []
        if hotel_list_response.status_code == 200 and hotel_list_response.json().get('data'):
            for hotel_info in hotel_list_response.json()['data'][:5]: # Get up to 5 hotel IDs
                hotel_ids.append(hotel_info['hotelId'])
        
        hotels = []
        if hotel_ids:
            # Now search for actual offers for these hotels
            for hotel_id in hotel_ids:
                hotel_offer_url = "https://test.api.amadeus.com/v3/shopping/hotel-offers"
                hotel_offer_params = {
                    'hotelIds': hotel_id,
                    'checkInDate': check_in,
                    'checkOutDate': check_out,
                    'adults': 1,
                    'currency': 'USD'
                }
                hotel_offer_response = requests.get(hotel_offer_url, headers={'Authorization': f'Bearer {token}'}, params=hotel_offer_params)
                print(f"Hotel offer search for {hotel_id} status: {hotel_offer_response.status_code}")

                if hotel_offer_response.status_code == 200 and hotel_offer_response.json().get('data'):
                    for offer in hotel_offer_response.json()['data'][0].get('offers', [])[:1]: # Get first offer
                        hotel_name = hotel_offer_response.json()['data'][0].get('hotel', {}).get('name', 'Hotel Name Unknown')
                        price_total = offer.get('price', {}).get('total', 'N/A')
                        currency = offer.get('price', {}).get('currency', '')
                        hotels.append({
                            'name': hotel_name,
                            'rating': 'N/A', # Rating is not directly in offers, would need another API call or static data
                            'price': f"{currency} {price_total}/night",
                            'location': city_name,
                            'amenities': 'WiFi, Breakfast' # Generic for now
                        })
                else:
                    print(f"No offers found for hotel {hotel_id} or API error.")
        
        return hotels if hotels else get_fallback_hotels(city_name)
    except Exception as e:
        print(f"Error searching hotels: {e}")
        return get_fallback_hotels(city_name)

def get_fallback_hotels(city_name):
    """Provide fallback hotel data when API fails"""
    return [
        {
            'name': f'Budget Stay in {city_name}',
            'rating': '4.2/5',
            'price': '$80-150/night',
            'location': 'City Center',
            'amenities': 'WiFi, Breakfast. (Fallback Data)'
        },
        {
            'name': f'Mid-Range Comfort in {city_name}',
            'rating': '4.5/5',
            'price': '$150-250/night',
            'location': 'Near Attractions',
            'amenities': 'WiFi, Pool, Restaurant. (Fallback Data)'
        },
        {
            'name': f'Luxury Retreat in {city_name}',
            'rating': '4.8/5',
            'price': '$250-500/night',
            'location': 'Prime Location',
            'amenities': 'WiFi, Spa, Fine Dining. (Fallback Data)'
        }
    ]

def get_weather_forecast(city_name, start_date, end_date):
    """Get weather forecast using OpenWeatherMap API with better formatting and unique dates"""
    try:
        if not OPENWEATHER_API_KEY:
            print("OpenWeatherMap API key not found. Returning fallback weather data.")
            return get_fallback_weather(city_name)
            
        # Get coordinates for the city
        geocode_url = "http://api.openweathermap.org/geo/1.0/direct"
        geocode_params = {
            'q': city_name,
            'limit': 1,
            'appid': OPENWEATHER_API_KEY
        }
        
        geocode_response = requests.get(geocode_url, params=geocode_params)
        if geocode_response.status_code != 200 or not geocode_response.json():
            print(f"Geocoding failed for {city_name}. Status: {geocode_response.status_code}, Response: {geocode_response.text}")
            return get_fallback_weather(city_name)
            
        geocode_data = geocode_response.json()
        lat = geocode_data[0]['lat']
        lon = geocode_data[0]['lon']
        
        # Get weather forecast (5-day forecast, 3-hour step)
        weather_url = "https://api.openweathermap.org/data/2.5/forecast"
        weather_params = {
            'lat': lat,
            'lon': lon,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric'
        }
        
        weather_response = requests.get(weather_url, params=weather_params)
        if weather_response.status_code != 200:
            print(f"OpenWeatherMap API returned non-200 status. Response: {weather_response.text}")
            return get_fallback_weather(city_name)
            
        weather_data = weather_response.json()
        forecast = []
        seen_dates = set()
        
        if weather_data.get('list'):
            # Iterate through forecasts, taking one entry per day
            for item in weather_data['list']:
                date_obj = datetime.fromtimestamp(item['dt'])
                date_str = date_obj.strftime('%Y-%m-%d')
                
                if date_str not in seen_dates and len(forecast) < 5: # Limit to 5 unique days
                    seen_dates.add(date_str)
                    temp = round(item['main']['temp'])
                    description = item['weather'][0]['description']
                    icon = item['weather'][0]['icon']
                    
                    forecast.append({
                        'date': date_str,
                        'temperature': temp,
                        'description': description.title(),
                        'icon': icon
                    })
        
        return forecast if forecast else get_fallback_weather(city_name)
    except Exception as e:
        print(f"Error getting weather forecast for {city_name}: {e}")
        return get_fallback_weather(city_name)

def get_fallback_weather(city_name):
    """Provide fallback weather data when API fails"""
    base_date = datetime.now()
    forecast = []
    for i in range(5):
        date = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
        forecast.append({
            'date': date,
            'temperature': 20 + (i % 5), # Vary temp slightly
            'description': 'Partly Cloudy (Fallback)',
            'icon': '02d'
        })
    return forecast

@app.route('/generate_itinerary', methods=['POST'])
def generate_itinerary():
    try:
        # Get user inputs
        user_mood = request.form['mood']
        user_budget = request.form['budget']
        user_duration = request.form['duration']
        user_travel_style = request.form['travel_style']
        user_origin = request.form['origin_city']
        user_travel_means = request.form['travel_means']
        user_hotel_preference = request.form['hotel_preference']
        user_departure_date = request.form['departure_date']
        
        # Create prompt for Gemini
        prompt = f"""
        You are an expert travel planner. Create a personalized travel itinerary based on these preferences:
        
        Travel Mood: {user_mood}
        Budget: ${user_budget}
        Duration: {user_duration} days
        Travel Style: {user_travel_style}
        Origin: {user_origin}
        Travel Means: {user_travel_means}
        Hotel Preference: {user_hotel_preference}
        Departure Date: {user_departure_date}
        
        Create a detailed travel plan in JSON format with the following structure:
        {{
            "destination": "Specific city and country name",
            "itinerary": "Detailed day-by-day itinerary with specific activities, times, and locations. Format as a numbered list with clear day separations. Each day should be a separate line item.",
            "cuisine": "Specific local dishes and restaurants to try with names and specialties. Format as a numbered list with restaurant names and dish descriptions. Each cuisine item should be a separate line item.",
            "fun_fact": "Interesting and specific fact about the destination that most people don't know",
            "estimated_cost": {{
                "Accommodation": "Detailed cost breakdown with specific price ranges",
                "Food": "Cost for meals and dining with specific amounts",
                "Activities": "Cost for attractions and experiences with specific prices",
                "Transportation": "Local transport costs with specific amounts",
                "Total": "Total estimated cost with clear breakdown"
            }},
            "best_time_to_visit": "Specific months and reasons why, tailored to the destination",
            "packing_tips": "Specific items to pack based on the destination and season, formatted as a numbered list. Each packing tip should be a separate line item."
        }}
        
        Make the response detailed, specific, and practical. Include actual place names, restaurant names, and specific activities. Ensure all lists are properly formatted with clear numbering, and do NOT include any trailing commas in the JSON.
        """
        
        # Generate response using Gemini
        response = model.generate_content(prompt)
        itinerary_data = clean_and_parse_response(response.text)
        
        # Get additional data
        destination = itinerary_data.get('destination', 'Unknown Destination')
        city_name = destination.split(',')[0].strip() # Extract city name from destination
        
        # Calculate return date
        departure_date = datetime.strptime(user_departure_date, '%Y-%m-%d')
        return_date = (departure_date + timedelta(days=int(user_duration))).strftime('%Y-%m-%d')
        
        print(f"Searching flights: {user_origin} to {city_name} on {user_departure_date} to {return_date}")
        flights_data = search_flights(user_origin, city_name, user_departure_date, return_date)
        print(f"Searching hotels in {city_name} from {user_departure_date} to {return_date}")
        hotels_data = search_hotels(city_name, user_departure_date, return_date)
        print(f"Getting weather forecast for {city_name} from {user_departure_date} to {return_date}")
        weather_data = get_weather_forecast(city_name, user_departure_date, return_date)
        
        # Return data in the format expected by frontend
        response_data = {
            'success': True,
            'destination': destination,
            'description': f"Your perfect {user_mood} getaway awaits!",
            'itinerary': itinerary_data.get('itinerary', 'Itinerary not available'),
            'cuisine': itinerary_data.get('cuisine', 'Local cuisine information not available'),
            'estimated_cost': itinerary_data.get('estimated_cost', {}),
            'best_time_to_visit': itinerary_data.get('best_time_to_visit', 'Year-round destination'),
            'packing_tips': itinerary_data.get('packing_tips', 'Pack according to season'),
            'flight_options': flights_data,
            'hotel_options': hotels_data,
            'weather_forecast': weather_data
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error generating itinerary: {e}")
        return jsonify({'success': False, 'error': f'Error generating itinerary: {str(e)}'}), 500

@app.route('/surprise_destination', methods=['POST'])
def surprise_destination():
    try:
        # Random surprise destinations
        surprise_destinations = [
            "Kyoto, Japan",
            "Santorini, Greece", 
            "Reykjavik, Iceland",
            "Marrakech, Morocco",
            "Bali, Indonesia",
            "Cape Town, South Africa",
            "Prague, Czech Republic",
            "Queenstown, New Zealand",
            "Dubrovnik, Croatia",
            "Banff, Canada"
        ]
        
        # Pick a random destination
        random_destination = random.choice(surprise_destinations)
        
        # Create a surprise prompt for Gemini
        prompt = f"""
        You are an expert travel planner. Create a surprise travel itinerary for: {random_destination}
        
        This is a surprise destination, so make it exciting and unexpected! Create a detailed travel plan in JSON format with the following structure:
        {{
            "destination": "{random_destination}",
            "itinerary": "Detailed day-by-day itinerary with specific activities, times, and locations for 5 days. Format as a numbered list with clear day separations. Each day should be a separate line item.",
            "cuisine": "Specific local dishes and restaurants to try with names and specialties. Format as a numbered list with restaurant names and dish descriptions. Each cuisine item should be a separate line item.",
            "fun_fact": "Interesting and specific fact about the destination that most people don't know",
            "estimated_cost": {{
                "Accommodation": "Detailed cost breakdown with specific price ranges",
                "Food": "Cost for meals and dining with specific amounts",
                "Activities": "Cost for attractions and experiences with specific prices",
                "Transportation": "Local transport costs with specific amounts",
                "Total": "Total estimated cost with clear breakdown"
            }},
            "best_time_to_visit": "Specific months and reasons why, tailored to the destination",
            "packing_tips": "Specific items to pack based on the destination and season, formatted as a numbered list. Each packing tip should be a separate line item."
        }}
        
        Make the response detailed, specific, and practical. Include actual place names, restaurant names, and specific activities. Ensure all lists are properly formatted with clear numbering, and do NOT include any trailing commas in the JSON.
        """
        
        # Generate response using Gemini
        response = model.generate_content(prompt)
        itinerary_data = clean_and_parse_response(response.text)
        
        # Get additional data
        destination = itinerary_data.get('destination', random_destination)
        city_name = destination.split(',')[0].strip() # Extract city name from destination
        
        # Search for flights, hotels, and weather (using default dates)
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        return_date = (datetime.now() + timedelta(days=6)).strftime('%Y-%m-%d')
        
        print(f"Searching flights for surprise: New York to {city_name} on {tomorrow} to {return_date}")
        flights_data = search_flights("New York", city_name, tomorrow, return_date)
        print(f"Searching hotels for surprise in {city_name} from {tomorrow} to {return_date}")
        hotels_data = search_hotels(city_name, tomorrow, return_date)
        print(f"Getting weather forecast for surprise in {city_name} from {tomorrow} to {return_date}")
        weather_data = get_weather_forecast(city_name, tomorrow, return_date)
        
        # Return data in the format expected by frontend
        response_data = {
            'success': True,
            'destination': destination,
            'description': f"Surprise! Your next adventure awaits in {destination}!",
            'itinerary': itinerary_data.get('itinerary', 'Itinerary not available'),
            'cuisine': itinerary_data.get('cuisine', 'Local cuisine information not available'),
            'estimated_cost': itinerary_data.get('estimated_cost', {}),
            'best_time_to_visit': itinerary_data.get('best_time_to_visit', 'Year-round destination'),
            'packing_tips': itinerary_data.get('packing_tips', 'Pack according to season'),
            'flight_options': flights_data,
            'hotel_options': hotels_data,
            'weather_forecast': weather_data
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logging.exception("Error generating surprise destination")
        return jsonify({'success': False, 'error': 'An internal error occurred while generating the surprise destination.'}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)