# Deployment Checklist: Backend (Cloud Run) + Frontend (Firebase Hosting)

This guide provides the exact order of operations for deploying ComicChase with Firebase Hosting for frontend and Cloud Run for backend.

---

## 📋 Pre-Deployment Checklist

- [ ] Google Cloud Project created
- [ ] Firebase project linked to Google Cloud project
- [ ] Firebase CLI installed (`npm install -g firebase-tools`)
- [ ] Google Cloud SDK installed and configured
- [ ] Backend code tested locally
- [ ] Frontend code tested locally
- [ ] Git repository up to date

---

## 🚀 Deployment Order

### **Phase 1: Deploy Backend First** (Get Cloud Run URL)

#### Step 1.1: Prepare Backend CORS Settings (Temporary)

**Location:** `app/src/config/settings/production.py` or `base.py`

```python
# Temporarily allow all origins for initial deployment
# We'll restrict this after getting Firebase URL
CORS_ALLOW_ALL_ORIGINS = True  # TEMPORARY - will change in Phase 3

ALLOWED_HOSTS = [
    '*',  # TEMPORARY - will restrict in Phase 3
]

CSRF_TRUSTED_ORIGINS = [
    'https://*.run.app',  # Allow all Cloud Run domains for now
]
```

**Files to modify:**

- [ ] `app/src/config/settings/base.py` (or `production.py`)

**Commit changes:**

```bash
git add app/src/config/settings/
git commit -m "feat: add temporary CORS settings for deployment"
```

---

#### Step 1.2: Deploy Backend to Cloud Run

**Follow:** `cloud-backend.md`

**Key commands:**

```bash
# Set environment variables
PROJECT_ID=$(gcloud config get-value core/project)
REGION=us-central1

# Run through all backend deployment steps from cloud-backend.md
# (Enable APIs, create Cloud SQL, Artifact Registry, etc.)

# Deploy backend
gcloud builds submit --config cloudmigrate.yaml \
    --substitutions _INSTANCE_NAME=${INSTANCE_NAME},_REGION=${REGION}
```

**Expected output:**

```
Service [comicchase-service] has been deployed
Service URL: https://comicchase-service-abc123xyz.us-central1.run.app
```

- [ ] Backend deployed successfully
- [ ] **COPY THE CLOUD RUN URL** - you'll need it for frontend configuration

---

#### Step 1.3: Save Backend URL

**Save this information:**

```bash
# Save to a file for easy reference
BACKEND_URL=$(gcloud run services describe comicchase-service \
    --region ${REGION} \
    --format "value(status.url)")

echo "Backend URL: ${BACKEND_URL}"
# Output: https://comicchase-service-abc123xyz.us-central1.run.app

# Save it
echo "BACKEND_URL=${BACKEND_URL}" > deployment-urls.txt
```

- [ ] Backend URL saved to `deployment-urls.txt`

---

#### Step 1.4: Test Backend API

```bash
# Test health endpoint
curl ${BACKEND_URL}/api/health

# Test admin (should redirect to login)
curl -I ${BACKEND_URL}/admin/

# Expected: 200 OK or 302 redirect
```

- [ ] Backend API responding
- [ ] Admin panel accessible

---

### **Phase 2: Configure and Deploy Frontend**

#### Step 2.1: Initialize Firebase

```bash
cd ui

# Login to Firebase
firebase login

# Initialize Firebase
firebase init hosting
```

**Selections:**

- Use existing project: `[your-project-id]`
- Public directory: `dist`
- Configure as single-page app: `Yes`
- Set up automatic builds: `No` (for now)
- Overwrite index.html: `No`

- [ ] Firebase initialized in `ui/` folder
- [ ] `firebase.json` created

---

#### Step 2.2: Configure Firebase Hosting

**Location:** `ui/firebase.json`

**Option A: Direct API Calls (Recommended)**

```json
{
  "hosting": {
    "public": "dist",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=31536000, immutable"
          }
        ]
      }
    ]
  }
}
```

**Option B: Firebase as Proxy (Alternative)**

```json
{
  "hosting": {
    "public": "dist",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "/api/**",
        "run": {
          "serviceId": "comicchase-service",
          "region": "us-central1"
        }
      },
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=31536000, immutable"
          }
        ]
      }
    ]
  }
}
```

- [ ] `firebase.json` configured
- [ ] Choose Option A or B and note your choice

---

#### Step 2.3: Create Production Environment File

**Location:** `ui/.env.production`

**If using Option A (Direct calls):**

```bash
cd ui
cat > .env.production << EOF
VITE_API_URL=https://comicchase-service-abc123xyz.us-central1.run.app
EOF
```

**If using Option B (Firebase proxy):**

```bash
cd ui
cat > .env.production << EOF
VITE_API_URL=/api
EOF
```

- [ ] `ui/.env.production` created with correct backend URL

---

#### Step 2.4: Update Frontend API Client

