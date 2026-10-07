# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

**Students** — University students and young professionals (18–30) in Algeria learning tech skills (programming, web development, data, etc.). French-speaking, some Arabic. Access the platform from desktop and mobile browsers.

**Instructors** — Independent Algerian educators who create and sell their own courses on the platform. They apply via tiered paid plans (Starter / Pro / Expert), upload payment proof (CCP/BaridiMob), and are activated after admin approval.

**Admin** — Platform operator who approves access requests, manages the course catalog, handles support tickets, and monitors instructor applications.

## Product Purpose

Hajime Learning is an e-learning platform purpose-built for the Algerian market. It solves the payment barrier that locks Algerian learners out of international platforms: courses are priced in Algerian Dinar (DA), and payment is handled through local methods (CCP/BaridiMob) with manual proof-of-payment validation — no international credit card required.

Success means Algerian students can buy, access, and complete online courses entirely within local financial infrastructure, and Algerian educators can monetize their knowledge without needing a foreign payment processor.

## Positioning

The only e-learning platform that pairs local Algerian payment rails (CCP/BaridiMob proof-of-payment) with a curated course catalog from Algerian instructors, in French, priced in DA. International competitors cannot replicate this because they do not integrate with Algeria's domestic payment ecosystem.

## Operating Context

- **Course structure**: Course → Modules → Lessons → Content Blocks (text/markdown, Bunny-hosted video, audio, downloadable files, timed quizzes).
- **Access flow (paid courses)**: Student submits payment proof image → Admin reviews and approves/rejects → Student gets course access.
- **Access flow (free courses)**: One-click enrollment, no payment required.
- **Instructor flow**: User picks a plan → Uploads payment proof → Admin approves → InstructorProfile created → Instructor can create courses up to their plan limits.
- **Coupons & activation codes**: Discount coupons with expiry and direct activation codes exist.
- **Support**: Per-course Q&A threads between students and admin/instructor, with open/resolved/closed statuses.
- **Progress tracking**: Per-lesson completion, per-course completion with PDF certificate generation (WeasyPrint).
- **Notifications**: Unified notification system for students (progress, support) and instructors (new questions, enrollments).
- **Landing page builder**: Drag-and-drop-ish section-based landing pages per course (hero, features, FAQ, testimonials, text+image, video).
- **Contact form**: General contact form with admin-defined reasons.

## Capabilities and Constraints

- **Stack**: Django 5.2, django-allauth (email-only auth, mandatory verification), django-cotton components, HTMX + Alpine.js, Tailwind CSS (standalone CLI via django-tailwind), WhiteNoise static serving, Celery + Redis for async tasks, WeasyPrint for PDFs, MarkdownX for content editing.
- **Database**: SQLite in dev, MySQL (PyMySQL) in production via cPanel.
- **Hosting**: cPanel shared hosting in production.
- **Language**: UI is in French. Code comments are in French.
- **Currency**: All prices in Algerian Dinar (DA), integer amounts.
- **No online payment gateway**: All payments are manual proof-of-payment flows.
- **Video hosting**: External (Bunny CDN), referenced by ID.
- **Tests**: pytest with 215+ tests covering models, views, signals, decorators, and management commands.

## Brand Commitments

- **Name**: Hajime Learning
- **Domain**: hajimelearning.com
- **Contact email**: contact@hajimelearning.com
- **Typography**: Inter (Google Fonts) — already in use.

- Visual identity: Defined in DESIGN.md.

## Evidence on Hand

- Working Django application with all core flows implemented.
- 215+ passing tests.
- Existing documentation in `/documentation/` covering components and feature guides.
- No live production screenshots, analytics data, or user research artifacts on hand.

## Product Principles

1. **Local-first**: Every design and product decision must work within Algeria's infrastructure — local payment, local currency, local language.
2. **Trust through transparency**: Manual payment review is a feature, not a workaround; the approval flow must feel reliable and professional, not bureaucratic.
3. **Instructor empowerment**: The platform exists to let Algerian educators monetize their expertise; friction in course creation is a direct threat to the catalog.
4. **Completion over consumption**: Progress tracking, certificates, and quizzes exist to prove learning happened — not just that content was accessed.
5. **Simplicity at scale**: The platform serves a young, mobile-heavy audience on shared hosting; every page must be fast and every flow must be self-explanatory.
