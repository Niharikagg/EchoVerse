from fastapi import FastAPI, Request, Body
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Backend is running!"}

# Update the POST endpoint with Body
@app.post("/recommend")
async def recommend(mood: str = Body(...)):
    # Logic based on mood
    if mood == "happy":
        return {"songs": ["Happy - Pharrell", "Can’t Stop the Feeling - JT"]}
    elif mood == "sad":
        return {"songs": ["Someone Like You - Adele", "Fix You - Coldplay"]}
    else:
        return {"songs": ["Blinding Lights - The Weeknd"]}
