import logging
import requests
import json
import os
import time
from mcp.server.fastmcp import FastMCP, Context
from datetime import datetime
from pprint import pprint

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("pyyan")

# Initialize FastMCP server
mcp = FastMCP("Prokerala MCP")

# Prokerala API credentials
CLIENT_ID = "609cb2d2-7c17-499a-a7a7-0ae0cb358871"
CLIENT_SECRET = "8qTGAhYD5sa6Xfpa1cydBMwB0T3KA4kBWNrN7oi2"
TOKEN_FILE_PATH = 'access_token.json'

def print_api_info(title, data):
    """Print API information in a formatted way"""
    print("\n" + "="*50)
    print(f"API {title}:")
    print("="*50)
    pprint(data)
    print("="*50 + "\n")

def is_token_expired(token_data):
    """Check if token is expired or will expire soon (within 5 minutes)"""
    if not token_data or 'expires_at' not in token_data:
        return True
    current_time = int(time.time())
    return current_time >= (token_data['expires_at'] - 300)  # 5 minutes buffer

def save_token_data(token_data):
    """Save token data with timestamps"""
    token_data['created_at'] = int(time.time())
    token_data['expires_at'] = token_data['created_at'] + token_data['expires_in']
    with open(TOKEN_FILE_PATH, 'w') as f:
        json.dump(token_data, f)
    logger.info("Token data saved successfully")

def load_token_data():
    """Load token data and check if it's expired"""
    if not os.path.exists(TOKEN_FILE_PATH):
        logger.warning("No token file found")
        return None
        
    try:
        with open(TOKEN_FILE_PATH, 'r') as f:
            token_data = json.load(f)
            
        if is_token_expired(token_data):
            logger.info("Token expired or will expire soon")
            return None
            
        logger.info("Valid token loaded from file")
        return token_data
    except Exception as e:
        logger.error(f"Error loading token data: {str(e)}")
        return None

def get_access_token():
    """Get access token from Prokerala API"""
    try:
        logger.info("Attempting to get new access token from Prokerala API")
        response = requests.post(
            "https://api.prokerala.com/token",
            data={
                "grant_type": "client_credentials",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            },
        )
        
        print_api_info("Token Request", {
            "url": "https://api.prokerala.com/token",
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "response": response.json() if response.status_code == 200 else response.text
        })
        
        if response.status_code == 200:
            token_data = response.json()
            save_token_data(token_data)
            logger.info("Successfully obtained and saved new access token")
            return token_data
        else:
            logger.error(f"Failed to get access token. Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error getting access token: {str(e)}", exc_info=True)
        return None

def get_auth_headers():
    """Get authorization headers with token refresh if needed"""
    # Try to load existing token
    token_data = load_token_data()
    
    if not token_data:
        # No valid token, get new one
        token_data = get_access_token()
        if not token_data:
            raise Exception("Failed to get access token")
            
    return {"Authorization": f"Bearer {token_data['access_token']}"}

def make_api_request(url, headers, params, method="get"):
    """Make API request with automatic token refresh"""
    try:
        # First attempt
        if method.lower() == "get":
            response = requests.get(url, headers=headers, params=params)
        else:
            response = requests.post(url, headers=headers, data=params)
        
        # If token expired (401), refresh and retry once
        if response.status_code == 401:
            logger.info("Token expired, attempting to refresh...")
            new_token_data = get_access_token()
            if new_token_data:
                new_headers = {"Authorization": f"Bearer {new_token_data['access_token']}"}
                if method.lower() == "get":
                    response = requests.get(url, headers=new_headers, params=params)
                else:
                    response = requests.post(url, headers=new_headers, data=params)
            else:
                logger.error("Failed to refresh token")
                
        return response
    except Exception as e:
        logger.error(f"API request error: {str(e)}")
        raise e

