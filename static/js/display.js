// WebSocket client for real-time updates
const socket = io();

socket.on('connect', function() {
    console.log('Connected to server');
});

socket.on('vote_cast', function(data) {
    console.log('Vote cast:', data);
    updateDisplay();
});

socket.on('poll_activated', function(data) {
    console.log('Poll activated:', data);
    location.reload();
});

function updateDisplay() {
    fetch('/api/display/data')
        .then(response => response.json())
        .then(data => {
            if (data.poll) {
                const countA = document.getElementById('count-a');
                const countB = document.getElementById('count-b');
                
                if (countA) countA.textContent = data.poll.count_a;
                if (countB) countB.textContent = data.poll.count_b;
            }
        })
        .catch(error => console.error('Error updating display:', error));
}

setInterval(updateDisplay, 5000);

