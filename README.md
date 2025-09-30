# Hey Gen Clone

A full-stack AI-powered video generation platform built with Next.js, featuring photo-to-video generation, video translation, and audio replacement capabilities.

## 🏗️ System Architecture

```mermaid
graph TB
    subgraph "Frontend (Next.js)"
        A[React Components]
        B[Next.js API Routes]
        C[Authentication]
        D[File Upload]
    end
    
    subgraph "Backend Services"
        E[Text-to-Speech Service]
        F[Photo-to-Video Service]
        G[File-to-S3 Service]
        H[Video Translation Service]
    end
    
    subgraph "External Services"
        I[AWS S3]
        J[FAL AI]
        K[Modal Labs]
        L[Polar API]
    end
    
    subgraph "Database"
        M[PostgreSQL]
        N[Prisma ORM]
    end
    
    A --> B
    B --> E
    B --> F
    B --> G
    B --> H
    E --> I
    F --> I
    G --> I
    H --> I
    F --> J
    E --> K
    F --> K
    B --> L
    B --> M
    M --> N
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ 
- Python 3.8+
- PostgreSQL
- AWS Account
- Modal Labs Account
- FAL AI Account
- Polar API Account

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hey-gen-clone
   ```

2. **Set up environment variables**
   ```bash
   # Copy the dummy environment variables
   cp dummy-env-vars.txt frontend/.env
   
   # Edit the .env file with your actual values
   nano frontend/.env
   ```

3. **Database Setup**
   ```bash
   cd frontend
   npm install
   npx prisma generate
   npx prisma db push
   ```

4. **Start the development servers**
   ```bash
   # Frontend (Terminal 1)
   cd frontend
   npm run dev
   
   # Backend services (Terminal 2-4)
   cd backend/text-to-speech
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python tts.py
   ```

## 📁 Project Structure

```
hey-gen-clone/
├── frontend/                 # Next.js application
│   ├── src/
│   │   ├── app/             # App router pages
│   │   ├── components/      # React components
│   │   ├── actions/         # Server actions
│   │   ├── lib/             # Utilities and configurations
│   │   └── hooks/           # Custom React hooks
│   ├── prisma/              # Database schema
│   └── package.json
├── backend/                 # Python microservices
│   ├── text-to-speech/      # TTS service
│   ├── photo-to-video/      # PTV service
│   ├── file-to-s3/          # File upload service
│   └── sieve-to-s3/         # Video processing service
└── README.md
```

## 🔧 Environment Variables

### Frontend (.env)

```bash
# Database
DATABASE_URL="postgresql://username:password@localhost:5432/database_name"

# Environment
NODE_ENV="development"

# Modal API (for AI services)
MODAL_KEY="your_modal_key"
MODAL_SECRET="your_modal_secret"

# AWS Configuration
AWS_ACCESS_KEY_ID="your_aws_access_key"
AWS_SECRET_ACCESS_KEY_ID="your_aws_secret_key"
AWS_REGION="us-east-1"
S3_BUCKET_NAME="your-s3-bucket-name"

# API Endpoints
TEXT_TO_SPEECH_ENDPOINT="http://localhost:8001"
PHOTO_TO_VIDEO_ENDPOINT="http://localhost:8002"
FILE_TO_S3_ENDPOINT="http://localhost:8003"

# Polar API (for payments)
POLAR_ACCESS_TOKEN="your_polar_access_token"
POLAR_WEBHOOK_SECRET="your_polar_webhook_secret"

# FAL AI
FAL_KEY="your_fal_key"

# Client-side environment variables
NEXT_PUBLIC_SMALL_CREDIT_PACK_ID="small_pack_id"
NEXT_PUBLIC_MEDIUM_CREDIT_PACK_ID="medium_pack_id"
NEXT_PUBLIC_LARGE_CREDIT_PACK_ID="large_pack_id"
```

### Backend Services

Each backend service requires its own environment configuration:

#### Text-to-Speech Service
```bash
# backend/text-to-speech/.env
MODAL_KEY="your_modal_key"
MODAL_SECRET="your_modal_secret"
AWS_ACCESS_KEY_ID="your_aws_access_key"
AWS_SECRET_ACCESS_KEY="your_aws_secret_key"
AWS_REGION="us-east-1"
S3_BUCKET_NAME="your-s3-bucket-name"
```

