# Deployment Guide for Cross-P (Px)

This guide provides step-by-step instructions to deploy **Cross-P (Px)**, including both local development and production setup.

---

## 1. Prerequisites

* **Python 3.10–3.12**
* **pip** and **virtualenv**
* **Git**
* **Optional:** Redis server for caching/rate limiting
* **NewsAPI Key** (for live market news)

---

## 2. Clone the Repository

```bash
git clone https://github.com/your-username/Cross-P-Px.git
cd Cross-P-Px
```

---

## 3. Setup Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

Upgrade pip and install build tools:

```bash
pip install --upgrade pip setuptools wheel
```

---

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 5. Environment Variables

Set your NewsAPI key:

```bash
export NEWS_API_KEY="your_newsapi_key_here"
```

> Optional: Add this to your shell profile (`~/.zshrc` or `~/.bashrc`) for persistence.

---

## 6. Run Locally

### Start FastAPI Backend (with WebSocket server)

```bash
uvicorn main:app --reload
```

* Runs backend on `http://localhost:8000`
* WebSocket live price updates available at `ws://localhost:8000/ws/prices`

### Start Streamlit Frontend

```bash
streamlit run main.py
```

* Access the app at `http://localhost:8501`
* The frontend communicates with FastAPI endpoints automatically.

---

## 7. Production Deployment

### Using Gunicorn + Uvicorn Workers

```bash
gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Optional: Serve Streamlit Frontend Separately

* Use **NGINX** or **Caddy** as a reverse proxy to serve Streamlit and FastAPI on standard ports.

### Redis Setup (Optional for rate-limiting)

```bash
brew install redis
redis-server
```

* Configure your app to connect to Redis via environment variable.

---

## 8. Notes

* Ensure Python version compatibility to avoid Streamlit segmentation faults on macOS.
* Always install pinned dependencies from `requirements.txt`.
* For production, consider **Dockerizing** the app for easier deployment.

---

## 9. Docker Deployment (Optional)

1. Create a `Dockerfile` with Python 3.11 base image.
2. Copy project files and install dependencies.
3. Expose ports 8000 (FastAPI) and 8501 (Streamlit).
4. Use Docker Compose to link Redis if needed.

---

This completes the deployment guide for **Cross-P (Px)**. Your platform should now be fully operational locally or in a production environment.
