# Deploy to Google Cloud Run

## Components

- Cloud Run
- Cloud SQL
- Artifact Registry
- Cloud Storage
- Secret Manager
- Cloud Build

## Steps

### Enable the Cloud APIs

```bash
gcloud services enable \
  run.googleapis.com \
  sql-component.googleapis.com \
  sqladmin.googleapis.com \
  compute.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com
```

### Prepare the environment

Clone the app:

```bash
git clone https://github.com/atwolin/ComicChase.git
```

### Set base environment variables

```bash
PROJECT_ID=$(gcloud config get-value core/project)
REGION=us-central1
```

### Create a service account

1. Create a service account (name is `cloudrun-serviceaccount`):

```bash
gcloud iam service-accounts create cloudrun-serviceaccount
```

2. Save the account:

```bash
SERVICE_ACCOUNT=$(gcloud iam service-accounts list \
    --filter cloudrun-serviceaccount --format "value(email)")
```

### Create a PostgreSQL instance on Cloud SQL

1. Create the PostgreSQL instance:

```bash
INSTANCE_NAME=comic-instance
gcloud sql instances create ${INSTANCE_NAME} \
    --project ${PROJECT_ID} \
    --database-version POSTGRES_16 \
    --tier db-g1-small \
    --region ${REGION} \
    --edition ENTERPRISE
```

2. Create a database:

```bash
DATABASE_NAME=dj-database
gcloud sql databases create ${DATABASE_NAME} \
    --instance ${INSTANCE_NAME}
```

3. Create a database user:

```bash
DATABASE_USERNAME=dj-user
DATABASE_PASSWORD=$(openssl rand -base64 24)
gcloud sql users create ${DATABASE_USERNAME} \
    --instance ${INSTANCE_NAME} \
    --password ${DATABASE_PASSWORD}
```

### Set up Artifact Registry

1. Create a repository to store the container image (repo name `cloud-run-source-deploy`):

```bash
gcloud artifacts repositories create cloud-run-source-deploy \
    --repository-format docker \
    --location ${REGION}
```

2. Save the registry name:

```bash
ARTIFACT_REGISTRY=${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy
```

### Set up a Cloud Storage bucket

1. Create a Cloud Storage bucket to store static assets and user-uploaded media:

```bash
GS_BUCKET_NAME=${PROJECT_ID}-media
gcloud storage buckets create gs://${GS_BUCKET_NAME} --location=${REGION}
```

### Store secret values in Secret Manager

1. Add values for the database connection string, media bucket, and a new `SECRET_KEY` value:

```bash
echo DATABASE_URL=\"postgres://${DATABASE_USERNAME}:${DATABASE_PASSWORD}@//cloudsql/${PROJECT_ID}:${REGION}:${INSTANCE_NAME}/${DATABASE_NAME}\" > .env
echo GS_BUCKET_NAME=\"${GS_BUCKET_NAME}\" >> .env
echo SECRET_KEY=$(cat /dev/urandom | LC_ALL=C tr -dc '[:alpha:]'| fold -w 50 | head -n1) >> .env
echo DEBUG=False >> .env
```

For SECRET_KEY generation, alternately use cryptographically secure methods:
```bash
echo SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())") >> .env
```
or
```bash
echo SECRET_KEY=$(openssl rand -base64 32) >> .env
```

2. Store the secret (name is `application_settings`) in Secret Manager:

```bash
SECRET_NAME=application_settings
gcloud secrets create ${SECRET_NAME} --data-file .env
```

3. Delete local file to prevent local setting overrides:

```bash
rm .env
```

4. Create secret for Django's admin password:

```bash
SUPERUSER_SECRET_NAME=superuser_password
echo -n "$(cat /dev/urandom | LC_ALL=C tr -dc '[:alpha:]'| fold -w 30 | head -n1)" | gcloud secrets create ${SUPERUSER_SECRET_NAME} --data-file -
```

### Setting minimum permissions

1. Assign the service account to the service:

```bash
# Cloud SQL Client
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member serviceAccount:${SERVICE_ACCOUNT} \
    --role roles/cloudsql.client

# Storage Admin, on the media bucket
gcloud storage buckets add-iam-policy-binding gs://${GS_BUCKET_NAME} \
    --member=serviceAccount:${SERVICE_ACCOUNT} \
    --role=roles/storage.objectAdmin

# Secret Accessor, on the Django settings secret.
gcloud secrets add-iam-policy-binding ${SECRET_NAME} \
    --member serviceAccount:${SERVICE_ACCOUNT} \
    --role roles/secretmanager.secretAccessor

# Secret Accessor, on the Django super user password.
gcloud secrets add-iam-policy-binding ${SUPERUSER_SECRET_NAME} \
    --member serviceAccount:${SERVICE_ACCOUNT} \
    --role roles/secretmanager.secretAccessor
```

> Confirm the secret has been created by listing the secrets:
>
> ```bash
> gcloud secrets versions list ${SECRET_NAME}
> ```

### Deploy the app to Cloud Run

1. Use Cloud Build to build the image using `cloudmigrate.yaml`:

```bash
gcloud builds submit --config cloudmigrate.yaml \
    --substitutions _INSTANCE_NAME=${INSTANCE_NAME},_REGION=${REGION}
```

2. (Alternative) If you prefer to deploy manually for the first time without using `cloudmigrate.yaml`,
   you can set the service region, base image, and connected Cloud SQL instance manually:

```bash
gcloud run deploy comicchase-service \
    --region ${REGION} \
    --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/comicchase-service \
    --add-cloudsql-instances ${PROJECT_ID}:${REGION}:${INSTANCE_NAME} \
    --service-account ${SERVICE_ACCOUNT} \
    --allow-unauthenticated
```

> Successful output:
>
> ```bash
> Service [comicchase-service] revision [comicchase-service-00001-tug] has been deployed
> and is serving 100 percent of traffic.
> Service URL: https://comicchase-service-${PROJECT_ID}.REGION.run.app
> ```

3. Update the service to the service URLs an an environment variable:

```bash
CLOUDRUN_SERVICE_URLS=$(gcloud run services describe comicchase-service \
    --region ${REGION}  \
    --format "value(metadata.annotations[\"run.googleapis.com/urls\"])" | tr -d '"[]')

gcloud run services update comicchase-service \
    --region ${REGION} \
    --update-env-vars "^##^CLOUDRUN_SERVICE_URLS=${CLOUDRUN_SERVICE_URLS}"
```

> To retrieve the superuser password from Secret Manager:
>
> ```bash
> gcloud secrets versions access latest --secret superuser_password && echo ""
> ```

### Updating the application

1. Run the Cloud Build script, including build, migration, and deployment:

```bash
gcloud builds submit --config cloudmigrate.yaml \
    --substitutions _INSTANCE_NAME=${INSTANCE_NAME},_REGION=${REGION}
```

2. Only deploy the service, without build and migration:

```bash
gcloud run deploy comicchase-service \
    --region ${REGION} \
    --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/comicchase-service
```
