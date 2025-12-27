# Plan: Display Without Vote Counts

Add a `/display-no-votes` route that shows poll options without revealing vote counts or bar graphs. Useful for displaying choices to an audience without biasing their decisions.

---

## Step 1: Add display-no-votes route and template

**Description**

Add a new `/display-no-votes` route that renders the active poll's question and answer options without vote counts or proportion bars. Create a new template `display_no_votes.html` based on `display.html` but with vote-related elements removed.

**Tests**

```
describe display_no_votes_interface
  it_shows_active_poll_question_and_answers
  it_does_not_show_vote_counts
  it_does_not_show_vertical_bars
  it_shows_message_when_no_active_poll
```

**Implementation Notes**

1. Create `templates/display_no_votes.html`:
   - Copy from `display.html`
   - Remove the `<div class="vertical-bar">` elements
   - Remove the `<div class="vote-count">` elements
   - Keep Socket.IO and existing `display.js` (it already null-checks elements, so missing vote elements are harmless no-ops)

2. In `app/__init__.py`, add new route:
   ```python
   @app.route('/display-no-votes')
   def display_no_votes():
       session = get_session()
       active_poll = session.query(Poll).filter_by(is_active=True).first()
       return render_template('display_no_votes.html', poll=active_poll)
   ```

3. In `tests/test_display.py`, add new test class with fixtures reused from existing tests.

---

## Questions

None.
