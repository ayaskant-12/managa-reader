# 📚 Manga Reading Website

An online platform for manga enthusiasts to read, bookmark, and track manga conveniently. It includes a user system, manga library, chapter reader, and an admin dashboard for managing content. Future enhancements include offline reading (PWA) and AI-powered recommendations.

## 🚀 Features
### 👤 User System
 
Register, login, logout.

Profile management (username, email, password).

Bookmark and favorites tracking.

Automatic reading history logging.

### 📖 Manga Library

Browse by genre, popularity, or release date.

Search by title, author, or keywords.

Detailed manga info page (cover, description, genres, author, chapters list).

### 📑 Chapter Reader

High-quality manga page rendering with lazy loading.

Navigation: next/previous chapter, jump to page.

Scrollable or paginated reading modes.

Dark mode toggle for readability.

### 💬 Community (Future)

Comments under chapters.

Ratings & reviews.

AI-based recommendations.

### 🛠️ Admin Dashboard

Upload manga & chapters (bulk uploads supported).

Manage metadata (title, author, genres, description).

User management & comment moderation.

## 🗄️ Database Design
### Entities & Attributes

Users → id, username, email, password_hash, role

Manga → id, title, author, description, genres, cover_url

Chapters → id, manga_id, chapter_number, title, release_date

Pages → id, chapter_id, page_number, image_url

Bookmarks → user_id, manga_id

Comments (optional) → id, user_id, chapter_id, text, created_at

### ⚙️ Tech Stack

Frontend: HTML, CSS, JavaScript

Backend: Python Flask

Database: PostgreSQL (pgAdmin4)

Image Storage: Local static folder (expandable to AWS S3, Cloud storage)

Deployment: Local → Cloud (Heroku, AWS, DigitalOcean)

## 🔒 Non-Functional Requirements

Performance: Optimized images (lazy loading, caching), indexed queries.

Scalability: Support for thousands of users & manga titles.

Security: Password hashing (bcrypt/werkzeug), JWT/session auth, role-based access.

Usability: Responsive design, dark mode, intuitive navigation.

Reliability: PostgreSQL constraints, ACID compliance, backups & failover support.

## 🌟 Future Enhancements

Offline Reading (PWA Support)

AI-powered Recommendations

Donation system to support creators

## 📌 Getting Started
### Prerequisites

Python 3.10+

PostgreSQL 14+

Node.js (optional for frontend tooling)

### Installation
Clone the repository
`git clone https://github.com/your-username/manga-reading-website.git`
`cd manga-reading-website`

Create a virtual environment
`python -m venv venv`
`source venv/bin/activate   # Linux/Mac`
`venv\Scripts\activate      # Windows`

Install dependencies
`pip install -r requirements.txt`

Setup database (PostgreSQL)
`psql -U postgres -c "CREATE DATABASE manga_db;"`

Run migrations (if using Flask-Migrate/Django migrations)
`flask db upgrade   # or python manage.py migrate`

Start the server
`flask run   # or python manage.py runserver`

Access the App

Open your browser → http://127.0.0.1:5000

## 👨‍💻 Authors

Developed as part of a Manga Reading Website project to provide a seamless manga reading experience.

## follow me

follow me on [github](https://github.com/ayaskant-12)

follow me on [instagram](https://www.instagram.com/ayaskant_dash_03/)
