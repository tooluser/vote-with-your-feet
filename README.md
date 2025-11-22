# Vote With Your Feet

A real-time polling application with admin interface, voting API, and live display interface. Built with Flask and WebSockets for a school project.

## Features

- **Admin Interface**: Create and manage polls, activate/deactivate polls
- **Voting API**: REST API for casting votes (A or B)
- **Live Display**: Split-screen display showing real-time vote counts
- **WebSocket Updates**: Instant updates when votes are cast
- **Simple Authentication**: Shared secret for admin access
- **SQLite Database**: Lightweight database for storing polls and votes

## Setup

This project uses [UV](https://github.com/astral-sh/uv) for dependency management.

```bash
uv sync
```

## Configuration

Set environment variables (or create a `.env` file):

```bash
ADMIN_SECRET=your-secure-secret
DATABASE_URL=sqlite:///votes.db
SECRET_KEY=your-flask-secret-key
```

## Running the Application

### Development Mode

```bash
uv run python app/main.py
```

The application will be available at:

- Display: <http://localhost:5000/display>
- Admin: <http://localhost:5000/admin?secret=YOUR_SECRET>
- API: <http://localhost:5000/api/vote>

### Docker

```bash
docker-compose up
```

## Running Tests

Run all tests:

```bash
uv run pytest
```

Run with verbose output:

```bash
uv run pytest -v
```

Run specific test file:

```bash
uv run pytest tests/test_models.py -v
```

## API Usage

### Cast a Vote

```bash
curl -X POST http://localhost:5000/api/vote \
  -H "Content-Type: application/json" \
  -d '{"answer": "A"}'
```

### Get Display Data

```bash
curl http://localhost:5000/api/display/data
```

## Admin Interface

1. Navigate to `/admin?secret=YOUR_SECRET`
2. Create a new poll with a question and two answer options
3. Click "Activate" to make a poll active
4. Only one poll can be active at a time

## Display Interface

Navigate to `/display` to see the live split-screen view with:

- Poll question at the top
- Answer A on the left (blue) with vote count
- Answer B on the right (orange) with vote count
- Real-time updates via WebSockets

## Deployment

See [docs/AWS_DEPLOYMENT.md](docs/AWS_DEPLOYMENT.md) for detailed AWS deployment instructions.

## Project Structure

```
vote_with_your_feet/
├── app/
│   ├── __init__.py          # App factory
│   ├── main.py              # Entry point
│   ├── config.py            # Configuration
│   ├── database.py          # DB initialization
│   ├── models.py            # SQLAlchemy models
│   ├── middleware/
│   │   └── auth.py          # Secret validation
│   └── routes/
│       ├── admin.py         # Admin blueprint
│       └── api.py           # Voting API + WebSocket
├── templates/
│   ├── admin.html           # Admin interface
│   └── display.html         # Display interface
├── static/
│   ├── css/
│   │   ├── admin.css
│   │   └── display.css
│   └── js/
│       └── display.js       # WebSocket client
├── tests/                   # Pytest test suite
├── docs/
│   └── AWS_DEPLOYMENT.md
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Technology Stack

- **Backend**: Flask with Flask-SocketIO
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML/CSS/JavaScript with Socket.IO client
- **Deployment**: Docker container, deployable to AWS EC2/ECS/Lightsail

## License

MIT
