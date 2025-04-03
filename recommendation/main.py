from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Table, MetaData, DateTime, func, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import numpy as np
from datetime import datetime, timedelta
import os
import time
import logging
import httpx
import random
from sqlalchemy.exc import OperationalError
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pickle
import json
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:1234@db:5432/event_platform")

# Create engine and session
engine = None
SessionLocal = None
Base = declarative_base()

# Path for storing ML models
MODEL_DIR = "/app/models"
os.makedirs(MODEL_DIR, exist_ok=True)
USER_CLUSTER_MODEL_PATH = os.path.join(MODEL_DIR, "user_clusters.pkl")
EVENT_CATEGORY_MATRIX_PATH = os.path.join(MODEL_DIR, "event_category_matrix.json")

# Models
class EventClick(Base):
    __tablename__ = "event_clicks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    event_id = Column(Integer, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
class EventView(Base):
    __tablename__ = "event_views"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    event_id = Column(Integer, index=True)
    view_duration = Column(Float, default=0.0)  # Time spent viewing in seconds
    timestamp = Column(DateTime, default=datetime.utcnow)

# Pydantic models
class ClickCreate(BaseModel):
    user_id: Optional[int] = None  # Allow anonymous clicks
    event_id: int
    
class ViewCreate(BaseModel):
    user_id: Optional[int] = None  # Allow anonymous views
    event_id: int
    view_duration: float
    
class RecommendationRequest(BaseModel):
    user_id: Optional[int] = None
    limit: int = 5

class EventResponse(BaseModel):
    id: int
    name: str
    image: Optional[str] = None
    date: str
    location: str
    price: str
    category: str
    
    class Config:
        orm_mode = True

# Connect to DB with retries
def connect_to_db_with_retries(max_retries=30, retry_interval=2):
    global engine, SessionLocal, Base
    
    retries = max_retries
    while retries > 0:
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as conn:
                logger.info("✅ Connected to the database")
                SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                
                # Create tables if they don't exist
                Base.metadata.create_all(bind=engine)
                logger.info("✅ Tables created or verified")
                return True
        except OperationalError as e:
            logger.warning(f"⏳ Database connection failed ({e}). Retrying in {retry_interval} seconds... ({retries} retries left)")
            time.sleep(retry_interval)
            retries -= 1
    
    logger.error("❌ Failed to connect to the database after multiple attempts")
    return False

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(title="Event Recommendation Service")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "recommendation"}

# ML status endpoint
@app.get("/ml/status")
def ml_status(db: Session = Depends(get_db)):
    # Check if model exists
    model_exists = os.path.exists(USER_CLUSTER_MODEL_PATH)
    prefs_exists = os.path.exists(EVENT_CATEGORY_MATRIX_PATH)
    
    # Get model stats if exists
    model_stats = {}
    cluster_stats = {}
    
    if model_exists:
        try:
            with open(USER_CLUSTER_MODEL_PATH, 'rb') as f:
                model_data = pickle.load(f)
                
            user_clusters = model_data.get('user_clusters', {})
            
            # Count users per cluster
            cluster_counts = defaultdict(int)
            for _, cluster in user_clusters.items():
                cluster_counts[cluster] += 1
                
            # Get total users
            total_users = len(user_clusters)
            
            model_stats = {
                "total_users_in_model": total_users,
                "clusters": len(cluster_counts),
                "users_per_cluster": dict(cluster_counts)
            }
        except Exception as e:
            logger.error(f"Error getting model stats: {e}")
            model_stats = {"error": str(e)}
    
    if prefs_exists:
        try:
            with open(EVENT_CATEGORY_MATRIX_PATH, 'r') as f:
                cluster_preferences = json.load(f)
            
            # Convert string keys to integers and get top categories per cluster
            for cluster_id, preferences in cluster_preferences.items():
                top_categories = sorted(preferences.items(), key=lambda x: x[1], reverse=True)[:3]
                cluster_stats[cluster_id] = {
                    "top_categories": [cat for cat, _ in top_categories],
                    "category_weights": {cat: count for cat, count in top_categories}
                }
        except Exception as e:
            logger.error(f"Error getting cluster preferences: {e}")
            cluster_stats = {"error": str(e)}
    
    # Count clicks in last 30 days
    try:
        recent_time = datetime.utcnow() - timedelta(days=30)
        total_clicks = db.query(EventClick).filter(
            EventClick.timestamp > recent_time
        ).count()
        
        # Count unique users with clicks
        unique_users = db.query(EventClick.user_id).filter(
            EventClick.timestamp > recent_time,
            EventClick.user_id != None
        ).distinct().count()
        
        click_stats = {
            "total_clicks_30_days": total_clicks,
            "unique_users_30_days": unique_users
        }
    except Exception as e:
        logger.error(f"Error getting click stats: {e}")
        click_stats = {"error": str(e)}
    
    return {
        "ml_model_exists": model_exists,
        "cluster_preferences_exists": prefs_exists,
        "model_stats": model_stats,
        "cluster_stats": cluster_stats,
        "interaction_stats": click_stats,
        "last_updated": os.path.getmtime(USER_CLUSTER_MODEL_PATH) if model_exists else None
    }

