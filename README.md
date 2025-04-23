# Mood-Based Music Recommender

This project uses AI to analyze user mood and recommend songs based on the analysis. The system combines sentiment analysis with music recommendation algorithms to provide personalized song suggestions.

## Features

- User mood analysis through text input
- AI-powered sentiment analysis
- Integration with Spotify API for music recommendations
- Personalized song suggestions based on mood
- Web interface for easy interaction

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your Spotify API credentials:
```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
```

3. Run the application:
```bash
python app.py
```

## Project Structure

- `Backend/`: Contains the AI models and recommendation logic
- `Frontend/`: Contains the web interface
- `app.py`: Main application file
- `requirements.txt`: Project dependencies

## How It Works

1. User inputs their current mood or feelings
2. The system analyzes the text using sentiment analysis
3. Based on the mood analysis, the system recommends songs from Spotify
4. Recommendations are displayed to the user with relevant metadata 