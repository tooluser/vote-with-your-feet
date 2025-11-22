// WebSocket client for real-time updates
const socket = io();

socket.on('connect', function () {
    console.log('Connected to server');
});

socket.on('vote_cast', function (data) {
    console.log('Vote cast:', data);
    updateDisplay();
});

socket.on('poll_activated', function (data) {
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
                const verticalBarA = document.getElementById('vertical-bar-a');
                const verticalBarB = document.getElementById('vertical-bar-b');

                const total = data.poll.count_a + data.poll.count_b;
                const percentA = total > 0 ? (data.poll.count_a / total * 100) : 0;
                const percentB = total > 0 ? (data.poll.count_b / total * 100) : 0;

                if (countA) countA.textContent = data.poll.count_a;
                if (countB) countB.textContent = data.poll.count_b;

                if (verticalBarA) verticalBarA.style.height = percentA + '%';
                if (verticalBarB) verticalBarB.style.height = percentB + '%';
            }
        })
        .catch(error => console.error('Error updating display:', error));
}

setInterval(updateDisplay, 5000);

