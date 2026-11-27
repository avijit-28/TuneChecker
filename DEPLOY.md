# TuneChecker — All-Time Free Deployment Guide

This setup runs **100% free forever** with zero credit card required:
- **Backend**: **Hugging Face Spaces (Docker Space, 16 GB RAM Free)** running FastAPI + FFmpeg + Faster-Whisper + 2-Layer Voice Acoustics + Gemini LLM
- **Frontend**: **Vercel (Free Hobby Plan)** serving the React/Vite app and proxying `/api/*` requests to your HF Space

---

## Step 1: Deploy Backend on Hugging Face Spaces (Free 16 GB RAM)

1. Create a free account at https://huggingface.co and click **New Space**.
2. Set:
   - **Space name**: `tunechecker-api`
   - **License**: `mit`
   - **Select Space SDK**: **Docker** → **Blank**
   - **Space hardware**: **CPU basic · 2 vCPU · 16 GB (Free)**
3. Clone your new Space repo and copy the contents of `backend/` into it (or push `backend/` directly to the Space's git remote):
   ```bash
   git clone https://huggingface.co/spaces/<YOUR_HF_USERNAME>/tunechecker-api
   cp -r backend/* backend/.dockerignore tunechecker-api/
   cd tunechecker-api
   git add .
   git commit -m "Deploy TuneChecker backend"
   git push
   ```
4. In your Hugging Face Space → **Settings** → **Variables and secrets**, add a **New secret**:
   - Name: `GEMINI_API_KEY`
   - Value: `<your Google AI Studio Gemini API key>`
5. Wait ~3–5 minutes for the Docker build to finish. Once running, verify:
   `https://<YOUR_HF_USERNAME>-tunechecker-api.hf.space/api/v1/health`

---

## Step 2: Deploy Frontend on Vercel (Free)

1. Open `frontend/vercel.json` and replace `YOUR-HF-USERNAME-tunechecker-api.hf.space` with your actual Hugging Face Space URL:
   ```json
   {
     "rewrites": [
       {
         "source": "/api/(.*)",
         "destination": "https://<YOUR_HF_USERNAME>-tunechecker-api.hf.space/api/$1"
       },
       {
         "source": "/(.*)",
         "destination": "/index.html"
       }
     ]
   }
   ```
2. Push your repo to GitHub, then go to https://vercel.com/new:
   - Import your GitHub repository.
   - Set **Root Directory** to `frontend`.
   - **Framework Preset**: `Vite`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. Click **Deploy**. Your live app will be ready at `https://<your-app>.vercel.app`!

---

## Notes
- **Cold Start**: Hugging Face Free Spaces sleep after 48 hours of inactivity and wake up in ~15–20 seconds on the first request.
- **Persistence**: On Free HF Spaces, local SQLite (`data/app.db`) resets if the container rebuilds; for permanent history across rebuilds, you can optionally point `DATABASE_URL` to a free PostgreSQL database (e.g., Neon / Supabase).