**Location:** `ui/src/api/client.ts` (or wherever you configure API calls)

**Create or update the API client:**

```typescript
// ui/src/api/client.ts
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // If using cookies/sessions
});

// Request interceptor for auth tokens
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if exists
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      console.error('Unauthorized - redirect to login');
    }
    return Promise.reject(error);
  }
);
```

**Update all API calls to use the client:**

```typescript
// Example: ui/src/services/comicService.ts
import { apiClient } from '../api/client';

export const getComics = async () => {
  const response = await apiClient.get('/api/comics/');
  return response.data;
};
```

- [ ] API client configured to use `VITE_API_URL`
- [ ] All API calls updated to use the centralized client

---

#### Step 2.5: Add .gitignore Entries

**Location:** `ui/.gitignore`

```gitignore
# Firebase
.firebase/
firebase-debug.log
firestore-debug.log
ui-debug.log

# Environment files (local only)
.env.local

# Firebase cache
.firebase/
```

- [ ] `.gitignore` updated

---

#### Step 2.6: Build Frontend

```bash
cd ui

# Install dependencies if needed
npm install

# Build for production
npm run build

# Verify build output
ls -la dist/
```

**Expected output:**

```
dist/
├── assets/
│   ├── index-abc123.js
│   └── index-def456.css
├── index.html
└── ...
```

- [ ] Frontend built successfully
- [ ] `dist/` folder contains built files

---

#### Step 2.7: Deploy Frontend to Firebase

```bash
cd ui

# Deploy to Firebase Hosting
firebase deploy --only hosting

# Wait for deployment...
```

**Expected output:**

```
✔  Deploy complete!

Project Console: https://console.firebase.google.com/project/your-project-id/overview
Hosting URL: https://your-project-id.web.app
```

- [ ] Frontend deployed successfully
- [ ] **COPY THE FIREBASE URL** - you'll need it for backend CORS configuration

---

#### Step 2.8: Save Frontend URL

```bash
# Save Firebase URL
echo "FRONTEND_URL=https://your-project-id.web.app" >> deployment-urls.txt

# View all URLs
cat deployment-urls.txt
```

- [ ] Frontend URL saved to `deployment-urls.txt`

---

### **Phase 3: Update Backend CORS (Restrict Access)**

#### Step 3.1: Update Backend Settings with Real URLs

**Location:** `app/src/config/settings/production.py` (or `base.py`)

**Replace temporary CORS settings:**

```python
# Remove CORS_ALLOW_ALL_ORIGINS = True

# Add specific origins
CORS_ALLOWED_ORIGINS = [
    'https://your-project-id.web.app',
    'https://your-project-id.firebaseapp.com',
    # Add custom domain if you have one
    # 'https://comicchase.com',
]

# Restrict allowed hosts
ALLOWED_HOSTS = [
    'comicchase-service-abc123xyz.us-central1.run.app',
    'your-project-id.web.app',
]

# Update CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    'https://your-project-id.web.app',
    'https://your-project-id.firebaseapp.com',
    'https://comicchase-service-abc123xyz.us-central1.run.app',
]

# Ensure corsheaders is configured
INSTALLED_APPS = [
    # ...
    'corsheaders',
    # ...
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Should be at top
    'django.middleware.security.SecurityMiddleware',
    # ...
]

# If using session/cookie authentication
SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = True
```

**Files to modify:**

- [ ] `app/src/config/settings/base.py` (or `production.py`)

**Commit changes:**

```bash
git add app/src/config/settings/
git commit -m "feat: configure CORS with Firebase Hosting URLs"
git push
```

---

#### Step 3.2: Redeploy Backend with Updated CORS

```bash
# Redeploy backend
gcloud builds submit --config cloudmigrate.yaml \
    --substitutions _INSTANCE_NAME=${INSTANCE_NAME},_REGION=${REGION}
```

- [ ] Backend redeployed with restricted CORS

---

### **Phase 4: Verification and Testing**

#### Step 4.1: Test Cross-Origin Requests

**Open frontend in browser:**

```bash
# Get frontend URL
cat deployment-urls.txt

# Open in browser
# https://your-project-id.web.app
```

**Check browser console:**

- [ ] No CORS errors in console
- [ ] API requests succeed
- [ ] Data loads correctly

---

#### Step 4.2: Test API Endpoints

**In browser dev tools console:**

```javascript
// Test API call
fetch('https://comicchase-service-abc123xyz.us-central1.run.app/api/comics/')
  .then(r => r.json())
  .then(console.log)

// Should return data, not CORS error
```

- [ ] API calls work from frontend
- [ ] Data returned successfully

---

#### Step 4.3: Test Authentication (if applicable)

**If using authentication:**

- [ ] Login works
- [ ] Tokens/cookies set correctly
- [ ] Protected routes work
- [ ] Logout works

---

#### Step 4.4: Test Different Pages/Routes

**Navigate through the app:**