# Track event click
@app.post("/click")
def record_click(click: ClickCreate, db: Session = Depends(get_db)):
    db_click = EventClick(
        user_id=click.user_id,
        event_id=click.event_id,
    )
    db.add(db_click)
    db.commit()
    db.refresh(db_click)
    return {"status": "success", "message": "Click recorded"}

# Track event view
@app.post("/view")
def record_view(view: ViewCreate, db: Session = Depends(get_db)):
    db_view = EventView(
        user_id=view.user_id,
        event_id=view.event_id,
        view_duration=view.view_duration
    )
    db.add(db_view)
    db.commit()
    db.refresh(db_view)
    return {"status": "success", "message": "View recorded"}

# Fetch events from main backend
async def fetch_events_from_backend():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://backend:8000/events/")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch events: {response.status_code}")
                return []
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        return []

# Get static example events as fallback
def get_fallback_events():
    return [
        { 
            "id": 1, 
            "name": "Concert in Almaty", 
            "date": "17.03.2025", 
            "location": "Republic Palace", 
            "price": "30", 
            "category": "concerts",
            "image": "/images/event1.jpg" 
        },
        { 
            "id": 2, 
            "name": "Movie Night", 
            "date": "18.03.2025", 
            "location": "Esentai Mall", 
            "price": "Free", 
            "category": "movies",
            "image": "/images/event2.jpg" 
        },
        { 
            "id": 3, 
            "name": "Football Match", 
            "date": "19.03.2025", 
            "location": "Central Stadium", 
            "price": "15", 
            "category": "sport",
            "image": "/images/event3.jpg" 
        },
        { 
            "id": 4, 
            "name": "Comedy Show", 
            "date": "20.03.2025", 
            "location": "Theatre", 
            "price": "25", 
            "category": "entertainment",
            "image": "/images/event4.jpeg" 
        },
        { 
            "id": 5, 
            "name": "Art Exhibition", 
            "date": "22.03.2025", 
            "location": "Kasteyev Museum", 
            "price": "10", 
            "category": "other",
            "image": "/images/event5.jpeg" 
        }
    ]

# ML: Create user-event interaction matrix
def create_user_event_matrix(db: Session):
    try:
        # Get all clicks from the last 30 days
        recent_time = datetime.utcnow() - timedelta(days=30)
        clicks = db.query(EventClick).filter(
            EventClick.timestamp > recent_time,
            EventClick.user_id != None  # Exclude anonymous clicks
        ).all()
        
        # Get all users and events
        user_ids = set(click.user_id for click in clicks)
        event_ids = set(click.event_id for click in clicks)
        
        if not user_ids or not event_ids:
            logger.warning("Not enough data to create user-event matrix")
            return None, None, None
        
        # Create a matrix of user-event interactions
        user_event_matrix = defaultdict(lambda: defaultdict(int))
        
        # Fill matrix with click counts
        for click in clicks:
            user_event_matrix[click.user_id][click.event_id] += 1
        
        # Convert to format suitable for scikit-learn
        user_features = []
        matrix_user_ids = []
        
        for user_id, event_interactions in user_event_matrix.items():
            # Create a feature vector for each user (event interaction counts)
            feature_vector = [event_interactions.get(event_id, 0) for event_id in sorted(event_ids)]
            user_features.append(feature_vector)
            matrix_user_ids.append(user_id)
        
        return np.array(user_features), matrix_user_ids, sorted(event_ids)
    except Exception as e:
        logger.error(f"Error creating user-event matrix: {e}")
        return None, None, None

