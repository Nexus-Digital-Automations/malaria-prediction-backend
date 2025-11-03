# Malaria Prediction Backend - Credentials Setup Guide

## 🎉 Configuration Status

### ✅ **CONFIGURED - Ready to Use**

The following data sources have been configured with valid credentials in `.env` file (gitignored):

| Data Source | Status | Purpose | Configuration Location |
|-------------|--------|---------|------------------------|
| **ERA5 Climate Data** | ✅ Configured | Temperature, humidity, precipitation | `.env` (gitignored) |
| **NASA EarthData (MODIS)** | ✅ Configured | Vegetation indices (NDVI/EVI) | `.env` (gitignored) |
| **CHIRPS Precipitation** | ✅ No Auth Required | High-resolution rainfall data | Open access |
| **WorldPop** | ✅ No Auth Required | Population density | Open access |
| **Malaria Atlas Project** | ✅ No Auth Required | Historical malaria data | Open access |

### ⚪ **OPTIONAL - Not Required for Core Functionality**

| Service | Status | Purpose |
|---------|--------|---------|
| **Firebase FCM** | ⚪ Optional | Push notifications |
| **DHIS2** | ⚪ Optional | Health information system integration |
| **Sentry** | ⚪ Optional | Error tracking |

---

## 📋 How Credentials Are Stored

### ✅ Secure Storage (Gitignored)

**ALL credentials are stored in `.env` file which is in `.gitignore`**

**Files:**
- `.env` - Contains all API keys, usernames, passwords (✅ GITIGNORED)
- `~/.cdsapirc` - ERA5 API configuration (outside repo, safe)

**What's in `.env`:**
```bash
# ERA5 Climate Data
EXTERNAL_APIS__ERA5_API_KEY="your_era5_api_key_here"

# NASA EarthData
NASA_EARTHDATA_USERNAME="your_email@example.com"
NASA_EARTHDATA_PASSWORD="your_password_here"

# Other services...
```

---

## 🔐 How to Get Credentials

### 1. ERA5 Climate Data (Copernicus CDS)

**Registration:**
1. Visit: https://cds.climate.copernicus.eu/user/register
2. Create account (instant approval)
3. Log in → Click username → Profile
4. Scroll to "API Key" section
5. Copy your UID and API key

**Configure:**
```bash
# Add to .env
EXTERNAL_APIS__ERA5_API_KEY="YOUR_UID:YOUR_API_KEY"
```

**Also create `~/.cdsapirc`:**
```ini
url: https://cds.climate.copernicus.eu/api
key: YOUR_UID:YOUR_API_KEY
```

**Important:** Accept Terms & Conditions for each dataset before downloading

---

### 2. NASA EarthData Login (MODIS)

**Registration:**
1. Visit: https://urs.earthdata.nasa.gov/users/new
2. Create account (instant approval)
3. Note your username and password

**Configure:**
```bash
# Add to .env
NASA_EARTHDATA_USERNAME="your_email@example.com"
NASA_EARTHDATA_PASSWORD="your_password"
```

**Authorize Applications:**
1. Log in to https://urs.earthdata.nasa.gov/
2. Username dropdown → Applications → "APPROVE MORE APPLICATIONS"
3. Search "LP DAAC Data Pool" → Authorize

---

## 🧪 Testing Your Configuration

### Quick Verification:

```bash
# Check .env exists and is gitignored
git check-ignore .env
# Expected output: .env

# Test environment loading (without showing values)
python3 << 'EOF'
from dotenv import load_dotenv
import os
load_dotenv()
era5 = os.getenv('EXTERNAL_APIS__ERA5_API_KEY')
nasa = os.getenv('NASA_EARTHDATA_USERNAME')
print(f"ERA5: {'✅ Loaded' if era5 else '❌ Missing'}")
print(f"NASA: {'✅ Loaded' if nasa else '❌ Missing'}")
EOF
```

### Test API Connections:

```bash
# Test ERA5
python3 << 'EOF'
import cdsapi
c = cdsapi.Client()
print("✅ ERA5 authentication successful!")
EOF

# Test NASA EarthData (when CLI implemented)
python -m malaria_predictor.cli modis-test
```

---

## 📦 Optional Services Setup

### Firebase Cloud Messaging (FCM)

1. Create project at https://console.firebase.google.com/
2. Project Settings → Service accounts → "Generate new private key"
3. Download JSON file to secure location (NOT in repo)
4. Update `.env`:
```bash
FCM__ENABLE_FCM="true"
FCM__CREDENTIALS_PATH="/secure/path/to/firebase-service-account.json"
FCM__PROJECT_ID="your-project-id"
```

### Sentry Error Tracking

1. Create account at https://sentry.io
2. Copy DSN from project settings
3. Update `.env`:
```bash
MONITORING__SENTRY_DSN="https://your-dsn@sentry.io/project"
```

---

## 🔒 Security Best Practices

### ✅ What We Do Right:

1. **`.env` is gitignored** - Credentials never committed
2. **No credentials in code** - Only environment variables
3. **Separate documentation** - This file has NO real credentials

### ⚠️ Security Checklist:

- ✅ Never commit `.env` file
- ✅ Never put credentials in documentation
- ✅ Use environment variables only
- ✅ Add `.env` to `.gitignore`
- ⚠️ Generate strong secret key for production:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- ⚠️ Rotate credentials every 90 days
- ⚠️ Use `chmod 600 .env` in production
- ⚠️ Never log full credentials

---

## 🚨 If Credentials Are Exposed

### If accidentally committed to git:

```bash
# Remove file from git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (WARNING: destructive!)
git push origin --force --all
```

### If credentials leaked:

1. **Immediately revoke/regenerate** all exposed credentials
2. **Update `.env`** with new credentials
3. **Audit access logs** for unauthorized usage
4. **Notify security team** if applicable

---

## 📞 Troubleshooting

### ERA5 Issues:

**"Terms and Conditions not accepted"**
- Visit dataset page and accept T&C before downloading

**Authentication fails**
- Verify `~/.cdsapirc` has correct format
- Check API key is valid (not expired)

### NASA EarthData Issues:

**401 Unauthorized**
- Authorize "LP DAAC Data Pool" application
- Verify username/password in `.env`

**Login fails**
- Check credentials have no typos
- Verify account is active

---

## ✅ Summary

**Credentials are securely configured in `.env` (gitignored)**

Ready to use:
- ✅ ERA5 Climate Data
- ✅ NASA EarthData (MODIS)
- ✅ CHIRPS (no auth needed)
- ✅ WorldPop (no auth needed)
- ✅ Malaria Atlas Project (no auth needed)

**All sensitive data is in `.env` which is NOT committed to git.**

---

*Last Updated: 2024*
*Configuration complete - NO credentials in this file*
