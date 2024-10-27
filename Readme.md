# Blog Project with AI-Powered Auto-Reply

This is a blog platform where users can register, post articles, and comment on each other’s posts. 
The application leverages FastAPI and SQLite for efficient performance, while Google Gemini provides AI-powered 
automated replies to comments, enhancing user engagement. The project is designed with asynchronous testing to ensure 
smooth performance and reliability.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running the Application](#running-the-application)
- [Configurations](#configurations)
- [Testing](#testing)
- [Technologies Used](#technologies-used)
- [License](#license)

## Features
- **User Authentication**: Secure registration and login with JWT-based cookies.
- **Posting and Commenting**: Users can create, view, and delete posts and comments.
- **AI-Powered Auto-Reply**: Comments on posts can receive auto-generated replies, powered by Google Gemini.
- **Admin and User Roles**: Different access levels for standard and admin users.
- **Asynchronous Testing**: Automated tests using pytest with an async test database.

## Installation
1. **Clone the repository**:
   ```bash
    git clone https://github.com/DmytroHlazyrin/Blog_with_AI.git
    cd Blog_with_AI
    ```
2. **Set up a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```
3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Environment Variables
Create a .env file in the root directory and configure the following variables:
   ```text
    DATABASE_URL="sqlite+aiosqlite:///./database.db"  # For development
    GEMINI_API_KEY="your_google_gemini_api_key"       # API key for Google Gemini
    JWT_SECRET="your_jwt_secret"                      # Secret for JWT token generation
   ```

## Running the Application
Start the application with:
   ```bash
   uvicorn app.main:app --reload
   ```
The API will be accessible at http://127.0.0.1:8000.

## Configurations
You could change gemini instructions for auto replying in app/ai/config.py

## Testing
To run tests, use:
   ```bash
   pytest
   ```
This project uses pytest and pytest-asyncio for testing. 
Fixtures are set up to use a separate test database.

## Technologies Used
* Backend: FastAPI, SQLAlchemy, Alembic, SQLite
* AI Integration: Google Gemini API
* Authentication: JWT, Cookies, FastAPI_users
* Testing: Pytest, Pytest-asyncio, Httpx

## License
This project is licensed under the MIT License.