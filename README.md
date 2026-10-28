# YCKF Backend

YCKF Backend is a Flask-based REST API for the YCKF learning platform. It powers course management, student enrollment, authentication, donations, payments, certificate generation, and administrative workflows.

## Overview

This backend serves as the engine for a digital learning and donations platform where users can:

- Sign up and sign in
- Browse and enroll in courses
- Track course progress
- Make donations via Paystack
- Receive email communications
- Generate and verify completion certificates
- Manage categories, course content, and admin actions

## Tech Stack

- Python 3
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-JWT-Extended
- Flask-Mail
- PostgreSQL / SQLAlchemy-compatible database
- Paystack API integration
- ReportLab and QRCode for certificate generation
- Gunicorn for production serving

## Project Structure

```text
.
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── emails.py
│   ├── models.py
│   ├── routes.py
│   ├── yckf.py
│   └── helpers/
│       └── allowedfiles.py
├── .env.example
├── .gitignore
├── gunicorn.conf.py
├── migrate_sql_to_pg.py
├── procfile
├── render.yaml
├── requirements.txt
├── runtime.txt
└── README.md
```

## Features

### Authentication and user management
- User sign-up and sign-in
- JWT-based authentication
- Password reset flow via email
- Role-based user handling for students and admins

### Course platform
- Create, update, and delete courses
- Add lessons to courses
- View courses and lesson lists
- Track course enrollment and progress

### Donations and payments
- Donation session creation
- Paystack payment initialization
- Webhook-based payment verification
- Donation status tracking

### Certificates
- Generate completion certificates as PDFs
- QR code verification links
- Certificate validation endpoint

### Admin tooling
- Recent activity logs
- Audit logs
- Category management
- Enrollment control

## Environment Variables

A sample environment file is included at `.env.example`.

Copy it into a `.env` file and fill in the values:

```env
MAIL_USERNAME=
MAIL_PASSWORD=
DATABASE_URL=
SECRET_KEY=
JWT_SECRET_KEY=
PAYSTACK_SECRET_KEY=
PAYSTACK_PUBLIC_KEY=
```

Additional optional values used by the app include:

```env
CERT_SIGNING_KEY=
CERT_LOGO_PATH=
BASE_URL=https://yckf-app.vercel.app
```

## Local Setup

1. Clone the repository

```bash
git clone https://github.com/brcikaday/yckfBackend.git
cd yckfBackend
```

2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
# or
venv\Scripts\activate      # Windows
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Configure environment variables

Create a `.env` file using the sample values from `.env.example`.

5. Run database migrations (if using Flask-Migrate)

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

6. Start the app

```bash
flask run
```

Or with the application entry point:

```bash
python app/__init__.py
```

## Production Deployment

This repository includes deployment configuration files for hosting platforms:

- `render.yaml`
- `gunicorn.conf.py`
- `procfile`
- `runtime.txt`

This is set up for deployment on services like Render or similar WSGI-capable hosts.

## API Highlights

Common endpoints include:

- `POST /signup`
- `POST /signin`
- `POST /request_password_reset`
- `POST /reset_password`
- `GET /courses`
- `POST /create_course`
- `GET /enrolled`
- `POST /courses/<id>/enroll`
- `GET /categories`
- `GET /donations`
- `POST /donations/create_payment_session`
- `POST /payments/webhook`
- `POST /certificates/generate/<course_id>`
- `GET /certificates/verify/<cert_id>`

## Notes

- The app uses CORS configured for local frontend development (`http://localhost:5173`).
- Payment functionality is integrated with Paystack and relies on valid secret keys in the environment.
- Certificate signing and verification depend on `CERT_SIGNING_KEY`.

## License

This project does not currently declare a license in the repository. If you plan to distribute it publicly, consider adding an appropriate open-source license.

## Author

Developed for the YCKF platform.
