# 🌟 AI-Powered Travel Genie

An intelligent travel planning application that leverages the power of Gemini AI to create personalized itineraries, discover local cuisine, and provide essential travel information, integrated with real-time flight, hotel, and weather data.

## ✨ Features

-   **Personalized Itineraries**: Users input their mood, budget, duration, travel style, origin, travel means, hotel preference, and departure date to receive a tailored travel plan.
-   **AI-Suggested Destinations**: Gemini AI recommends unique destinations based on user preferences.
-   **Daily Itinerary**: Detailed day-by-day plans with activities, times, and locations.
-   **Local Cuisine Suggestions**: Discover specific local dishes and restaurants.
-   **Fun Facts**: Interesting facts about the chosen destination.
-   **Estimated Cost Breakdown**: Transparent breakdown of accommodation, food, activities, and transportation costs.
-   **Best Time to Visit & Packing Tips**: Seasonal recommendations and a comprehensive packing list.
-   **Real-time Flight Options**: Integrates with Amadeus API to provide flight details from the origin to the destination.
-   **Top Hotel Options**: Fetches hotel suggestions using Amadeus API, including name, rating, price, and location.
-   **Weather Forecast**: Provides a 5-day weather forecast for the destination using OpenWeatherMap API, including temperature, description, and icons.
-   **Interactive Map**: Google Maps integration to visualize the destination (placeholder for full interactive features).
-   **"🎲 Surprise Me!" Button**: Get a random destination and itinerary for an unexpected adventure.
-   **Modern & Responsive UI**: Built with Flask, HTML, CSS (Poppin's font, Font Awesome icons), providing a visually appealing and easy-to-use interface.

## 🚀 Flow

1.  **User Input**: The user fills out a form on the frontend with their travel preferences.
2.  **Backend Processing**:
    *   Flask receives the user inputs.
    *   A prompt is dynamically constructed and sent to the **Gemini API**.
    *   Gemini generates the core travel itinerary, cuisine, costs, and tips in a structured JSON format.
    *   The application then calls external APIs:
        *   **Amadeus API** for searching flights and hotels (requires city code lookup).
        *   **OpenWeatherMap API** for fetching a 5-day weather forecast.
    *   All gathered data is combined.
3.  **Frontend Display**: The processed and combined data is sent back to the Flask UI, where it's beautifully rendered in a single-screen, card-based layout.
4.  **Interactive Features**: Users can save/share itineraries or get a "Surprise Me!" destination.

## 🛠️ Technologies Used

### Frontend
-   **HTML5**: Structure of the web pages.
-   **CSS3**: Styling with a modern design inspired by ThemeWagon's "Tour" template.
    -   Google Fonts (Poppins)
    -   Font Awesome (icons)
-   **JavaScript**: Dynamic content rendering, form handling, and API integration.
-   **Google Maps API**: For interactive destination maps.

### Backend
-   **Python**: Core programming language.
-   **Flask**: Web framework for building the backend API.
-   **Google Generative AI (Gemini API)**: For generating personalized travel content.
-   **Python-dotenv**: For securely managing environment variables (API keys).
-   **Requests**: HTTP library for making API calls to external services.
-   **Amadeus API (via `requests`)**: For flight search and hotel listing.
-   **OpenWeatherMap API (via `requests`)**: For weather forecasts.

## ⚙️ Setup and Installation

### 1. Clone the Repository (if applicable)
```bash
# If you have a git repository, clone it first
# git clone <your-repo-url>
# cd <your-repo-name>
```

### 2. Install Dependencies
Ensure you have Python 3.8+ installed. It's recommended to use a virtual environment.
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install Flask google-generativeai python-dotenv requests beautifulsoup4 lxml
```
_Note: `beautifulsoup4` and `lxml` were included in `pyproject.toml` earlier, but the app does not directly use them in the current version for parsing HTML. They are typically used for web scraping, which is not part of the current API integration. You can install them if you intend to add web scraping capabilities in the future._

### 3. Configure API Keys
Create a `.env` file in your project's root directory with the following content:

```ini
GEMINI_API_KEY=your_gemini_api_key_here
AMADEUS_API_KEY=your_amadeus_api_key_here
AMADEUS_API_SECRET=your_amadeus_api_secret_here
OPENWEATHER_API_KEY=your_openweathermap_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

**Where to get your API keys:**
-   **Gemini API**: [Google AI Studio](https://makersuite.google.com/app/apikey)
-   **Amadeus API**: [Amadeus for Developers](https://developers.amadeus.com/) (Sign up, create an application, and get your API Key and Secret). Remember to use the `TEST` environment for development.
-   **OpenWeatherMap API**: [OpenWeatherMap](https://openweathermap.org/api) (Sign up for a free account and get your API key).
-   **Google Maps API**: [Google Cloud Console](https://console.cloud.google.com/projectselector2/apiui/credential) (Enable the Maps JavaScript API and Geocoding API, then create an API key).

### 4. Run the Application
```bash
flask run
```
or if your main file is `app.py`:
```bash
python app.py
```

The application will typically run on `http://127.0.0.1:5000/`.

## 🤝 Usage

1.  Open your web browser and navigate to `http://127.0.0.1:5000/`.
2.  Fill in your travel preferences in the form on the hero section.
3.  Click "Generate My Trip" to get a personalized itinerary, or "Surprise Me!" for a random destination.
4.  View the detailed results including itinerary, cuisine, costs, weather, flights, hotels, and a map.

## 📄 License

[Specify your license here, e.g., MIT License]