- [ ] Home page loads
- [ ] All routes work
- [ ] SPA routing works (refresh on sub-routes)
- [ ] Images/assets load
- [ ] API data displays

---

#### Step 4.5: Test Mobile/Responsive

**Check on different devices:**

- [ ] Desktop browser
- [ ] Mobile browser
- [ ] Different browsers (Chrome, Firefox, Safari)

---

### **Phase 5: Post-Deployment Tasks**

#### Step 5.1: Set Up Custom Domain (Optional)

**For Firebase:**

```bash
firebase hosting:channel:deploy production

# Follow Firebase Console to add custom domain
# https://console.firebase.google.com/project/your-project-id/hosting
```

**Update CORS settings if using custom domain:**

```python
CORS_ALLOWED_ORIGINS = [
    'https://your-project-id.web.app',
    'https://comicchase.com',  # Custom domain
]
```

- [ ] Custom domain configured (if needed)
- [ ] CORS updated for custom domain

---

#### Step 5.2: Set Up Monitoring

**Cloud Run (Backend):**

```bash
# View logs
gcloud run services logs read comicchase-service --region ${REGION} --limit 50

# Set up alerts in Cloud Console
# https://console.cloud.google.com/run
```

**Firebase (Frontend):**

```bash
# View hosting stats
firebase hosting:channel:list

# Check Firebase Console
# https://console.firebase.google.com/project/your-project-id/hosting
```

- [ ] Monitoring set up for backend
- [ ] Monitoring set up for frontend

---

#### Step 5.3: Document Deployment URLs

**Create or update:** `README.md`

```markdown
## Production URLs

- **Frontend:** https://your-project-id.web.app
- **Backend API:** https://comicchase-service-abc123xyz.us-central1.run.app
- **Admin Panel:** https://comicchase-service-abc123xyz.us-central1.run.app/admin/

## Deployment

- Frontend: Firebase Hosting (See `cloud-frontend.md`)
- Backend: Cloud Run (See `cloud-backend.md`)
- Full guide: `deployment-checklist.md`
```

- [ ] README.md updated with production URLs

---

#### Step 5.4: Clean Up Temporary Files

```bash
# Remove temporary deployment URLs file (or commit it)
# rm deployment-urls.txt

# Or add to .gitignore
echo "deployment-urls.txt" >> .gitignore
```

- [ ] Cleanup completed

---

## 🔄 Future Updates

### Update Frontend Only

```bash
cd ui
npm run build
firebase deploy --only hosting
```

### Update Backend Only

```bash
gcloud builds submit --config cloudmigrate.yaml \
    --substitutions _INSTANCE_NAME=${INSTANCE_NAME},_REGION=${REGION}
```

### Update Both

1. Deploy backend first (follow backend update steps)
2. Update frontend `.env.production` if backend URL changed
3. Deploy frontend

---

## 🚨 Troubleshooting

### CORS Errors

**Problem:** `Access to fetch at '...' has been blocked by CORS policy`

**Solutions:**

1. Check `CORS_ALLOWED_ORIGINS` includes Firebase URL
2. Verify `corsheaders` is in `INSTALLED_APPS`
3. Ensure `CorsMiddleware` is at top of `MIDDLEWARE`
4. Check backend logs: `gcloud run services logs read comicchase-service`

### API Calls Fail

**Problem:** 404 or 500 errors on API calls

**Solutions:**

1. Verify `VITE_API_URL` in `.env.production`
2. Check backend is deployed and running
3. Test backend URL directly in browser
4. Check Firebase proxy configuration (if using Option B)

### Frontend Shows Old Version

**Problem:** Changes not visible after deployment

**Solutions:**

1. Hard refresh browser (Ctrl+Shift+R)
2. Clear browser cache
3. Check Firebase deployment was successful
4. Verify build includes latest changes: `npm run build`

### Session/Cookie Issues

**Problem:** Authentication not persisting

**Solutions:**

1. Check `SESSION_COOKIE_SAMESITE = 'None'`
2. Verify `SESSION_COOKIE_SECURE = True`
3. Ensure `withCredentials: true` in frontend
4. Check HTTPS is used (not HTTP)

---

## ✅ Final Checklist

- [ ] Backend deployed to Cloud Run
- [ ] Frontend deployed to Firebase Hosting
- [ ] CORS configured correctly
- [ ] API calls working
- [ ] Authentication working (if applicable)
- [ ] All pages/routes tested
- [ ] Mobile/responsive tested
- [ ] Monitoring set up
- [ ] Documentation updated
- [ ] Custom domain configured (optional)

---

## 📚 Reference Documents

- **Backend Deployment:** `cloud-backend.md`
- **Frontend Deployment:** `cloud-frontend.md`
- **This Checklist:** `deployment-checklist.md`

---

**🎉 Deployment Complete!**

Your ComicChase application is now live:

- Frontend: `https://your-project-id.web.app`
- Backend: `https://comicchase-service-xyz.run.app`
