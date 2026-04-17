# User Profile Page Design

Date: 2026-04-17

## Goal

Add a dedicated user profile page with basic personal information fields and field-level visibility controls, replacing the current lightweight profile summary on the home page.

## Problem

The current frontend only shows minimal user information on the home page.

Current issues:

- there is no dedicated profile page
- profile information is too limited for a real personal detail view
- users cannot manage what personal information is shown to others
- the home page is mixing navigation and profile display responsibilities

This is a product gap because user identity is relevant to circles, teams, invitations, and matching, but the system currently does not provide a proper profile surface.

## Product Decision

Introduce a dedicated profile module with:

- a dedicated profile page
- editable basic personal information
- field-level visibility toggles
- a public profile read path for viewing another user's visible information

Default visibility rule:

- profile fields are public by default
- each field can be hidden individually by the user

Version-one fields:

- `full_name`
- `gender`
- `birthday`
- `email`
- `bio`

This change will not cover:

- avatar upload
- social links
- phone number
- location
- major or academic metadata
- profile analytics

## Scope

This change will cover:

- dedicated profile data storage
- dedicated profile frontend page
- current-user profile read and update APIs
- public profile read API with field filtering
- home-page navigation update
- seed-data and test-sample updates for profile information

This change will not cover:

- profile search
- profile recommendation logic
- using profile fields directly in matching
- profile media management

## Architecture

### Dedicated profile model

Use a dedicated `UserProfile` model instead of expanding the existing `User` table with all profile fields.

Recommended rationale:

- `User` should remain focused on identity and authentication
- profile information has a different lifecycle and display behavior
- visibility toggles belong with profile presentation, not account credentials
- future profile extension remains cleaner with one dedicated model

Recommended storage pattern:

- `User` continues to store account identity such as `username`, `email`, and `hashed_password`
- `UserProfile` stores profile details and visibility toggles

### One page, two views

Use one dedicated profile page but support two display modes:

- self view
- public read-only view

Self view:

- editable
- shows all fields
- shows all visibility toggles

Public view:

- read-only
- only shows fields that are marked visible

This keeps the mental model simple: one profile area, different behavior depending on whose profile is being opened.

## Data Model Design

### Recommended model

Add a `UserProfile` table with a one-to-one relationship to `User`.

Recommended fields:

- `id`
- `user_id`
- `full_name`
- `gender`
- `birthday`
- `bio`
- `show_full_name`
- `show_gender`
- `show_birthday`
- `show_email`
- `show_bio`

### Field ownership

Field storage should follow this split:

- `email` remains on `User`
- `full_name`, `gender`, `birthday`, and `bio` belong to `UserProfile`
- all `show_*` toggles belong to `UserProfile`

This allows the API to decide whether to expose `email` publicly without moving the real account field out of `User`.

### Defaults

Default visibility values should all be `True`:

- `show_full_name = True`
- `show_gender = True`
- `show_birthday = True`
- `show_email = True`
- `show_bio = True`

This matches the agreed product rule that profile data is public by default unless the user hides individual fields.

### Field constraints

Recommended version-one validation:

- `full_name`
  - optional
  - short plain text
- `gender`
  - restricted enum-like value
  - recommended options:
    - `Male`
    - `Female`
    - `Other`
    - `Prefer not to say`
- `birthday`
  - stored as `date`
- `bio`
  - optional short text
  - recommended maximum length: 200 to 300 characters

## API Design

### Current-user profile read

Add:

- `GET /profile/me`

Purpose:

- return the authenticated user's full editable profile
- include all stored fields
- include all visibility toggles
- include account email

This endpoint must always return the full truth for the current user, regardless of public visibility settings.

### Current-user profile update

Add:

- `PUT /profile/me`

Allowed updates:

- `full_name`
- `gender`
- `birthday`
- `bio`
- all `show_*` flags

This endpoint should not allow changing core account fields such as `username` or authentication password.

### Public profile read

Add:

- `GET /users/{user_id}/profile`

Purpose:

- return another user's public profile view
- expose only fields allowed by visibility flags

Recommended response behavior:

- visible fields are returned normally
- hidden fields are omitted or returned as `null`
- account email is returned only when `show_email = True`

## Read and Display Rules

### Self view rules

When a user reads `GET /profile/me`:

- all fields are visible
- all visibility toggles are visible
- all editable values are returned exactly as stored

### Public view rules

When any user reads `GET /users/{user_id}/profile`:

- `username` may always be shown because it is already a public-facing identity in the app
- profile fields are shown only when the corresponding `show_*` toggle is `True`
- hidden values must not be leaked in the API response

### Home page rules

The home page should no longer act as the main profile display area.

Instead:

- keep a short summary if useful
- add a clear navigation entry to the profile page
- remove the expectation that the home page is where profile management happens

## Frontend Page Design

### Dedicated page

Add a dedicated frontend page such as:

- `frontend/pages/profile.py`

Recommended page sections for self view:

- profile overview
- editable basic information
- visibility settings
- save action area

Recommended page sections for public read view:

- username and visible identity summary
- visible personal details
- visible bio

### UX intent

The profile page should feel simple and utility-first.

It does not need to become a social-media-style personal page.

Its purpose is:

- basic identity presentation
- editable personal details
- clear visibility control

## Missing Profile Behavior

To stay compatible with existing users and test data, the system should tolerate users without a stored `UserProfile` row.

Recommended behavior:

- if a profile row does not exist, reads should behave as if the user has an empty profile plus default visibility settings
- the first profile update should create the row automatically

This avoids migration friction for existing records and keeps API behavior simple.

## Error Handling

Recommended API behavior:

- unauthenticated access to `/profile/me` or `PUT /profile/me` -> `401` or the existing auth failure pattern
- unknown user id on `/users/{user_id}/profile` -> `404`
- invalid `birthday` format -> `400`
- invalid `gender` value -> `400`
- overlong `bio` -> `400`

The public profile API must never expose hidden fields due to validation or serialization mistakes.

## Seed Data and Test Sample Updates

This change should explicitly include updates to seed data and related tests.

### Seed updates

Update `scripts/seed_data.py` so demo and stress data include realistic profile values for seeded users:

- `full_name`
- `gender`
- `birthday`
- `bio`
- default `show_*` values

Recommended seed strategy:

- most users keep default public visibility
- a small number of seed users should hide selected fields to exercise privacy-display behavior

### Test updates

Update seed-related tests and any test fixtures that assume user identity data is limited to username and email.

Relevant seed-focused tests include:

- `tests/test_seed_data.py`
- `tests/test_seed_integration.py`
- `tests/test_seed_consistency.py`

Other API and frontend tests may also need updates if they render or assert user details.

## Testing Strategy

### Model and API tests

Add tests for:

- reading a default empty profile
- creating or updating a profile through `PUT /profile/me`
- reading your own full profile
- reading another user's filtered public profile
- hidden email not being exposed publicly
- default visibility being public

### Frontend tests

Add tests for:

- dedicated profile page rendering
- edit form initialization
- visibility-toggle handling
- home page linking to the profile page

### Regression tests

Add tests for:

- existing users without `UserProfile` rows
- privacy filtering not leaking hidden values
- seed data staying internally consistent

## Recommended Implementation Order

1. Add `UserProfile` model and persistence support
2. Add profile read and update API models
3. Implement `/profile/me`
4. Implement `/users/{user_id}/profile`
5. Add the dedicated frontend profile page
6. Simplify the home page profile area into a navigation entry
7. Update seed data and related tests
8. Add regression coverage for public field filtering
