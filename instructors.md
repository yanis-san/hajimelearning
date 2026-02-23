The tests are getting interrupted by something. Let me try a different approach:

All 215 tests pass (172 existing + 42 new instructor tests + 1 previously added). Now rebuild Tailwind:

Everything is complete. Here's the summary:

Instructor system fully implemented:

Templates created: course_form.html — grouped form with 4 fieldsets (info, pedagogy, SEO/pricing, image/options), edit mode with thumbnail preview, plan limit indicator
Navbar updated: navbar.html — "🎓 Espace Instructeur" link for active instructors, "Devenir Instructeur" for everyone else (both desktop + mobile)
3 plans seeded: Starter (5000DA/1 course/70%), Pro (12000DA/3 courses/80%), Expert (25000DA/10 courses/90%) via seed_instructor_plans management command
42 new tests covering models, signal (approval → profile creation), decorators, all 6 views, form submission, course limits, edit isolation, and seed idempotency
215 total tests passing, zero regressions
Tailwind rebuilt
Claude Opus 4.6 • 3x