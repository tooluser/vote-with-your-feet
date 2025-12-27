// Rotation logic for completed polls display
(function() {
    // Check if we have more than 4 polls
    if (typeof allPolls === 'undefined' || allPolls.length <= 4) {
        return; // No rotation needed
    }

    const POLLS_PER_PAGE = 4;
    const ROTATION_INTERVAL = 10000; // 10 seconds
    const FADE_DURATION = 300; // milliseconds, matches CSS transition

    let currentPage = 0;
    const totalPages = Math.ceil(allPolls.length / POLLS_PER_PAGE);

    const gridContainer = document.getElementById('grid-container');
    const currentPageEl = document.getElementById('current-page');

    // Defensive check for required DOM elements
    if (!gridContainer || !currentPageEl) {
        console.error('Required DOM elements not found for rotation');
        return;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatPercent(count_a, count_b) {
        const total = count_a + count_b;
        if (total === 0) return { percent_a: 0, percent_b: 0 };

        return {
            percent_a: (count_a / total) * 100,
            percent_b: (count_b / total) * 100
        };
    }

    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    function createPollCard(pollData, index) {
        const percents = formatPercent(pollData.count_a, pollData.count_b);

        return `
            <div class="poll-card fade-in" data-poll-index="${index}">
                <div class="poll-question">
                    <h2>${escapeHtml(pollData.poll.question)}</h2>
                </div>

                <div class="poll-results">
                    <div class="answer-result answer-a">
                        <div class="answer-label">${escapeHtml(pollData.poll.answer_a)}</div>
                        <div class="bar-container">
                            <div class="bar bar-a" style="width: ${percents.percent_a}%"></div>
                        </div>
                        <div class="vote-count">${pollData.count_a} votes (${Math.round(percents.percent_a)}%)</div>
                    </div>

                    <div class="answer-result answer-b">
                        <div class="answer-label">${escapeHtml(pollData.poll.answer_b)}</div>
                        <div class="bar-container">
                            <div class="bar bar-b" style="width: ${percents.percent_b}%"></div>
                        </div>
                        <div class="vote-count">${pollData.count_b} votes (${Math.round(percents.percent_b)}%)</div>
                    </div>
                </div>

                <div class="poll-date">
                    ${formatDate(pollData.poll.created_at)}
                </div>
            </div>
        `;
    }

    function rotatePage() {
        // Fade out current cards
        const cards = gridContainer.querySelectorAll('.poll-card');
        cards.forEach(card => card.classList.add('fade-out'));

        // Wait for fade out animation
        setTimeout(() => {
            // Move to next page
            currentPage = (currentPage + 1) % totalPages;

            // Calculate which polls to show
            const startIdx = currentPage * POLLS_PER_PAGE;
            const endIdx = Math.min(startIdx + POLLS_PER_PAGE, allPolls.length);
            const pollsToShow = allPolls.slice(startIdx, endIdx);

            // Update grid with new polls
            gridContainer.innerHTML = pollsToShow.map((poll, idx) =>
                createPollCard(poll, startIdx + idx)
            ).join('');

            // Update page indicator
            currentPageEl.textContent = currentPage + 1;
        }, FADE_DURATION);
    }

    // Start rotation
    setInterval(rotatePage, ROTATION_INTERVAL);

    console.log(`Rotation enabled: ${allPolls.length} polls, ${totalPages} pages`);
})();
