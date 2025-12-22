# Deploy Frontend to Google Cloud

## Overview

The frontend (React + Vite SPA) can be deployed using two approaches:

- **Option 1: Firebase Hosting** (Recommended - simpler, cheaper, CDN included)
- **Option 2: Cloud Run** (Using Nginx container)

Unlike the backend, the frontend **does NOT require**:

- ❌ Cloud SQL (no database)
- ❌ Secret Manager (no sensitive credentials)
- ❌ Cloud Storage (static files in container/CDN)
- ❌ Service accounts with multiple IAM roles

---

## Option 1: Firebase Hosting (Recommended)

### Components

- Firebase Hosting (CDN-backed static hosting)
- (Optional) Cloud Build for CI/CD

### Prerequisites

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login to Firebase
firebase login
```

### Steps

#### 1. Set base environment variables

```bash
PROJECT_ID=$(gcloud config get-value core/project)
BACKEND_URL="https://comicchase-service-${PROJECT_ID}.REGION.run.app"
```

#### 2. Navigate to UI folder and build the app

```bash
cd ui

# Create production build
npm run build
```

#### 3. Initialize Firebase Hosting

```bash
# Initialize Firebase (run in ui/ folder)
firebase init hosting

# Select options:
# - Use existing project: [your-project-id]
# - Public directory: dist
# - Configure as single-page app: Yes
# - Set up automatic builds with GitHub: No (for now)
# - Overwrite index.html: No
```

#### 4. Configure environment variables for production

Create `ui/.env.production` file:

```bash
cat > .env.production << EOF
VITE_API_BASE_URL=${BACKEND_URL}
EOF
```

#### 5. Update firebase.json configuration

Edit `ui/firebase.json` to add rewrites for SPA routing and API proxy:

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
          "region": "REGION"
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

#### 6. Build and deploy

```bash
# Rebuild with production environment
npm run build

# Deploy to Firebase Hosting
firebase deploy --only hosting

# Output will show:
# ✔  Deploy complete!
# Hosting URL: https://your-project-id.web.app
```

#### 7. (Optional) Set up custom domain

```bash
# In Firebase Console or CLI
firebase hosting:channel:deploy production --expires 7d
```

### Updating the Frontend

```bash
cd ui

# Make your changes, then rebuild
npm run build

# Redeploy
firebase deploy --only hosting
```

### Cost Estimation

- **Firebase Hosting**: Free tier includes 10GB storage, 360MB/day bandwidth
- **Paid tier**: $0.026/GB storage, $0.15/GB bandwidth

---

## Option 2: Cloud Run (Nginx Container)

### Components

- Cloud Run
- Artifact Registry
- (Optional) Cloud Build for CI/CD

### Steps

#### 1. Enable Google Cloud APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com
```

#### 2. Set base environment variables

```bash
PROJECT_ID=$(gcloud config get-value core/project)
REGION=us-central1
BACKEND_URL="https://comicchase-service-${PROJECT_ID}.${REGION}.run.app"
```

#### 3. Set up Artifact Registry

Create a repository for the frontend container:

```bash
gcloud artifacts repositories create cloud-run-frontend-deploy \
    --repository-format docker \
    --location ${REGION}

ARTIFACT_REGISTRY=${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-frontend-deploy
```

#### 4. Update environment configuration

Create `ui/.env.production`:

```bash
cd ui
cat > .env.production << EOF
VITE_API_URL=${BACKEND_URL}
EOF
```

#### 5. Update nginx.conf for Cloud Run

Edit `ui/nginx.conf` to use environment variable for backend URL:

```nginx
server {
    listen 8080;  # Cloud Run uses port 8080
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Handle React Router (SPA routing)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 6. Update Dockerfile for Cloud Run

Ensure `ui/Dockerfile` exposes port 8080:

```dockerfile
# Frontend Dockerfile for ComicChase UI (React + Vite)

# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage with Nginx
FROM nginx:alpine AS runner

# Copy built files to nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Cloud Run uses PORT environment variable (default 8080)
ENV PORT=8080
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
```

#### 7. Build and push the container image

```bash
cd ui

# Build the container
gcloud builds submit --tag ${ARTIFACT_REGISTRY}/comicchase-frontend .

# Or build locally and push
docker build -t ${ARTIFACT_REGISTRY}/comicchase-frontend .
docker push ${ARTIFACT_REGISTRY}/comicchase-frontend
```

#### 8. Deploy to Cloud Run

```bash
gcloud run deploy comicchase-frontend \
    --region ${REGION} \
    --image ${ARTIFACT_REGISTRY}/comicchase-frontend \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --set-env-vars "VITE_API_URL=${BACKEND_URL}"
```

Output:

```bash
Service [comicchase-frontend] revision [comicchase-frontend-00001-abc] has been deployed
and is serving 100 percent of traffic.
Service URL: https://comicchase-frontend-xyz.REGION.run.app
```

#### 9. (Optional) Set up Cloud Build for automated deployment

Create `ui/cloudbuild-frontend.yaml`:

```yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - '${_REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-frontend-deploy/comicchase-frontend'
      - '.'
    dir: 'ui'

  # Push the container image to Artifact Registry
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - '${_REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-frontend-deploy/comicchase-frontend'

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'comicchase-frontend'
      - '--image'
      - '${_REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-frontend-deploy/comicchase-frontend'
      - '--region'
      - '${_REGION}'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--port'
      - '8080'

images:
  - '${_REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-frontend-deploy/comicchase-frontend'

substitutions:
  _REGION: us-central1

options:
  logging: CLOUD_LOGGING_ONLY
```

Deploy using Cloud Build:

```bash
gcloud builds submit --config ui/cloudbuild-frontend.yaml
```

### Updating the Frontend (Cloud Run)

```bash
# Option 1: Using Cloud Build (recommended)
gcloud builds submit --config ui/cloudbuild-frontend.yaml

# Option 2: Manual deployment
cd ui
gcloud builds submit --tag ${ARTIFACT_REGISTRY}/comicchase-frontend .
gcloud run deploy comicchase-frontend \
    --region ${REGION} \
    --image ${ARTIFACT_REGISTRY}/comicchase-frontend
```

### Cost Estimation (Cloud Run)

- **Cloud Run**: $0.00002400/vCPU-second, $0.00000250/GiB-second
- **Requests**: First 2 million free per month
- **Artifact Registry**: $0.10/GB storage

---

## Comparison: Firebase Hosting vs Cloud Run

| Feature | Firebase Hosting | Cloud Run |
|---------|-----------------|-----------|
| **Setup Complexity** | Simple | Moderate |
| **Cost** | Lower (generous free tier) | Higher (pay per request) |
| **CDN** | Built-in global CDN | Needs Cloud CDN setup |
| **SSL/HTTPS** | Automatic | Automatic |
| **Custom Domain** | Easy setup | Easy setup |
| **Deployment Speed** | Very fast | Fast |
| **Best For** | Static SPAs | When you need container control |

## Recommendation

✅ **Use Firebase Hosting** for the frontend because:

1. Simpler deployment process
2. Lower costs with generous free tier
3. Built-in global CDN
4. Perfect for React SPAs
5. Easier CI/CD setup

Use Cloud Run only if you need:

- Custom Nginx configurations
- Server-side logic in the container
- Integration with existing Cloud Run infrastructure