#### Photo-to-Video Service
```bash
# backend/photo-to-video/.env
FAL_KEY="your_fal_key"
AWS_ACCESS_KEY_ID="your_aws_access_key"
AWS_SECRET_ACCESS_KEY="your_aws_secret_key"
AWS_REGION="us-east-1"
S3_BUCKET_NAME="your-s3-bucket-name"
```

## 🛠️ Development Setup

### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Database setup**
   ```bash
   # Generate Prisma client
   npx prisma generate
   
   # Run database migrations
   npx prisma db push
   
   # Open Prisma Studio (optional)
   npx prisma studio
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

4. **Available scripts**
   ```bash
   npm run dev          # Start development server
   npm run build        # Build for production
   npm run start        # Start production server
   npm run lint         # Run ESLint
   npm run format:write # Format code with Prettier
   ```

### Backend Services Setup

#### Text-to-Speech Service

1. **Setup Python environment**
   ```bash
   cd backend/text-to-speech
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run the service**
   ```bash
   python tts.py
   ```

#### Photo-to-Video Service

1. **Setup Python environment**
   ```bash
   cd backend/photo-to-video
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run the service**
   ```bash
   python ptv.py
   ```

#### File-to-S3 Service

1. **Setup Python environment**
   ```bash
   cd backend/file-to-s3
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run the service**
   ```bash
   python file_to_s3.py
   ```

## 🗄️ Database Schema

The application uses PostgreSQL with Prisma ORM. Key models include:

- **User**: User accounts with authentication and credits
- **PhotoToVideoGeneration**: Photo-to-video generation jobs
- **VideoTranslationGeneration**: Video translation jobs
- **ChangeVideoAudioGeneration**: Audio replacement jobs
- **Session**: User sessions
- **Account**: OAuth accounts

## 🔌 API Endpoints

### Frontend API Routes

- `POST /api/auth/[...all]` - Authentication endpoints
- `POST /api/fal` - FAL AI integration
- `POST /api/inngest` - Background job processing

### Backend Services

- **Text-to-Speech**: `http://localhost:8001`
- **Photo-to-Video**: `http://localhost:8002`
- **File-to-S3**: `http://localhost:8003`

## 🎨 Features

### Core Functionality

1. **Photo-to-Video Generation**
   - Upload photos and generate talking head videos
   - Multiple voice options and expressiveness controls
   - High-resolution output support

2. **Video Translation**
   - Translate videos to different languages
   - Maintain original voice characteristics
   - Support for multiple target languages

3. **Audio Replacement**
   - Replace audio in existing videos
   - Maintain lip-sync accuracy
   - Support for various audio formats

4. **User Management**
   - OAuth authentication
   - Credit-based system
   - Generation history tracking

### Technical Features

- **Real-time Processing**: Background job processing with Inngest
- **File Management**: AWS S3 integration for media storage
- **AI Integration**: FAL AI and Modal Labs for AI services
- **Payment Processing**: Polar API integration
- **Responsive Design**: Mobile-first UI with Tailwind CSS

## 🚀 Deployment

### Frontend Deployment (Vercel)

1. **Connect repository to Vercel**
2. **Set environment variables in Vercel dashboard**
3. **Deploy automatically on push to main**

### Backend Deployment

Each service can be deployed independently:

1. **Modal Labs**: For AI processing services
2. **AWS Lambda**: For serverless functions
3. **Docker**: For containerized deployment

## 🔒 Security

- Environment variables for sensitive data
- OAuth authentication with Better Auth
- AWS IAM roles for S3 access
- API key management for external services

## 📊 Monitoring

- Database monitoring with Prisma
- File upload tracking
- Generation job status monitoring
- Credit usage tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE.MD file for details.

## 🆘 Support

For support and questions:

1. Check the documentation
2. Review existing issues
3. Create a new issue with detailed information

## 🔄 Updates

- Regular dependency updates
- Security patches
- Feature enhancements
- Performance optimizations
