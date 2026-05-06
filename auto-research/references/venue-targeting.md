# Venue Targeting

Stage 0 exists to prevent the pipeline from inventing "generic top-tier paper" goals that fit no real venue.

## Mandatory Stage 0 questions

Ask these before ideation if the user did not already answer them:

1. What conference or journal are we targeting?
2. Is there a specific track, workshop, or special call?
3. Is the goal novelty-first, systems-first, benchmark-first, or theory-first?

## What Stage 0 must fetch

Only use official venue sources when available.

1. Official LaTeX or author kit.
2. Call for papers / aims and scope / track description.
3. Submission limits and formatting constraints.
4. Review criteria if the venue publishes them.

Write the fetched artifacts under `runs/<run_id>/stage0_setup/`.

## Required files

- `venue_profile.yaml`: normalized summary of venue name, track, scope, deadlines, page limits, and review criteria.
- `cfp.md`: the raw or summarized call text with source URLs logged.
- `submission_requirements.md`: page limits, anonymization, artifact policy, checklist requirements, etc.
- `latex_source.json`: where the template came from, fetch date, and fallback notes.
- `latex_template/`: downloaded official template files or a logged fallback.

## Output expectations

The setup hand-off to Stage 1 must answer:

- what kinds of contributions this venue tends to reward,
- what kinds of claims are risky or unconvincing for this venue,
- what packaging constraints will matter later in writing.

## Fallbacks

If the official template cannot be fetched:

1. log the failed source attempts,
2. use the closest built-in fallback template,
3. mark the result as a temporary fallback in `latex_source.json`,
4. tell the user before Stage 4 starts.
