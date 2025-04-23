from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
import json
from groq import Groq

# Load environment variables
load_dotenv()

# Debug: Print Spotify credentials (remove this in production)
print("Spotify Client ID:", os.getenv('SPOTIFY_CLIENT_ID'))
print("Spotify Client Secret:", os.getenv('SPOTIFY_CLIENT_SECRET'))
print("Spotify Redirect URI:", os.getenv('SPOTIFY_REDIRECT_URI'))

app = Flask(__name__, 
    template_folder='Frontend/templates',
    static_folder='Frontend/static'
)
app.secret_key = os.urandom(24)  # Required for session management

# Initialize Groq client
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

# Spotify OAuth configuration
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = 'http://127.0.0.1:5000/callback'
SCOPE = 'user-read-private user-read-email playlist-modify-public playlist-modify-private user-top-read user-read-recently-played'

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        show_dialog=True,
        cache_path='.spotify_caches'
    )

@app.route('/')
def home():
    if 'token_info' not in session:
        return render_template('index.html', logged_in=False)
    return render_template('index.html', logged_in=True)

@app.route('/login')
def login():
    try:
        sp_oauth = create_spotify_oauth()
        auth_url = sp_oauth.get_authorize_url()
        print("Auth URL:", auth_url)  # Debug print
        return redirect(auth_url)
    except Exception as e:
        print("Login error:", str(e))  # Debug print
        return str(e), 500

@app.route('/callback')
def callback():
    try:
        sp_oauth = create_spotify_oauth()
        session.clear()
        code = request.args.get('code')
        print("Callback code:", code)  # Debug print
        token_info = sp_oauth.get_access_token(code)
        session['token_info'] = token_info
        return redirect(url_for('home'))
    except Exception as e:
        print("Callback error:", str(e))  # Debug print
        return str(e), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

def get_token():
    token_info = session.get('token_info', None)
    if not token_info:
        print("No token info in session")
        return None
        
    sp_oauth = create_spotify_oauth()
    if sp_oauth.is_token_expired(token_info):
        print("Token expired, refreshing...")
        try:
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            session['token_info'] = token_info
        except Exception as e:
            print(f"Error refreshing token: {str(e)}")
            return None
            
    return token_info['access_token']

def analyze_mood_with_groq(text):
    try:
        print("\n=== Starting Mood Analysis ===")
        print(f"Input text: {text}")
        
        # Simple keyword-based mood detection
        mood_keywords = {
            'happy': ['happy', 'joy', 'excited', 'good', 'great', 'wonderful', 'amazing', 'delighted', 'cheerful'],
            'sad': ['sad', 'down', 'depressed', 'lonely', 'unhappy', 'miserable', 'heartbroken', 'gloomy', 'blue'],
            'energetic': ['energetic', 'pumped', 'excited', 'active', 'lively', 'energized', 'cool', 'dynamic', 'vibrant'],
            'calm': ['calm', 'peaceful', 'relaxed', 'serene', 'quiet', 'tranquil', 'chill', 'ease', 'easy', 'at ease', 'comfortable'],
            'angry': ['angry', 'frustrated', 'annoyed', 'mad', 'irritated', 'upset', 'furious', 'enraged'],
            'romantic': ['romantic', 'love', 'affectionate', 'tender', 'sweet', 'loving', 'passionate', 'intimate'],
            'fear': ['fear', 'afraid', 'scared', 'anxious', 'worried', 'nervous', 'terrified', 'panic', 'frightened']
        }
        
        # Convert text to lowercase for case-insensitive matching
        text_lower = text.lower()
        print(f"Processed text (lowercase): {text_lower}")
        
        # Count matches for each mood
        mood_scores = {}
        for mood, keywords in mood_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                print(f"Found {score} matches for mood '{mood}'")
            mood_scores[mood] = score
        
        print(f"Mood scores: {mood_scores}")
        
        # Get the mood with the highest score
        if not any(mood_scores.values()):
            print("No mood keywords found, defaulting to 'calm'")
            return {
                'mood': 'calm',
                'explanation': 'I notice you might be feeling calm and peaceful today.'
            }
        
        best_mood = max(mood_scores.items(), key=lambda x: x[1])[0]
        print(f"Detected mood: {best_mood}")
        
        # Natural language explanations for each mood
        mood_explanations = {
            'happy': 'I can tell you\'re feeling happy and positive! Your energy is uplifting.',
            'sad': 'I understand you\'re feeling down right now. It\'s okay to feel this way.',
            'energetic': 'You\'re radiating energy and enthusiasm! Your vibe is contagious.',
            'calm': 'You seem to be in a peaceful and relaxed state of mind.',
            'angry': 'I sense you\'re feeling frustrated or upset. It\'s okay to feel this way.',
            'romantic': 'You\'re in a loving and affectionate mood. How sweet!',
            'fear': 'I notice you might be feeling anxious or worried. It\'s okay to feel this way.'
        }
        
        result = {
            'mood': best_mood,
            'explanation': mood_explanations[best_mood]
        }
        print(f"Final result: {result}")
        return result
    
    except Exception as e:
        print(f"Error in mood analysis: {str(e)}")
        return {
            'mood': 'calm',
            'explanation': 'I notice you might be feeling calm and peaceful today.'
        }

