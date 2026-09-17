# Deploying to Google Cloud Run

Same GCP project as Earth Engine (`openfarm-analytics`), so the Cloud Run
service's own identity can be granted Earth Engine access directly —
no `EE_SERVICE_ACCOUNT_JSON` secret to manage in production.
`app/config.py` already tries Application Default Credentials first when
that env var isn't set, which is exactly what Cloud Run provides.

## One-time setup

```bash
# Install gcloud CLI if you don't have it: https://cloud.google.com/sdk/docs/install
gcloud auth login
gcloud config set project openfarm-analytics

gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

**Grant the runtime service account Earth Engine access** — by default
Cloud Run runs as `PROJECT_NUMBER-compute@developer.gserviceaccount.com`.
Find it and register it for EE access:

```bash
gcloud iam service-accounts list --filter="displayName:'Compute Engine default service account'"
```

Then add that email at
[signup.earthengine.google.com/#!/service_accounts](https://signup.earthengine.google.com/#!/service_accounts),
or via the Earth Engine project's Permissions panel
(code.earthengine.google.com → your project → Project settings → Permissions
→ add the service account as a Reader).

## Deploy

From the repo root (`gcloud run deploy --source .` builds the `Dockerfile`
via Cloud Build automatically — no local Docker needed):

```bash
cd /Users/nicolasjulia/googlebuildathonfarmers
gcloud run deploy sage-openfarm \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars EE_PROJECT_ID=openfarm-analytics
```

It'll print a `*.run.app` URL when done — that's your public HTTPS link.
Test it: `curl https://<your-url>/health` should return `{"status":"ok"}`,
and `https://<your-url>/field-locator` is the chat UI.

## Continuous deploy from GitHub (optional)

Instead of running `gcloud run deploy` by hand each time, connect the repo
so every push to `main` redeploys automatically:

```bash
gcloud run deploy sage-openfarm \
  --region us-central1 \
  --source . \
  --set-env-vars EE_PROJECT_ID=openfarm-analytics
# then in the Cloud Console: Cloud Run -> sage-openfarm -> "Set up Continuous Deployment"
# -> pick the GitHub repo (googlebuildathonfarmers) -> branch "main" -> Dockerfile build
```

That walks you through a one-time GitHub OAuth connection; after that,
`git push origin main` triggers a Cloud Build + redeploy automatically.

## Known limitation

`data/koppen/` (Köppen climate rasters) and `data/maxent_suitability.db`
are **not** included in the image (see `data/README.md` — they're large
binaries excluded from git). Without them, `get_climate_class()` silently
falls back to a default "Cfb" zone for every location, and MaxEnt
suitability returns empty. Plant health, irrigation, spectral indices, and
weather features are unaffected (they don't touch these files). To fix:
bake the files into the image (`COPY data/koppen ./data/koppen` in the
Dockerfile once they're present locally) or mount them from a GCS bucket
via `OPENFARM_DATA_DIR`.