# ML: Train K-Means clustering model
def train_user_clusters(db: Session):
    logger.info("Training user clusters model with K-Means...")
    
    # Create user-event interaction matrix
    user_features, user_ids, event_ids = create_user_event_matrix(db)
    
    if user_features is None or len(user_features) < 5:
        logger.warning("Not enough user data to train cluster model")
        return None
    
    try:
        # Normalize the features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(user_features)
        
        # Determine optimal number of clusters (simplified - using min(5, n_users/2))
        n_clusters = min(5, max(2, len(user_features) // 2))
        
        # Train K-Means
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(scaled_features)
        
        # Create a mapping from user_id to cluster
        user_clusters = {user_id: int(label) for user_id, label in zip(user_ids, cluster_labels)}
        
        # Create a mapping of clusters to most clicked event categories
        all_events = get_fallback_events() # Fallback if backend fails
        
        # Try to get events from backend
        backend_events = asyncio.run(fetch_events_from_backend())
        if backend_events:
            all_events = backend_events
        
        # Create a mapping of event_id to category
        event_categories = {}
        for event in all_events:
            event_categories[event['id']] = event['category']
        
        # For each cluster, find the most common event categories
        cluster_preferences = defaultdict(lambda: defaultdict(int))
        
        for i, user_id in enumerate(user_ids):
            cluster = int(cluster_labels[i])
            for event_id, count in user_event_matrix[user_id].items():
                if event_id in event_categories:
                    category = event_categories[event_id]
                    cluster_preferences[cluster][category] += count
        
        # Save model and cluster preferences
        model_data = {
            'kmeans': kmeans,
            'scaler': scaler,
            'user_clusters': user_clusters
        }
        
        with open(USER_CLUSTER_MODEL_PATH, 'wb') as f:
            pickle.dump(model_data, f)
        
        # Save cluster category preferences
        with open(EVENT_CATEGORY_MATRIX_PATH, 'w') as f:
            json.dump(dict(cluster_preferences), f)
        
        logger.info(f"✅ K-Means model trained with {n_clusters} clusters")
        return user_clusters
    except Exception as e:
        logger.error(f"Error training K-Means model: {e}")
        return None

# ML: Get user's cluster
def get_user_cluster(user_id: int):
    if not os.path.exists(USER_CLUSTER_MODEL_PATH):
        return None
    
    try:
        with open(USER_CLUSTER_MODEL_PATH, 'rb') as f:
            model_data = pickle.load(f)
        
        user_clusters = model_data.get('user_clusters', {})
        return user_clusters.get(user_id)
    except Exception as e:
        logger.error(f"Error getting user cluster: {e}")
        return None

# ML: Get category preferences for a cluster
def get_cluster_preferences(cluster_id: int):
    if not os.path.exists(EVENT_CATEGORY_MATRIX_PATH):
        return None
    
    try:
        with open(EVENT_CATEGORY_MATRIX_PATH, 'r') as f:
            cluster_preferences = json.load(f)
        
        # Convert string keys to integers
        cluster_preferences = {int(k): v for k, v in cluster_preferences.items()}
        
        # Get preferences for this cluster
        preferences = cluster_preferences.get(cluster_id, {})
        
        # Sort by count
        sorted_preferences = sorted(preferences.items(), key=lambda x: x[1], reverse=True)
        return [category for category, _ in sorted_preferences]
    except Exception as e:
        logger.error(f"Error getting cluster preferences: {e}")
        return None

# Schedule periodic training of the model
@app.on_event("startup")
async def startup_event():
    success = connect_to_db_with_retries()
    if not success:
        logger.error("Failed to connect to database. Exiting...")
        exit(1)
    
    # Train model on startup if enough data
    db = SessionLocal()
    try:
        train_user_clusters(db)
    finally:
        db.close()

# ML endpoint to manually trigger model training
@app.post("/train")
def train_model(db: Session = Depends(get_db)):
    user_clusters = train_user_clusters(db)
    if user_clusters:
        return {"status": "success", "message": f"Model trained with {len(user_clusters)} users"}
    else:
        return {"status": "error", "message": "Failed to train model or not enough data"}

# Get event recommendations using the ML model
@app.get("/recommendations", response_model=List[EventResponse])
async def get_recommendations(
    user_id: Optional[int] = Query(None),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    # Fetch all events from backend
    all_events = await fetch_events_from_backend()
    
    # If we couldn't fetch events from backend, use fallback static events
    if not all_events:
        logger.warning("No events from backend, using fallback events")
        all_events = get_fallback_events()
    
    # If we still have no events, return empty list
    if not all_events:
        logger.error("No events available from any source")
        return []
    
    # For logged-in users - try to provide personalized recommendations with ML
    if user_id:
        logger.info(f"Generating ML-based recommendations for user {user_id}")
        
        # Try to get user's cluster
        user_cluster = get_user_cluster(user_id)
        
        # If user has a cluster, use it for recommendations
        if user_cluster is not None:
            logger.info(f"User {user_id} belongs to cluster {user_cluster}")
            
            # Get preferred categories for this cluster
            preferred_categories = get_cluster_preferences(user_cluster)
            
            if preferred_categories:
                logger.info(f"Cluster {user_cluster} prefers categories: {preferred_categories}")
                
                # Get user's recent clicks to avoid recommending the same events
                recent_time = datetime.utcnow() - timedelta(days=7)
                user_clicks = db.query(EventClick).filter(
                    EventClick.user_id == user_id,
                    EventClick.timestamp > recent_time
                ).all()
                
                already_seen = set(click.event_id for click in user_clicks)
                recommended_events = []
                
                # Recommend events from preferred categories
                for category in preferred_categories:
                    if len(recommended_events) >= limit:
                        break
                    
                    category_events = [event for event in all_events 
                                      if event['category'] == category and event['id'] not in already_seen]
                    
                    remaining = limit - len(recommended_events)
                    recommended_events.extend(category_events[:remaining])
                
                # If we have recommendations, return them
                if recommended_events:
                    logger.info(f"Returning {len(recommended_events)} ML-based recommendations")
                    return recommended_events[:limit]
        
        # If we don't have ML recommendations, fall back to simpler approach
        logger.info("Falling back to non-ML approach for user")
        
        # Get user's recent clicks (last 7 days)
        recent_time = datetime.utcnow() - timedelta(days=7)
        user_clicks = db.query(EventClick).filter(
            EventClick.user_id == user_id,
            EventClick.timestamp > recent_time
        ).all()
        
        # If user has clicks history
        if user_clicks and len(user_clicks) > 0:
            logger.info(f"User {user_id} has {len(user_clicks)} recent clicks")
            # Get event_ids the user clicked on
            clicked_event_ids = [click.event_id for click in user_clicks]
            
            # Find the most clicked categories (simple collaborative filtering)
            event_categories = {}
            for event in all_events:
                event_categories[event['id']] = event['category']
            
            category_counts = {}
            for event_id in clicked_event_ids:
                if event_id in event_categories:
                    category = event_categories[event_id]
                    category_counts[category] = category_counts.get(category, 0) + 1
            
            # Sort categories by click count
            sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
            logger.info(f"Preferred categories: {sorted_categories}")
            
            # Get recommended events (those in preferred categories not already clicked)
            recommended_events = []
            already_seen = set(clicked_event_ids)
            
            # Fill with events from user's favorite categories
            for category, _ in sorted_categories:
                if len(recommended_events) >= limit:
                    break
                
                category_events = [event for event in all_events 
                                  if event['category'] == category and event['id'] not in already_seen]
                
                remaining = limit - len(recommended_events)
                recommended_events.extend(category_events[:remaining])
                
            # If still need more recommendations, add trending events
            if len(recommended_events) < limit:
                # Add trending events not already recommended
                remaining = limit - len(recommended_events)
                recommended_ids = [e['id'] for e in recommended_events]
                trending_events = [e for e in all_events 
                                  if e['id'] not in already_seen and e['id'] not in recommended_ids]
                
                # Shuffle trending events to add randomness
                random.shuffle(trending_events)
                recommended_events.extend(trending_events[:remaining])
                
            if recommended_events:
                logger.info(f"Returning {len(recommended_events)} personalized recommendations")
                return recommended_events[:limit]
    
    # Default strategy for new users or when personalization fails:
    # Mix of trending and random recommendations
    logger.info("Generating mixed trending/random recommendations")
    
    # Get some trending events
    recent_time = datetime.utcnow() - timedelta(days=30)
    popular_events = db.query(
        EventClick.event_id,
        func.count(EventClick.id).label('click_count')
    ).filter(
        EventClick.timestamp > recent_time
    ).group_by(
        EventClick.event_id
    ).order_by(
        desc('click_count')
    ).limit(max(limit // 2, 1)).all()
    
    popular_event_ids = [event.event_id for event in popular_events]
    
    # First, try to fill with trending events
    trending_recommendations = [event for event in all_events if event['id'] in popular_event_ids]
    
    # If not enough trending events, get random ones to fill
    if len(trending_recommendations) < limit:
        remaining = limit - len(trending_recommendations)
        already_recommended = set(e['id'] for e in trending_recommendations)
        
        # Get all events not already recommended
        other_events = [event for event in all_events if event['id'] not in already_recommended]
        
        # Shuffle them for randomness
        random.shuffle(other_events)
        
        # Add random events to recommendations
        trending_recommendations.extend(other_events[:remaining])
    
    # If still not enough, just return random selection
    if not trending_recommendations:
        random_selection = random.sample(all_events, min(limit, len(all_events)))
        logger.info(f"Returning {len(random_selection)} random recommendations")
        return random_selection
    
    logger.info(f"Returning {len(trending_recommendations)} mixed recommendations")
    return trending_recommendations[:limit]

if __name__ == "__main__":
    import uvicorn
    import asyncio
    uvicorn.run(app, host="0.0.0.0", port=8080) 