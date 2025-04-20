# Compatibility Matrix API

Backend API for the Compatibility Matrix System, developed with FastAPI and PostgreSQL.

## Overview

The Compatibility Matrix API powers the backend services for measuring and analyzing compatibility between individuals across multiple dimensions including personality traits, values, interests, communication styles, and more.

## Features

- User authentication (JWT with refresh tokens)
- User profile management
- Assessment delivery and response collection
- Compatibility calculation algorithms
- Matrix visualization data
- Connection management

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT (JSON Web Tokens)
- **Password Hashing**: Bcrypt
- **API Documentation**: OpenAPI (Swagger UI)
- **Database Migrations**: Alembic
- **Testing**: Pytest

## Setup Instructions

### Prerequisites

- Python 3.10+
- PostgreSQL
- Git

### Local Development Setup

1. **Clone the repository**

```bash
git clone https://github.com/your-username/compatibility-matrix-api.git
cd compatibility-matrix-api
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Create environment variables file**

Create a `.env` file in the root directory based on the provided `.env.sample`:

```bash
cp .env.sample .env
```

Edit the `.env` file with your configuration details:

```
# Application
APP_NAME=Compatibility Matrix

# Security
JWT_SECRET_KEY=your_generated_secret_key
JWT_REFRESH_SECRET_KEY=your_generated_refresh_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=compatibility_matrix

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

Generate secure keys for JWT:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

5. **Set up the database**

Create a PostgreSQL database named "compatibility_matrix":

```bash
createdb compatibility_matrix
```

The application will create the necessary tables automatically on startup.

6. **Run the application**

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
compatibility-matrix-api/
  ├── app/
  │   ├── api/                  # API endpoints
  │   │   ├── v1/
  │   │   │   ├── endpoints/    # API route handlers
  │   │   │   │   ├── auth.py   # Authentication endpoints
  │   │   │   │   ├── users.py  # User endpoints
  │   │   │   ├── api.py        # API router
  │   │   ├── dependencies/     # API dependencies
  │   │       ├── auth.py       # Auth dependencies
  │   ├── core/                 # Core application code
  │   │   ├── config.py         # Configuration settings
  │   ├── db/                   # Database setup
  │   │   ├── database.py       # Database connection
  │   ├── models/               # Database models
  │   │   ├── user.py           # User model
  │   ├── services/             # Business logic
  │   │   ├── auth.py           # Auth service
  │   ├── main.py               # Application entry point
  ├── migrations/               # Database migrations
  ├── tests/                    # Test suite
  ├── requirements.txt          # Python dependencies
  ├── .env.sample               # Sample environment variables
  ├── .gitignore                # Git ignore configuration
  ├── README.md                 # Project documentation
```

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Login and get access token
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout

### Users

- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update current user profile
- `GET /api/v1/users/{user_id}` - Get user by ID

### Assessment (Coming Soon)

- `GET /api/v1/assessments` - Get all assessments
- `POST /api/v1/assessments` - Start a new assessment
- `GET /api/v1/assessments/{assessment_id}` - Get assessment details
- `PUT /api/v1/assessments/{assessment_id}` - Update assessment
- `GET /api/v1/questions` - Get assessment questions
- `POST /api/v1/responses` - Submit assessment responses

### Compatibility (Coming Soon)

- `GET /api/v1/compatibility` - Get compatibility matrix
- `GET /api/v1/compatibility/{user_id}` - Get compatibility with specific user
- `GET /api/v1/compatibility/report/{user_id}` - Get detailed compatibility report

## Authentication Flow

1. **Registration**: Users register with email, name, and password
2. **Login**: Users login with email and password to receive JWT access and refresh tokens
3. **Access Protected Routes**: Access token is sent in Authorization header for protected endpoints
4. **Token Refresh**: When access token expires, refresh token is used to obtain a new one
5. **Logout**: Tokens are removed client-side

## Database Schema

### Users Table

| Column         | Type      | Description                   |
|----------------|-----------|-------------------------------|
| id             | Integer   | Primary key                   |
| email          | String    | Unique user email             |
| name           | String    | User's full name              |
| password_hash  | String    | Hashed password               |
| created_at     | DateTime  | Account creation timestamp    |
| is_active      | Boolean   | Account status                |
| is_verified    | Boolean   | Email verification status     |

Additional tables for assessments, responses, and compatibility scores will be added as development progresses.

## Development Guidelines

### Code Style

We follow PEP 8 style guide for Python code. Please install and run flake8 before committing changes:

```bash
pip install flake8
flake8 .
```

### Testing

Tests are written using pytest. Run the tests with:

```bash
pytest
```

### Adding New Endpoints

1. Create a new file in `app/api/v1/endpoints/` for the feature
2. Define the routes and handlers
3. Include the router in `app/api/v1/api.py`
4. Create necessary models in `app/models/`
5. Implement business logic in `app/services/`
6. Add tests in `tests/`

## Deployment

### Production Setup

For production deployment:

1. Set up a production PostgreSQL database
2. Update environment variables for production
3. Use a production ASGI server like Gunicorn with Uvicorn workers:

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

### Docker Deployment (Coming Soon)

Docker configuration will be provided in a future update.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Pydantic](https://pydantic-docs.helpmanual.io/)
- [JWT](https://jwt.io/)