@app.route('/analyze', methods=['POST'])
def analyze_mood():
    try:
        print("\n=== Starting Mood Analysis Request ===")
        data = request.get_json()
        print(f"Received data: {data}")
        
        text = data.get('text', '')
        if not text:
            print("No text provided in request")
            return jsonify({'error': 'No text provided'}), 400
            
        print(f"Text to analyze: {text}")
        
        # Analyze mood using Groq
        result = analyze_mood_with_groq(text)
        print(f"Mood analysis result: {result}")
        
        # Get recommendations from Spotify
        token = get_token()
        if not token:
            print("No valid token found")
            return jsonify({'error': 'Not authenticated'}), 401
            
        print("Creating Spotify client...")
        sp = spotipy.Spotify(auth=token)
        
        # Verify authentication by getting user info
        try:
            user_info = sp.current_user()
            print(f"Authenticated as user: {user_info['id']}")
        except Exception as e:
            print(f"Error verifying authentication: {str(e)}")
            return jsonify({'error': 'Authentication failed'}), 401
        
        print("Getting recommendations...")
        recommendations = get_spotify_recommendations(sp, result['mood'])
        print(f"Recommendations received: {recommendations}")
        
        # Always return mood and explanation, even if no recommendations
        response = {
            'mood': result['mood'],
            'explanation': result['explanation'],
            'recommendations': recommendations if recommendations else []
        }
        print(f"Sending response: {response}")
        return jsonify(response)
    
    except Exception as e:
        print(f"Error in analyze_mood: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/create_playlist', methods=['POST'])
def create_playlist():
    try:
        print("Attempting to create playlist...")  # Debug log
        token = get_token()
        if not token:
            print("No token found - user not authenticated")  # Debug log
            return jsonify({'error': 'Not authenticated'}), 401
            
        sp = spotipy.Spotify(auth=token)
        data = request.get_json()
        track_uris = data.get('track_uris', [])
        mood = data.get('mood', '')
        
        print(f"Creating playlist for mood: {mood}")  # Debug log
        print(f"Number of tracks to add: {len(track_uris)}")  # Debug log
        
        # Get user's Spotify ID
        user_info = sp.current_user()
        user_id = user_info['id']
        print(f"User ID: {user_id}")  # Debug log
        
        # Create playlist
        playlist = sp.user_playlist_create(
            user_id,
            f'Mood Playlist: {mood.capitalize()}',
            public=True,
            description=f'Playlist created based on your {mood} mood'
        )
        print(f"Playlist created with ID: {playlist['id']}")  # Debug log
        
        # Add tracks to playlist
        sp.playlist_add_items(playlist['id'], track_uris)
        print("Tracks added to playlist successfully")  # Debug log
        
        return jsonify({
            'success': True,
            'playlist_url': playlist['external_urls']['spotify']
        })
        
    except Exception as e:
        print(f"Error creating playlist: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500

def get_spotify_recommendations(sp, mood):
    try:
        print("\n=== Starting Spotify Recommendations Process ===")
        print(f"Analyzing mood: {mood}")
        
        # Get user's top artists to personalize recommendations
        try:
            print("\n1. Fetching user's top artists...")
            top_artists = sp.current_user_top_artists(limit=5, time_range='medium_term')
            print(f"Top artists response: {top_artists}")
            
            if not top_artists or not top_artists.get('items'):
                print("No top artists found, using default seed tracks")
                seed_artists = ['4NHQUGzhtTLFvgF5SZesLK']  # Default artist ID
            else:
                seed_artists = [artist['id'] for artist in top_artists['items']]
            print(f"Using seed artists: {seed_artists}")
            
            # Get a popular track from the first artist
            if seed_artists:
                artist_tracks = sp.artist_top_tracks(seed_artists[0])
                if artist_tracks and artist_tracks.get('tracks'):
                    seed_tracks = [artist_tracks['tracks'][0]['id']]
                    print(f"Using seed track: {seed_tracks[0]}")
                else:
                    seed_tracks = ['4NHQUGzhtTLFvgF5SZesLK']  # Default track ID
            else:
                seed_tracks = ['4NHQUGzhtTLFvgF5SZesLK']  # Default track ID
                
            # Get genres from the first artist
            if top_artists and top_artists.get('items'):
                genres = top_artists['items'][0].get('genres', [])
                if genres:
                    seed_genres = [genres[0]]
                    print(f"Using seed genre: {seed_genres[0]}")
                else:
                    seed_genres = ['pop']  # Default genre
            else:
                seed_genres = ['pop']  # Default genre
                
        except Exception as e:
            print(f"Error getting top artists: {str(e)}")
            seed_artists = ['4NHQUGzhtTLFvgF5SZesLK']  # Default artist ID
            seed_tracks = ['4NHQUGzhtTLFvgF5SZesLK']  # Default track ID
            seed_genres = ['pop']  # Default genre
        
        # Mood to Spotify audio features mapping
        print("\n2. Setting audio features based on mood")
        mood_features = {
            'happy': {'target_valence': 0.8, 'target_energy': 0.7, 'target_danceability': 0.7},
            'sad': {'target_valence': 0.2, 'target_energy': 0.3, 'target_danceability': 0.3},
            'energetic': {'target_valence': 0.7, 'target_energy': 0.8, 'target_danceability': 0.8},
            'calm': {'target_valence': 0.5, 'target_energy': 0.3, 'target_danceability': 0.3},
            'angry': {'target_valence': 0.3, 'target_energy': 0.8, 'target_danceability': 0.6},
            'romantic': {'target_valence': 0.7, 'target_energy': 0.4, 'target_danceability': 0.5},
            'fear': {'target_valence': 0.2, 'target_energy': 0.6, 'target_danceability': 0.4}
        }
        
        features = mood_features.get(mood, {'target_valence': 0.5, 'target_energy': 0.5, 'target_danceability': 0.5})
        print(f"Using audio features: {features}")
        
        try:
            print("\n3. Requesting recommendations from Spotify...")
            recommendations = sp.recommendations(
                seed_artists=seed_artists[:5],
                seed_tracks=seed_tracks,
                seed_genres=seed_genres,
                limit=10,
                target_valence=features['target_valence'],
                target_energy=features['target_energy'],
                target_danceability=features['target_danceability'],
                min_popularity=30,
                market='US'
            )
            print(f"Spotify API response received")
            
            if not recommendations or not recommendations.get('tracks'):
                print("No tracks in Spotify response")
                return []
            
            print(f"\n4. Processing {len(recommendations['tracks'])} tracks")
            tracks = []
            for track in recommendations['tracks']:
                if not track.get('uri'):
                    print(f"Warning: Track {track.get('name', 'Unknown')} has no URI")
                    continue
                
                track_data = {
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'album': track['album']['name'],
                    'preview_url': track['preview_url'],
                    'image_url': track['album']['images'][0]['url'] if track['album']['images'] else None,
                    'uri': track['uri']
                }
                print(f"Processed track: {track_data['name']} by {track_data['artist']}")
                tracks.append(track_data)
            
            print(f"\n5. Successfully processed {len(tracks)} tracks")
            return tracks
            
        except Exception as e:
            print(f"Error getting recommendations from Spotify: {str(e)}")
            return []
    
    except Exception as e:
        print(f"Error in get_spotify_recommendations: {str(e)}")
        return []

if __name__ == '__main__':
    app.run(debug=True) 