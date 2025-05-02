# Prokerala Astrology MCP

MCP for Vedic astrology API  powered by Prokerala API, providing astrological services like horoscopes, panchang, and compatibility analysis through both command-line and web interfaces.

## Features

- Vedic astrology consultations
- Daily horoscope readings
- Panchang details
- Kundli matching and compatibility analysis
- Manglik Dosha analysis
- Multiple interfaces (CLI and Web UI)
- Support for multiple Indian languages

## Components

1. **Core MCP Server** (`coremcp.py`)
   - Main server implementation
   - Handles Prokerala API integration
   - Provides astrological tools and calculations

2. **Test Client** (`testclient.py`)
   - Command-line interface for testing
   - Interactive chat-based interface
   - Useful for development and testing

3. **Web UI** (`ui.py`)
   - Chainlit-based web interface
   - User-friendly chat interface
   - Real-time responses

## Prerequisites

- Python 3.12 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Installation

1. Clone the repository:
   ```bash
   git clone git@github.com:sajithamma/prokerala-mcp-server.git
   cd prokerala-mcp-server
   ```

2. Create and activate a virtual environment:
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your Prokerala API credentials:
   ```
   OPENAI_API_KEY=your_openai_api_key
   CLIENT_ID=your_client_id
   CLIENT_SECRET=your_client_secret
   TOKEN_FILE_PATH=access_token.json
   ```

## Running the Application

### 1. Start the MCP Server

First, start the main server:
```bash
fastmcp run coremcp.py:mcp --transport sse
```

The server will start on `http://localhost:8000`

### 2. Run the Test Client

In a new terminal:
```bash
python testclient.py
```

The test client provides an interactive command-line interface where you can:
- Get daily horoscopes
- Check compatibility
- Get panchang details
- And more...

Example usage:
```
Enter your message: get me today's horoscope
Sure, I can help with that. Could you please tell me your zodiac sign?
Enter your message: aries
[Horoscope details will be displayed]
```

### 3. Run the Web UI (Chainlit)

In a new terminal:
```bash
chainlit run ui.py
```

The web interface will be available at `http://localhost:8000` and provides:
- A modern chat interface
- Real-time responses
- Easy-to-use format for all astrological services

## Available Astrological Services

1. **Daily Horoscope**
   - Get personalized daily predictions
   - Available for all zodiac signs

2. **Panchang**
   - Daily astrological details
   - Tithi, nakshatra, yoga information

3. **Kundli Matching**
   - Compatibility analysis
   - Porutham checking
   - Manglik Dosha analysis

4. **Birth Chart Analysis**
   - Detailed birth chart
   - Planetary positions
   - Dosha analysis

## Environment Variables

The application uses the following environment variables:
- `CLIENT_ID`: Your Prokerala API client ID
- `CLIENT_SECRET`: Your Prokerala API client secret
- `TOKEN_FILE_PATH`: Path to store the access token

## Troubleshooting

1. **Server Connection Issues**
   - Ensure the MCP server is running before starting the client or UI
   - Check if port 8000 is available

2. **API Authentication Errors**
   - Verify your API credentials in the `.env` file
   - Check if the token file has proper permissions

3. **Date Format Issues**
   - Use the correct datetime format: YYYY-MM-DD HH:MM AM/PM
   - For API calls, the system will automatically convert to ISO format

