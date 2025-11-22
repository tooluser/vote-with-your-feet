# Plans

Plans describe the means for building a system or change. They indicate changes to documentation, infrastructure, tests, and implementation.

They can also contain preambles that contextualize the change.
Confine next steps or questions to the end of the plan.
Notify me of ambiguities, make good assumptions, and ask questions as necessary to build a plan.

## Steps

Each step in a plan is either an infrastructure/documentation step or an implementation step.

### Infrastructure/Documentation Step

These steps describe changes that must be performed elsewhere, such as configurations at AWS or planned changes to documentation. They can be brief. They are not committed.

### Implementation Steps

Each implementation step should be a single, conceptually atomic change. Adding an API endpoint is one step, and adding a UI element that uses it is another.

Each implementation step has the following in this order:

- Title. This will be used as the commit message title
- Description. This should describe the changes in the step conceptually. It will be the body of the commit message. Be concise.
- Tests. Describe tests that will be modified or added in a nested pytest-describe fashion. If modifying existing tests, indicate what is new.

when the api is called
  with valid arguments
  with an invalid 'foo' argument
  **with an invalid 'bar' argument**
    **that is out of bounds**
    **that is the wrong type**

- Implementation Notes.
Explain what will be done in each step. Be concise and organized. Use pseudocode and file references. Another engineer should be able to implement these steps.

# Plan Execution

Each plan should have its own branch for execution.
All plans should be saved in ./plans/ as md files.

Follow the plan step by step.

When executing an implementation step, always write tests first, and make sure they run (and fail). Then build implementation to make the tests pass. Do not remove tests to make tests pass, and only modify tests if they are actually wrong.

When a step is complete and its tests pass, use 'git commit' to commit the changes, including the commit message and body from the step description.
