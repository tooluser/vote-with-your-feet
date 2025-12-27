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
ADMIN_SECRET=your-secure-secret        # Required to access admin panel
VOTE_PASSWORD=your-vote-password       # Required to cast votes via API
DATABASE_URL=sqlite:///data/votes.db   # For local dev; Docker uses /app/data/votes.db
SECRET_KEY=your-flask-secret-key
```

The database file will be created automatically on first run. When using Docker, the database persists in the `./data` directory on your host machine.

## Running the Application

### Development Mode

```bash
uv run python app/main.py
```

The application will be available at:

- Display (with votes): <http://localhost:8080/display>
- Display (no votes): <http://localhost:8080/display-no-votes>
- Display (completed): <http://localhost:8080/display-completed>
- Admin: <http://localhost:8080/admin?secret=YOUR_SECRET>
- API: <http://localhost:8080/api/vote>

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

Votes require the `X-Vote-Password` header and an `answer` query parameter (`A` or `B`):

```bash
curl -X POST "http://localhost:8080/vote?answer=A" \
  -H "X-Vote-Password: your-vote-password"
```

**Response:**

```json
{"success": true, "poll_id": 1}
```

**Errors:**

- `403` — missing or incorrect `X-Vote-Password`
- `400` — no active poll, missing answer, or invalid answer

### Get Display Data

```bash
curl http://localhost:8080/api/display/data
```

## Admin Interface

1. Navigate to `/admin?secret=YOUR_SECRET`
2. Create a new poll with a question and two answer options
3. Click "Activate" to make a poll active
4. Only one poll can be active at a time

## Display Interface

Three display modes are available:

### `/display` — Live Results

Split-screen view showing real-time vote counts:

- Poll question at the top
- Answer A on the left (blue) with vote count
- Answer B on the right (orange) with vote count
- Real-time updates via WebSockets

### `/display-no-votes` — Options Only

Shows the active poll question and answer options without revealing vote counts. Useful for displaying the poll to voters before or during voting.

### `/display-completed` — Historical Results

A 2×2 grid of completed (inactive) polls with their final results. Each card shows the question, answers, vote counts, and percentage bars.

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
│   ├── admin.html           # Admin dashboard
│   ├── admin_edit_poll.html # Edit poll form
│   ├── admin_edit_votes.html # Edit vote counts
│   ├── display.html         # Live results display
│   ├── display_no_votes.html # Options-only display
│   └── display_completed.html # Historical results grid
├── static/
│   ├── css/
│   │   ├── admin.css
│   │   ├── display.css
│   │   └── display_completed.css
│   └── js/
│       ├── display.js       # WebSocket client
│       └── display_completed.js
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
