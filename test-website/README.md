# Fantasy Sports Frontend

This directory contains the V0-generated frontend for the Fantasy Sports API.

## Structure
```
frontend/
├── src/                    # Source files
├── public/                 # Static assets
├── package.json           # Dependencies
└── README.md              # This file
```

## API Integration

The frontend connects to the Fantasy Sports API running on:
- **Local Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Key API Endpoints

### Authentication
- **Kinde Login**: `/auth/login`
- **User Profile**: `/api/user/profile`

### Fantasy Data
- **User Leagues**: `/api/user/leagues`
- **League Details**: `/api/leagues/{league_id}`
- **Team Rosters**: `/api/leagues/{league_id}/teams`
- **API Keys**: `/api/user/api-keys`

## Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
VITE_KINDE_DOMAIN=fantasysnipe.kinde.com
VITE_KINDE_CLIENT_ID=your_client_id
VITE_KINDE_REDIRECT_URI=http://localhost:3000/callback
```

## Development

1. Install dependencies: `npm install`
2. Start development server: `npm run dev`
3. Build for production: `npm run build`

## Features

- **Multi-user authentication** with Kinde
- **Fantasy league management**
- **Team roster viewing**
- **Player analytics integration**
- **Real-time data updates** 