# Firebase Google Sign-In Testing Guide

**Status:** ✅ App Running | ⚠️ SSL Certificate Issue (Development Only)

---

## Current Status

### ✅ What's Working
- Flutter Web app launches successfully on Chrome
- UI renders correctly (splash, login screens)
- Phone OTP flow works (when backend SSL is resolved)
- Navigation between screens works
- Hot reload/hot restart working

### ⚠️ What Needs Fixing
- **SSL Certificate Verification Error** when verifying Firebase tokens
- This is a **backend development environment issue**, not an app code issue
- Error: `[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed`

---

## Understanding the SSL Error

### Root Cause
When you click "Continue with Gmail":
1. ✅ Google popup opens and you authenticate
2. ✅ Google returns an ID token
3. ✅ App sends token to backend
4. ❌ Backend tries to verify token with Firebase
5. ❌ Backend can't reach Google's certificate verification servers due to SSL issues

### Why This Happens
Your development machine might be:
- Missing root CA certificates
- Behind a corporate proxy/firewall
- Using Windows/MacOS with outdated SSL certificates
- Missing Python SSL dependencies

---

## Solution: Fix SSL Certificate Verification

### Option 1: Update Python SSL Certificates (Recommended)

#### On Windows (PowerShell as Admin):
```powershell
# For Python 3.9+, run the certificate installer
$python_path = (python -c "import sys; print(sys.prefix)").Trim()
& "$python_path\Scripts\Install Certificates.command"

# Or manually:
$certifi_path = (pip show certifi | Select-String "Location:").ToString().Split()[-1]
python -c "import ssl; ssl.create_default_context()"
```

#### On macOS:
```bash
/Applications/Python\ 3.x/Install\ Certificates.command
```

#### On Linux:
```bash
# Debian/Ubuntu
sudo apt-get install ca-certificates

# Fedora
sudo dnf install ca-certificates
```

### Option 2: Disable SSL Verification for Development

**⚠️ WARNING: Only for local development, NEVER for production**

Create `backend/.env.dev`:
```bash
# Development only!
PYTHONHTTPSVERIFY=0
```

Then in `backend/routes/auth.py`, add at the top:
```python
import os
if os.getenv('PYTHONHTTPSVERIFY') == '0':
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context
```

**Then restart backend:**
```bash
PYTHONHTTPSVERIFY=0 python -m uvicorn main:app --reload
```

### Option 3: Use a Corporate Proxy Certificate

If behind a corporate firewall:

```bash
# Set Python to use corporate certificates
pip install --upgrade certifi
```

Then configure Python to trust your organization's root CA certificate in `backend/routes/auth.py`:

```python
import certifi
import ssl

ssl_context = ssl.create_default_context(cafile=certifi.where())
# Use ssl_context in Firebase client
```

---

## Testing Firebase Google Sign-In

### Step 1: Ensure Backend is Running
```bash
cd backend
python -m uvicorn main:app --reload
```

Expected output:
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 2: Fix SSL Certificates (Choose One Option Above)

### Step 3: Test Google Sign-In

1. **Open Flutter app** (already running or restart):
   ```bash
   cd way_mobile
   flutter run -d chrome
   ```

2. **In the app**:
   - You should see login screen
   - Click "Continue with Gmail" (gray button with "G")
   - Google popup should open
   - Select your Google account
   - Approve permissions

3. **Expected Flow**:
   ```
   ✅ Google popup opens
   ✅ User authenticates
   ✅ Popup closes
   ✅ App receives ID token
   ✅ Backend verifies token (should work now!)
   ✅ Backend creates/updates user
   ✅ App receives access token
   ✅ App navigates to MainScreen
   ✅ User sees home page
   ```

### Step 4: Check Browser Console

Press **F12** in browser to open developer tools:

1. **Console Tab**: Should NOT see red errors about COOP
2. **Network Tab**: 
   - POST to `/auth/firebase` should return **200 OK**
   - Response should contain `access_token`

3. **Look for**:
   ```
   ✅ POST http://localhost:8000/auth/firebase [200 OK]
   ✅ Response: {"access_token": "eyJ0eXAi...", "token_type": "bearer"}
   ❌ NOT: 400 or SSL errors
   ```

