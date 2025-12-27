def format_poll_response(poll, session):
    """
    Format a poll object with vote counts into the standard API response format.

    Args:
        poll: Poll model instance
        session: Database session for querying vote counts

    Returns:
        dict: Formatted poll data with counts
    """
    counts = poll.get_vote_counts(session)

    return {
        "poll": {
            "id": poll.id,
            "question": poll.question,
            "answer_a": poll.answer_a,
            "answer_b": poll.answer_b,
            "count_a": counts["A"],
            "count_b": counts["B"]
        }
    }