def format_datetime(dt_str: str) -> str:
    """Format datetime string to ISO format with timezone"""
    try:
        # Try parsing the input datetime
        dt = datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
        # Convert to ISO format with timezone
        return dt.strftime("%Y-%m-%dT%H:%M:%S+05:30")
    except ValueError as e:
        logger.error(f"Error parsing datetime: {str(e)}")
        raise ValueError("Invalid datetime format. Please use format: YYYY-MM-DD HH:MM AM/PM")


@mcp.tool()
def get_panchang(coordinates: str, datetime_str: str) -> str:
    """Get panchang details including tithi, nakshatra, yoga, karana, and other astrological details
    Args:
        coordinates: Latitude,Longitude (e.g., "8.8932,76.6141")
        datetime_str: Date and time in 24 hours format with timezone  in YYYY-MM-DDTHH:MM:SS+05:30
    """
    try:
        formatted_datetime = format_datetime(datetime_str)
        headers = get_auth_headers()
        params = {
            "ayanamsa": 1,
            "coordinates": coordinates,
            "datetime": formatted_datetime
        }
        
        print_api_info("Panchang Request", {
            "url": "https://api.prokerala.com/v2/astrology/panchang",
            "headers": headers,
            "params": params
        })
        
        response = requests.get(
            "https://api.prokerala.com/v2/astrology/panchang",
            headers=headers,
            params=params
        )
        
        print_api_info("Panchang Response", {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "response": response.json() if response.status_code == 200 else response.text
        })
        
        if response.status_code != 200:
            return f"API Error: {response.status_code} - {response.text}"
            
        return json.dumps(response.json(), indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error getting panchang: {str(e)}", exc_info=True)
        return f"Error: {str(e)}"

@mcp.tool()
def get_kundli(coordinates: str, datetime_str: str) -> str:
    """Get kundli details for given coordinates and datetime"""
    try:
        logger.info(f"Getting kundli for coordinates: {coordinates}, datetime: {datetime_str}")
        
        formatted_datetime = format_datetime(datetime_str)
        logger.debug(f"Formatted datetime: {formatted_datetime}")
        
        headers = get_auth_headers()
        params = {
            "ayanamsa": 1,
            "coordinates": coordinates,
            "datetime": formatted_datetime
        }
        
        print_api_info("Kundli Request", {
            "url": "https://api.prokerala.com/v2/astrology/kundli/advanced",
            "headers": headers,
            "params": params
        })
        
        response = make_api_request(
            "https://api.prokerala.com/v2/astrology/kundli/advanced",
            headers=headers,
            params=params
        )
        
        print_api_info("Kundli Response", {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "response": response.json() if response.status_code == 200 else response.text
        })
        
        if response.status_code != 200:
            return f"API Error: {response.status_code} - {response.text}"
            
        response.raise_for_status()
        
        result = response.json()
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return f"Error: {str(e)}"
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        logger.error(f"Request URL: {e.request.url if hasattr(e, 'request') else 'Unknown'}")
        logger.error(f"Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return f"Error: {str(e)}"

# Calendar and Panchang Tools
@mcp.tool()
def get_calendar(coordinates: str, datetime: str) -> str:
    """Get calendar details for given coordinates and datetime"""
    try:
        headers = get_auth_headers()
        params = {
            "ayanamsa": 1,
            "coordinates": coordinates,
            "datetime": datetime
        }
        response = make_api_request(
            "https://api.prokerala.com/v2/astrology/calendar",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        logger.error(f"Error getting calendar: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
def get_panchang(coordinates: str, datetime_str: str) -> str:
    """Get panchang details including tithi, nakshatra, yoga, karana, and other astrological details
    Args:
        coordinates: Latitude,Longitude (e.g., "8.8932,76.6141")
        datetime_str: Date and time in 24 hours format with timezone  in YYYY-MM-DDTHH:MM:SS+05:30
    """
    try:
        formatted_datetime = format_datetime(datetime_str)
        headers = get_auth_headers()
        params = {
            "ayanamsa": 1,
            "coordinates": coordinates,
            "datetime": formatted_datetime
        }
        
        print_api_info("Panchang Request", {
            "url": "https://api.prokerala.com/v2/astrology/panchang",
            "headers": headers,
            "params": params
        })
        
        response = requests.get(
            "https://api.prokerala.com/v2/astrology/panchang",
            headers=headers,
            params=params
        )
        
        print_api_info("Panchang Response", {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "response": response.json() if response.status_code == 200 else response.text
        })
        
        if response.status_code != 200:
            return f"API Error: {response.status_code} - {response.text}"
            
        return json.dumps(response.json(), indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error getting panchang: {str(e)}", exc_info=True)
        return f"Error: {str(e)}"

# Period Analysis Tools
@mcp.tool()
def get_auspicious_period(coordinates: str, datetime: str) -> str:
    """Get auspicious period details for given coordinates and datetime
    Args:
        coordinates: Latitude,Longitude (e.g., "23.1765,75.7885")
        datetime: Date and time in 24 hours format with timezone in YYYY-MM-DDTHH:MM:SS+05:30 (e.g., "2023-11-09T09:24:27+05:30")
    
    Example API call:
    {
        "ayanamsa": 1,
        "coordinates": "23.1765,75.7885",
        "datetime": "2023-11-09T09:24:27+05:30"
    }
    """
    try:
        headers = get_auth_headers()
        params = {
            "ayanamsa": 1,
            "coordinates": coordinates,
            "datetime": datetime
        }
        response = make_api_request(
            "https://api.prokerala.com/v2/astrology/auspicious-period",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        logger.error(f"Error getting auspicious period: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
def get_inauspicious_period(coordinates: str, datetime: str) -> str:
    """Get inauspicious period details for given coordinates and datetime
    Args:
        coordinates: Latitude,Longitude (e.g., "23.1765,75.7885")
        datetime: Date and time in 24 hours format with timezone in YYYY-MM-DDTHH:MM:SS+05:30 (e.g., "2023-11-09T09:24:27+05:30")
    
    Example API call:
    {
        "ayanamsa": 1,
        "coordinates": "23.1765,75.7885",
        "datetime": "2023-11-09T09:24:27+05:30"
    }
    """
    try:
        headers = get_auth_headers()
        params = {
            "ayanamsa": 1,
            "coordinates": coordinates,
            "datetime": datetime
        }
        response = make_api_request(
            "https://api.prokerala.com/v2/astrology/inauspicious-period",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        logger.error(f"Error getting inauspicious period: {str(e)}")
        return f"Error: {str(e)}"

# Horoscope and Birth Details
@mcp.tool()
def get_daily_horoscope(sign: str, datetime_str: str) -> str:
    """Get daily horoscope for a zodiac sign
    Args:
        sign: Zodiac sign (e.g., aries, taurus, etc.)
        datetime_str: Date and time in 24 format with timezone, eg:  YYYY-MM-DDTHH:MM:SS+05:30,
    """
    try:
        formatted_datetime = format_datetime(datetime_str)
        headers = get_auth_headers()
        params = {
            "datetime": formatted_datetime,
            "sign": sign.lower()
        }
        
        print_api_info("Daily Horoscope Request", {
            "url": "https://api.prokerala.com/v2/horoscope/daily",
            "headers": headers,
            "params": params
        })
        
        response = requests.get(
            "https://api.prokerala.com/v2/horoscope/daily",
            headers=headers,
            params=params
        )
        
        print_api_info("Daily Horoscope Response", {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "response": response.json() if response.status_code == 200 else response.text
        })
        
        if response.status_code != 200:
            return f"API Error: {response.status_code} - {response.text}"
            
        return json.dumps(response.json(), indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error getting daily horoscope: {str(e)}", exc_info=True)
        return f"Error: {str(e)}"

@mcp.tool()
def get_birth_details(coordinates: str, datetime: str) -> str:
    """Get birth details for given coordinates and datetime"""
    try:
        headers = get_auth_headers()
        params = {
            "ayanamsa": 1,
            "coordinates": coordinates,
            "datetime": datetime
        }
        response = make_api_request(
            "https://api.prokerala.com/v2/astrology/birth-details",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        logger.error(f"Error getting birth details: {str(e)}")
        return f"Error: {str(e)}"

# Dosha Analysis Tools
@mcp.tool()
def get_kaal_sarp_dosha(coordinates: str, datetime: str) -> str:
    """Get Kaal Sarp Dosha details for given coordinates and datetime
    Args:
        coordinates: Latitude,Longitude (e.g., "23.1765,75.7885")
        datetime: Date and time in 24 hours format with timezone in YYYY-MM-DDTHH:MM:SS+05:30 (e.g., "2023-11-09T09:24:27+05:30")
    
    Example:
    {
        "ayanamsa": 1,
        "coordinates": "23.1765,75.7885",
        "datetime": "2023-11-09T09:24:27+05:30"
    }
    """
    try:
        headers = get_auth_headers()
        params = {
            "ayanamsa": 1,
            "coordinates": coordinates,
            "datetime": datetime
        }
        response = make_api_request(
            "https://api.prokerala.com/v2/astrology/kaal-sarp-dosha",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        logger.error(f"Error getting Kaal Sarp Dosha: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
def get_manglik_dosha(coordinates: str, datetime: str) -> str:
    """Get Manglik Dosha details for given coordinates and datetime"""
    try:
        headers = get_auth_headers()
        params = {
            "ayanamsa": 1,
            "coordinates": coordinates,
            "datetime": datetime
        }
        response = make_api_request(
            "https://api.prokerala.com/v2/astrology/manglik-dosha",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        logger.error(f"Error getting Manglik Dosha: {str(e)}")
        return f"Error: {str(e)}"

# Chart and Position Tools
@mcp.tool()
def get_chart(coordinates: str, datetime: str, chart_type: str = "rasi", chart_style: str = "south-indian", format: str = "svg", language: str = "en") -> str:
    """Get chart details for given coordinates and datetime
    Args:
        coordinates: Latitude,Longitude (e.g., "8.8932,76.6141")
        datetime: Date and time in 24 hours format with timezone in YYYY-MM-DDTHH:MM:SS+05:30 (e.g., "1983-03-21T23:30:00+05:30")
        chart_type: Type of chart (e.g., "rasi")
        chart_style: Style of chart (e.g., "south-indian")
        format: Output format (e.g., "svg")
        language: Language code (e.g., "en" for English, "ml" for Malayalam)
    
    Example:
    {
        "ayanamsa": 1,
        "coordinates": "8.8932,76.6141",
        "datetime": "1983-03-21T23:30:00+05:30",
        "chart_type": "rasi",
        "chart_style": "south-indian",
        "format": "svg",
        "la": "en"
    }
    """
    try:
        headers = get_auth_headers()
        params = {
            "ayanamsa": 1,
            "coordinates": coordinates,
            "datetime": datetime,
            "chart_type": chart_type,
            "chart_style": chart_style,
            "format": format,
            "la": language
        }
        response = make_api_request(
            "https://api.prokerala.com/v2/astrology/chart",
            headers=headers,
            params=params
        )
        response.raise_for_status()

        # Check the content type of the response
        content_type = response.headers.get('Content-Type', '')

        if 'svg' in content_type:
            # Handle SVG content
            svg_file_path = 'output.svg'
            svg_data = response.text
            with open(svg_file_path, 'w') as file:
                file.write(svg_data)
            return f"SVG chart saved to {svg_file_path}"
        elif 'json' in content_type:
            # Handle JSON content
            return json.dumps(response.json(), indent=2)
        else:
            return f"Unsupported response format: {content_type}"
    except Exception as e:
        logger.error(f"Error getting chart: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
def get_planet_positions(coordinates: str, datetime: str, language: str = "en") -> str:
    """Get planet positions for given coordinates and datetime
    Args:
        coordinates: Latitude,Longitude (e.g., "8.8932,76.6141")
        datetime: Date and time in 24 hours format with timezone in YYYY-MM-DDTHH:MM:SS+05:30 (e.g., "1983-03-21T23:30:00+05:30")
        language: Language code (e.g., "en" for English, "ml" for Malayalam)
    
    Example:
    {
        "ayanamsa": 1,
        "coordinates": "8.8932,76.6141",
        "datetime": "1983-03-21T23:30:00+05:30",
        "la": "en"
    }
    """
    try:
        headers = get_auth_headers()
        params = {
            "ayanamsa": 1,
            "coordinates": coordinates,
            "datetime": datetime,
            "la": language
        }
        response = make_api_request(
            "https://api.prokerala.com/v2/astrology/planet-position",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        logger.error(f"Error getting planet positions: {str(e)}")
        return f"Error: {str(e)}"

# Matching Tools
@mcp.tool()
def get_kundli_matching(girl_coordinates: str, girl_dob: str, boy_coordinates: str, boy_dob: str) -> str:
    """Get kundli matching details for given coordinates and dates of birth
    Args:
        girl_coordinates: Girl's birth coordinates (Latitude,Longitude) (e.g., "23.1765,75.7885")
        girl_dob: Girl's date of birth in 24 hours format with timezone in YYYY-MM-DDTHH:MM:SS+05:30 (e.g., "2023-11-09T09:24:27+05:30")
        boy_coordinates: Boy's birth coordinates (Latitude,Longitude) (e.g., "23.1765,75.7885")
        boy_dob: Boy's date of birth in 24 hours format with timezone in YYYY-MM-DDTHH:MM:SS+05:30 (e.g., "2023-11-09T09:24:27+05:30")
    
    Example:
    {
        "ayanamsa": 1,
        "girl_coordinates": "23.1765,75.7885",
        "girl_dob": "2023-11-09T09:24:27+05:30",
        "boy_coordinates": "23.1765,75.7885",
        "boy_dob": "2023-11-09T09:24:27+05:30"
    }
    """
    try:
        headers = get_auth_headers()
        params = {
            "ayanamsa": 1,
            "girl_coordinates": girl_coordinates,
            "girl_dob": girl_dob,
            "boy_coordinates": boy_coordinates,
            "boy_dob": boy_dob
        }
        response = make_api_request(
            "https://api.prokerala.com/v2/astrology/kundli-matching/advanced",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        logger.error(f"Error getting kundli matching: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
def get_porutham(girl_coordinates: str, girl_dob: str, 
                boy_coordinates: str, boy_dob: str, 
                system: str = "kerala", language: str = "ml") -> str:
    """Get porutham (compatibility) details between two individuals
    Args:
        girl_coordinates: Girl's birth coordinates (Latitude,Longitude) (e.g., "23.1765,75.7885")
        girl_dob: Girl's date of birth in 24 hours format with timezone in YYYY-MM-DDTHH:MM:SS+05:30 (e.g., "2023-11-09T09:24:27+05:30")
        boy_coordinates: Boy's birth coordinates (Latitude,Longitude) (e.g., "23.1765,75.7885")
        boy_dob: Boy's date of birth in 24 hours format with timezone in YYYY-MM-DDTHH:MM:SS+05:30 (e.g., "2023-11-09T09:24:27+05:30")
        system: Matching system (e.g., "kerala")
        language: Language code (e.g., "ml" for Malayalam, "en" for English)
    
    Example:
    {
        "ayanamsa": 1,
        "girl_coordinates": "23.1765,75.7885",
        "girl_dob": "2023-11-09T09:24:27+05:30",
        "boy_coordinates": "23.1765,75.7885",
        "boy_dob": "2023-11-09T09:24:27+05:30",
        "system": "kerala",
        "lang": "ml"
    }
    """
    try:
        headers = get_auth_headers()
        params = {
            "ayanamsa": 1,
            "girl_coordinates": girl_coordinates,
            "girl_dob": girl_dob,
            "boy_coordinates": boy_coordinates,
            "boy_dob": boy_dob,
            "system": system,
            "lang": language
        }
        
        print_api_info("Porutham Request", {
            "url": "https://api.prokerala.com/v2/astrology/porutham/advanced",
            "headers": headers,
            "params": params
        })
        
        response = requests.get(
            "https://api.prokerala.com/v2/astrology/porutham/advanced",
            headers=headers,
            params=params
        )
        
        print_api_info("Porutham Response", {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "response": response.json() if response.status_code == 200 else response.text
        })
        
        if response.status_code != 200:
            return f"API Error: {response.status_code} - {response.text}"
            
        return json.dumps(response.json(), indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error getting porutham: {str(e)}", exc_info=True)
        return f"Error: {str(e)}"

@mcp.tool()
def get_papasamyam(girl_coordinates: str, girl_dob: str, 
                  boy_coordinates: str, boy_dob: str, 
                  system: str = "kerala", language: str = "ml") -> str:
    """Check for papasamyam (dosha compatibility) between two individuals
    Args:
        girl_coordinates: Girl's birth coordinates (Latitude,Longitude) (e.g., "23.1765,75.7885")
        girl_dob: Girl's date of birth in 24 hours format with timezone in YYYY-MM-DDTHH:MM:SS+05:30 (e.g., "2023-11-09T09:24:27+05:30")
        boy_coordinates: Boy's birth coordinates (Latitude,Longitude) (e.g., "23.1765,75.7885")
        boy_dob: Boy's date of birth in 24 hours format with timezone in YYYY-MM-DDTHH:MM:SS+05:30 (e.g., "2023-11-09T09:24:27+05:30")
        system: Matching system (e.g., "kerala")
        language: Language code (e.g., "ml" for Malayalam, "en" for English)
    
    Example:
    {
        "ayanamsa": 1,
        "girl_coordinates": "23.1765,75.7885",
        "girl_dob": "2023-11-09T09:24:27+05:30",
        "boy_coordinates": "23.1765,75.7885",
        "boy_dob": "2023-11-09T09:24:27+05:30",
        "system": "kerala",
        "lang": "ml"
    }
    """
    try:
        girl_formatted_dob = format_datetime(girl_dob)
        boy_formatted_dob = format_datetime(boy_dob)
        
        headers = get_auth_headers()
        params = {
            "ayanamsa": 1,
            "girl_coordinates": girl_coordinates,
            "girl_dob": girl_formatted_dob,
            "boy_coordinates": boy_coordinates,
            "boy_dob": boy_formatted_dob,
            "system": system,
            "lang": language
        }
        
        print_api_info("Papasamyam Request", {
            "url": "https://api.prokerala.com/v2/astrology/papasamyam-check",
            "headers": headers,
            "params": params
        })
        
        response = requests.get(
            "https://api.prokerala.com/v2/astrology/papasamyam-check",
            headers=headers,
            params=params
        )
        
        print_api_info("Papasamyam Response", {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "response": response.json() if response.status_code == 200 else response.text
        })
        
        if response.status_code != 200:
            return f"API Error: {response.status_code} - {response.text}"
            
        return json.dumps(response.json(), indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error getting papasamyam: {str(e)}", exc_info=True)
        return f"Error: {str(e)}"

@mcp.tool()
def get_mangal_dosha(coordinates: str, datetime: str, language: str = "ml") -> str:
    """Get Mangal Dosha details for given coordinates and datetime
    Args:
        coordinates: Latitude,Longitude (e.g., "23.1765,75.7885")
        datetime: Date and time in 24 hours format with timezone in YYYY-MM-DDTHH:MM:SS+05:30 (e.g., "2023-11-09T09:24:27+05:30")
        language: Language code (e.g., "ml" for Malayalam, "en" for English)
    
    Example:
    {
        "ayanamsa": 1,
        "coordinates": "23.1765,75.7885",
        "datetime": "2023-11-09T09:24:27+05:30",
        "la": "ml"
    }
    """
    try:
        headers = get_auth_headers()
        params = {
            "ayanamsa": 1,
            "coordinates": coordinates,
            "datetime": datetime,
            "la": language
        }
        response = make_api_request(
            "https://api.prokerala.com/v2/astrology/mangal-dosha",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        logger.error(f"Error getting Mangal Dosha: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="sse")

# run using  fastmcp run coremcp.py:mcp --transport sse 