---

## Verification Checklist

- [ ] Backend starts without errors
- [ ] SSL certificates updated or workaround applied
- [ ] Flutter app running on Chrome
- [ ] Click "Continue with Gmail"
- [ ] Google popup opens
- [ ] Select account and approve
- [ ] No red errors in browser F12 console
- [ ] Network shows POST to /auth/firebase returns 200
- [ ] App navigates to home screen
- [ ] Refresh page (F5) - user still logged in

---

## Debugging

### If Google Popup Doesn't Open
Check browser F12 → Console for errors like:
- `Cross-Origin-Opener-Policy` error → Use signInWithRedirect (already implemented ✅)
- Permission denied → Check Firebase config
- Timeout → Check internet connection

**Fix**: Already implemented in `auth_service.dart` (signInWithRedirect for web)

### If Backend Shows SSL Error
Check backend terminal output for:
```
[SSL: CERTIFICATE_VERIFY_FAILED]
```

**Fix**: Follow Option 1, 2, or 3 above

### If No Response from Backend
Check:
```bash
# Verify backend is running
curl http://localhost:8000/docs

# Check if endpoint exists
curl http://localhost:8000/auth/firebase
```

Should get proper response, not connection refused.

### If Token Verification Passes but Navigation Fails
Check browser F12 → Console for navigation errors:
- May be missing route
- May be missing screen widget
- Check if `MainScreen` is properly imported

---

## Code Changes Made

### 1. Fixed Flutter Compilation
**File**: `way_mobile/lib/screens/login_flow.dart`
- ✅ Added missing `class LoginFlow extends StatefulWidget {` declaration

### 2. Fixed setState() After Dispose
**File**: `way_mobile/lib/screens/login_flow.dart`
- ✅ Added `if (mounted)` checks before all `setState()` calls
- ✅ Prevents errors when navigating away from phone OTP screen

### 3. Improved Backend Error Handling
**File**: `backend/routes/auth.py`
- ✅ Better SSL error detection and messaging
- ✅ Logs full error for debugging
- ✅ Provides helpful development tips

---

## Production Deployment Notes

### ✅ For Production:
- Remove SSL verification workarounds
- Use proper CA certificates
- Update certifi: `pip install --upgrade certifi`
- Ensure Firebase credentials are in AWS Secrets Manager
- Add HTTPS for all connections
- Monitor token verification errors

### ⚠️ Never in Production:
- Disable SSL verification
- Commit credentials to git
- Use development certificates
- Ignore CERTIFICATE_VERIFY_FAILED errors

---

## Quick Testing Commands

```bash
# Test backend is running
curl http://localhost:8000/docs

# Test Firebase endpoint exists
curl -X POST http://localhost:8000/auth/firebase \
  -H "Content-Type: application/json" \
  -d '{"id_token": "test"}'

# Should return: Invalid Firebase ID token (normal if test token)
# Should NOT return: SSL Certificate Verify Failed
```

---

## Next Steps

1. ✅ **Run the commands** from Option 1/2/3 to fix SSL certificates
2. ✅ **Restart backend**: `python -m uvicorn main:app --reload`
3. ✅ **Test Google Sign-In** using the checklist above
4. ✅ **Verify navigation** to home screen works
5. ✅ **Test persistence**: Refresh page (F5) and verify user stays logged in
6. ✅ **Check all auth methods**: Try phone OTP, Google, skip option

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| SSL cert error | Python missing root CAs | Run Install Certificates script |
| Popup blocked | Browser security | Allow popups for localhost |
| Token not found | Firebase not initialized | Check firebase-admin.json exists |
| Nav fails after login | Missing MainScreen | Check import in main.dart |
| User not persisted | No auth state listener | Listener already added ✅ |

---

## Support

- **Flutter Docs**: https://firebase.flutter.dev/docs/auth/overview/
- **Python SSL**: https://docs.python.org/3/library/ssl.html
- **Firebase Docs**: https://firebase.google.com/docs/auth/web/google-signin

---

**Status**: 🟡 In Progress  
**Last Updated**: August 15, 2026  
**Next**: Fix SSL certificates and test flow

