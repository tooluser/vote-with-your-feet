from app import create_app, socketio
from flask_socketio import emit


app = create_app()


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')


def emit_vote_cast(poll_id):
    """Emit vote cast event to all connected clients"""
    socketio.emit('vote_cast', {'poll_id': poll_id})


def emit_poll_activated(poll_id):
    """Emit poll activated event to all connected clients"""
    socketio.emit('poll_activated', {'poll_id': poll_id})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

