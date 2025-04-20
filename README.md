# Compatibility Matrix API with Supabase

Backend API for the Compatibility Matrix System, developed with FastAPI and Supabase.

## Overview

The Compatibility Matrix API powers the backend services for measuring and analyzing compatibility between individuals across multiple dimensions including personality traits, values, interests, communication styles, and more.

## Features

- User authentication (using Supabase Auth)
- User profile management
- Assessment delivery and response collection
- Compatibility calculation algorithms
- Matrix visualization data
- Connection management

## Tech Stack

- **Framework**: FastAPI
- **Database & Auth**: Supabase
- **API Documentation**: OpenAPI (Swagger UI)

## Prerequisites

- Python 3.10+
- A Supabase account and project

## Supabase Setup

1. **Create a Supabase Project**
   - Sign up at [supabase.com](https://supabase.com) if you haven't already
   - Create a new project

2. **Set Up Database Tables**
   - Navigate to the SQL Editor in your Supabase dashboard
   - Run the following SQL scripts to create the necessary tables:

```sql
-- Create profiles table
CREATE TABLE profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  email TEXT NOT NULL,
  name TEXT NOT NULL,
  avatar_url TEXT,
  bio TEXT,
  location TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create assessment_dimensions table
CREATE TABLE assessment_dimensions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  description TEXT,
  weight INTEGER DEFAULT 1,
  order_index INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create assessment_questions table
CREATE TABLE assessment_questions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  dimension_id UUID REFERENCES assessment_dimensions(id) NOT NULL,
  text TEXT NOT NULL,
  options JSONB NOT NULL,
  weight INTEGER DEFAULT 1,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create user_assessments table
CREATE TABLE user_assessments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES profiles(id) NOT NULL,
  dimension_id UUID REFERENCES assessment_dimensions(id) NOT NULL,
  status TEXT NOT NULL,
  progress INTEGER DEFAULT 0,
  responses JSONB DEFAULT '[]',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create compatibility_scores table
CREATE TABLE compatibility_scores (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id_a UUID REFERENCES profiles(id) NOT NULL,
  user_id_b UUID REFERENCES profiles(id) NOT NULL,
  overall_score INTEGER NOT NULL,
  dimension_scores JSONB DEFAULT '[]',
  strengths JSONB DEFAULT '[]',
  challenges JSONB DEFAULT '[]',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  -- Ensure only one record per user pair
  CONSTRAINT unique_user_pair UNIQUE (user_id_a, user_id_b),
  -- Ensure user_id_a is always less than user_id_b to avoid duplicates
  CONSTRAINT user_order CHECK (user_id_a < user_id_b)
);
```

3. **Set Up Row Level Security Policies**
   - Configure RLS policies to secure your data:

```sql
-- Enable RLS on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_dimensions ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE compatibility_scores ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view their own profile"
  ON profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
  ON profiles FOR UPDATE
  USING (auth.uid() = id);

-- Assessment dimensions policies (readable by all authenticated users)
CREATE POLICY "Assessment dimensions are viewable by all authenticated users"
  ON assessment_dimensions FOR SELECT
  USING (auth.role() = 'authenticated');

-- Assessment questions policies
CREATE POLICY "Assessment questions are viewable by all authenticated users"
  ON assessment_questions FOR SELECT
  USING (auth.role() = 'authenticated');

-- User assessments policies
CREATE POLICY "Users can view their own assessments"
  ON user_assessments FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own assessments"
  ON user_assessments FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own assessments"
  ON user_assessments FOR UPDATE
  USING (auth.uid() = user_id);

-- Compatibility scores policies
CREATE POLICY "Users can view compatibility scores they're part of"
  ON compatibility_scores FOR SELECT
  USING (auth.uid() = user_id_a OR auth.uid() = user_id_b);
```

4. **Set Up Auth**
   - Configure Email Auth in Supabase Auth settings
   - Optionally enable social providers

5. **Get API Keys**
   - From your Supabase project dashboard, get:
     - Project URL
     - API Key (anon public)
     - Service Role Key (keep this secret)

## Local Development Setup

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

Edit the `.env` file with your Supabase project details:

```
# Application
APP_NAME=Compatibility Matrix

# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

5. **Run the application**

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
  │   ├── api/                   # API endpoints
  │   │   ├── v1/
  │   │   │   ├── endpoints/     # API route handlers
  │   │   │   │   ├── auth.py    # Authentication endpoints
  │   │   │   │   ├── users.py   # User endpoints
  │   │   │   │   ├── assessments.py  # Assessment endpoints
  │   │   │   │   ├── compatibility.py  # Compatibility endpoints
  │   │   │   ├── api.py         # API router
  │   │   ├── dependencies/      # API dependencies
  │   │       ├── auth.py        # Auth dependencies
  │   ├── core/                  # Core application code
  │   │   ├── config.py          # Configuration settings
  │   ├── db/                    # Database setup
  │   │   ├── supabase.py        # Supabase client
  │   ├── models/                # Pydantic models
  │   │   ├── user.py            # User models
  │   ├── main.py                # Application entry point
  ├── requirements.txt           # Python dependencies
  ├── .env.sample                # Sample environment variables
  ├── .gitignore                 # Git ignore configuration
  ├── README.md                  # Project documentation
```

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Login and get access token
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout
- `POST /api/v1/auth/send-reset-password` - Send password reset email

### Users

- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update current user profile
- `GET /api/v1/users/{user_id}` - Get user by ID

### Assessments

- `GET /api/v1/assessments` - Get all assessments for the current user
- `POST /api/v1/assessments` - Start a new assessment
- `GET /api/v1/assessments/{assessment_id}` - Get assessment details
- `PUT /api/v1/assessments/{assessment_id}` - Update assessment with new responses
- `GET /api/v1/assessments/questions/{dimension_id}` - Get questions for a dimension
- `POST /api/v1/assessments/responses` - Submit assessment responses

### Compatibility

- `GET /api/v1/compatibility/matrix` - Get compatibility matrix
- `GET /api/v1/compatibility/{user_id}` - Get compatibility with specific user
- `GET /api/v1/compatibility/report/{user_id}` - Get detailed compatibility report

## Authentication Flow

1. **Registration**: Users register with email, name, and password using Supabase Auth
2. **Email Verification**: Supabase sends verification email
3. **Login**: Users login with email and password to receive JWT access and refresh tokens
4. **Access Protected Routes**: JWT is sent in Authorization header for protected endpoints
5. **Token Refresh**: When access token expires, refresh token is used to obtain a new one
6. **Logout**: Session is invalidated in Supabase Auth

## Development Guidelines

### Adding New Endpoints

1. Create a new file in `app/api/v1/endpoints/` for the feature
2. Define the routes and handlers
3. Include the router in `app/api/v1/api.py`
4. Create necessary models in `app/models/`
5. Add the necessary tables to Supabase

### Testing

Use the Swagger UI at http://localhost:8000/docs to test API endpoints during development.

## Deployment

### Production Setup

For production deployment:

1. Configure your Supabase project for production
2. Update environment variables for production
3. Deploy the API to your preferred hosting platform (e.g., Heroku, Azure, AWS)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [Supabase](https://supabase.com/)
- [Pydantic](https://pydantic-docs.helpmanual.io/)