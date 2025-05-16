
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional, Union
import sqlite3
import uuid
import os
from pathlib import Path
import uvicorn

# Create the FastAPI app
app = FastAPI(
    title="Recipe Sharing App API",
    description="API for uploading, rating, and commenting on recipes.",
    version="1.0.0"
)

# Define Pydantic models for request and response validation
class RecipeBase(BaseModel):
    title: str
    ingredients: List[str]
    instructions: str

class RecipeComment(BaseModel):
    comment: str

class RecipeRating(BaseModel):
    rating: int = Field(..., ge=1, le=5)

class Recipe(RecipeBase):
    id: str
    comments: List[dict] = []
    avgRating: Optional[float] = None

# Database setup
def init_db():
    conn = sqlite3.connect('db.sqlite3', check_same_thread=False)
    cursor = conn.cursor()
    
    # Create recipes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS recipes (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        ingredients TEXT NOT NULL,
        instructions TEXT NOT NULL
    )
    ''')
    
    # Create comments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id TEXT PRIMARY KEY,
        recipe_id TEXT NOT NULL,
        comment TEXT NOT NULL,
        FOREIGN KEY (recipe_id) REFERENCES recipes (id)
    )
    ''')
    
    # Create ratings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ratings (
        id TEXT PRIMARY KEY,
        recipe_id TEXT NOT NULL,
        rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
        FOREIGN KEY (recipe_id) REFERENCES recipes (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Database connection dependency
def get_db():
    conn = sqlite3.connect('db.sqlite3', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Helper function to convert a recipe from DB to API model
def recipe_to_model(recipe_row, comments=None, avg_rating=None):
    recipe = dict(recipe_row)
    recipe['ingredients'] = recipe['ingredients'].split('||')
    
    if comments is None:
        comments = []
    
    recipe['comments'] = comments
    recipe['avgRating'] = avg_rating
    
    return Recipe(**recipe)

# Setup templates for HTML responses
templates = Jinja2Templates(directory="templates")

# Create templates directory if it doesn't exist
os.makedirs("templates", exist_ok=True)

# Create basic HTML templates
with open("templates/recipe_overview.html", "w") as f:
    f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Recipe Overview</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        h1 { color: #333; }
        .recipe-list { list-style: none; padding: 0; }
        .recipe-item { margin-bottom: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .recipe-title { font-weight: bold; }
        .recipe-rating { color: #f90; }
    </style>
</head>
<body>
    <h1>Recipe Overview</h1>
    
    <h2>Recent Recipes</h2>
    <ul class="recipe-list">
        {% for recipe in recent_recipes %}
        <li class="recipe-item">
            <div class="recipe-title"><a href="/recipes/{{ recipe.id }}">{{ recipe.title }}</a></div>
            {% if recipe.avgRating %}
            <div class="recipe-rating">Rating: {{ recipe.avgRating }}/5</div>
            {% else %}
            <div class="recipe-rating">No ratings yet</div>
            {% endif %}
        </li>
        {% endfor %}
    </ul>
    
    <h2>Top Rated Recipes</h2>
    <ul class="recipe-list">
        {% for recipe in top_recipes %}
        <li class="recipe-item">
            <div class="recipe-title"><a href="/recipes/{{ recipe.id }}">{{ recipe.title }}</a></div>
            <div class="recipe-rating">Rating: {{ recipe.avgRating }}/5</div>
        </li>
        {% endfor %}
    </ul>
</body>
</html>
''')

with open("templates/recipe_detail.html", "w") as f:
    f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>{{ recipe.title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        h1 { color: #333; }
        .recipe-section { margin-bottom: 20px; }
        .ingredients-list { list-style: disc; padding-left: 20px; }
        .instructions { white-space: pre-line; }
        .rating-section { margin: 20px 0; }
        .comments-section { margin-top: 30px; }
        .comment { padding: 10px; border: 1px solid #ddd; margin-bottom: 10px; border-radius: 5px; }
        form { margin-top: 20px; }
        input, textarea, button { padding: 8px; margin-bottom: 10px; }
        .rating-stars { font-size: 24px; }
        .rating-stars span { cursor: pointer; }
    </style>
</head>
<body>
    <h1>{{ recipe.title }}</h1>
    
    <div class="recipe-section">
        <h2>Ingredients</h2>
        <ul class="ingredients-list">
            {% for ingredient in recipe.ingredients %}
            <li>{{ ingredient }}</li>
            {% endfor %}
        </ul>
    </div>
    
    <div class="recipe-section">
        <h2>Instructions</h2>
        <div class="instructions">{{ recipe.instructions }}</div>
    </div>
    
    <div class="rating-section">
        <h2>Rating</h2>
        {% if recipe.avgRating %}
        <div>Average Rating: {{ recipe.avgRating }}/5</div>
        {% else %}
        <div>No ratings yet</div>
        {% endif %}
        
        <form action="/recipes/{{ recipe.id }}/ratings" method="post">
            <div class="rating-stars">
                <span onclick="document.getElementById('rating').value='1'">★</span>
                <span onclick="document.getElementById('rating').value='2'">★</span>
                <span onclick="document.getElementById('rating').value='3'">★</span>
                <span onclick="document.getElementById('rating').value='4'">★</span>
                <span onclick="document.getElementById('rating').value='5'">★</span>
            </div>
            <input type="hidden" id="rating" name="rating" value="5">
            <button type="submit">Submit Rating</button>
        </form>
    </div>
    
    <div class="comments-section">
        <h2>Comments</h2>
        {% if recipe.comments %}
            {% for comment_item in recipe.comments %}
            <div class="comment">{{ comment_item.comment }}</div>
            {% endfor %}
        {% else %}
            <p>No comments yet.</p>
        {% endif %}
        
        <form action="/recipes/{{ recipe.id }}/comments" method="post">
            <textarea name="comment" rows="4" cols="50" placeholder="Add your comment..."></textarea><br>
            <button type="submit">Submit Comment</button>
        </form>
    </div>
</body>
</html>
''')

# API Endpoints

@app.get("/recipes", response_class=HTMLResponse)
async def get_recipes_overview(request: Request, db: sqlite3.Connection = Depends(get_db)):
    """Get an overview of recipes"""
    cursor = db.cursor()
    
    # Get recent recipes (last 5)
    cursor.execute('''
    SELECT r.id, r.title, r.ingredients, r.instructions,
           ROUND(AVG(rt.rating), 1) as avgRating
    FROM recipes r
    LEFT JOIN ratings rt ON r.id = rt.recipe_id
    GROUP BY r.id
    ORDER BY r.rowid DESC
    LIMIT 5
    ''')
    recent_recipes = []
    for row in cursor.fetchall():
        recipe_dict = dict(row)
        recipe_dict['ingredients'] = recipe_dict['ingredients'].split('||')
        if recipe_dict['avgRating'] is None:
            recipe_dict['avgRating'] = None
        recent_recipes.append(recipe_dict)
    
    # Get top rated recipes (top 5)
    cursor.execute('''
    SELECT r.id, r.title, r.ingredients, r.instructions,
           ROUND(AVG(rt.rating), 1) as avgRating
    FROM recipes r
    JOIN ratings rt ON r.id = rt.recipe_id
    GROUP BY r.id
    HAVING COUNT(rt.rating) > 0
    ORDER BY avgRating DESC
    LIMIT 5
    ''')
    top_recipes = []
    for row in cursor.fetchall():
        recipe_dict = dict(row)
        recipe_dict['ingredients'] = recipe_dict['ingredients'].split('||')
        top_recipes.append(recipe_dict)
    
    return templates.TemplateResponse(
        "recipe_overview.html", 
        {"request": request, "recent_recipes": recent_recipes, "top_recipes": top_recipes}
    )

@app.post("/recipes/upload", response_model=Recipe, status_code=status.HTTP_201_CREATED)
async def upload_recipe(recipe: RecipeBase, db: sqlite3.Connection = Depends(get_db)):
    """Upload a new recipe"""
    recipe_id = str(uuid.uuid4())
    
    # Join ingredients list with a separator for storage
    ingredients_str = "||".join(recipe.ingredients)
    
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO recipes (id, title, ingredients, instructions) VALUES (?, ?, ?, ?)",
        (recipe_id, recipe.title, ingredients_str, recipe.instructions)
    )
    db.commit()
    
    # Return the created recipe
    return Recipe(
        id=recipe_id,
        title=recipe.title,
        ingredients=recipe.ingredients,
        instructions=recipe.instructions,
        comments=[],
        avgRating=None
    )

@app.get("/recipes/{recipe_id}", response_class=HTMLResponse)
async def get_recipe(request: Request, recipe_id: str, db: sqlite3.Connection = Depends(get_db)):
    """Get a recipe by ID"""
    cursor = db.cursor()
    
    # Get recipe
    cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
    recipe_row = cursor.fetchone()
    
    if not recipe_row:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Get comments
    cursor.execute("SELECT comment FROM comments WHERE recipe_id = ?", (recipe_id,))
    comments = [{"comment": row["comment"]} for row in cursor.fetchall()]
    
    # Get average rating
    cursor.execute(
        "SELECT ROUND(AVG(rating), 1) as avg_rating FROM ratings WHERE recipe_id = ?", 
        (recipe_id,)
    )
    avg_rating_row = cursor.fetchone()
    avg_rating = avg_rating_row["avg_rating"] if avg_rating_row and avg_rating_row["avg_rating"] else None
    
    # Convert to model
    recipe = recipe_to_model(recipe_row, comments, avg_rating)
    
    return templates.TemplateResponse(
        "recipe_detail.html", 
        {"request": request, "recipe": recipe}
    )

@app.post("/recipes/{recipe_id}/comments", status_code=status.HTTP_201_CREATED)
async def add_comment(recipe_id: str, comment_data: RecipeComment, db: sqlite3.Connection = Depends(get_db)):
    """Add a comment to a recipe"""
    cursor = db.cursor()
    
    # Check if recipe exists
    cursor.execute("SELECT id FROM recipes WHERE id = ?", (recipe_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Add comment
    comment_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO comments (id, recipe_id, comment) VALUES (?, ?, ?)",
        (comment_id, recipe_id, comment_data.comment)
    )
    db.commit()
    
    return {"message": "Comment added successfully"}

@app.post("/recipes/{recipe_id}/ratings", status_code=status.HTTP_201_CREATED)
async def add_rating(recipe_id: str, rating_data: RecipeRating, db: sqlite3.Connection = Depends(get_db)):
    """Rate a recipe"""
    cursor = db.cursor()
    
    # Check if recipe exists
    cursor.execute("SELECT id FROM recipes WHERE id = ?", (recipe_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Validate rating
    if rating_data.rating < 1 or rating_data.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    # Add rating
    rating_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO ratings (id, recipe_id, rating) VALUES (?, ?, ?)",
        (rating_id, recipe_id, rating_data.rating)
    )
    db.commit()
    
    return {"message": "Rating added successfully"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)