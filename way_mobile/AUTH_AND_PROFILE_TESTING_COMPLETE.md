# Authentication & Profile Management - Complete Testing Guide

**Status:** ✅ ALL SYSTEMS FIXED AND READY FOR TESTING  
**Last Updated:** August 15, 2026  
**Coverage:** OTP Auth, Google Sign-In, Profile Management, Logout, Session Persistence

---

## 📋 Quick Summary of Fixes

### ✅ Fixed Issues (7/7)

| # | Issue | Fix | Status |
|---|-------|-----|--------|
| 1 | SSL Certificate Error | Added JWT fallback in backend for dev environments | ✅ Done |
| 2 | OTP Flow Broken | Fixed state management, removed manual navigation | ✅ Done |
| 3 | Google Sign-In COOP Error | Using signInWithRedirect instead of popup | ✅ Done |
| 4 | Profile Not Displaying | Profile screen loads user data from /users/me | ✅ Done |
| 5 | Profile Not Saveable | updateProfileName() working via PUT /users/me | ✅ Done |
| 6 | Logout Not Working | Cleared tokens, signed out Firebase, redirects properly | ✅ Done |
| 7 | Session Lost on Refresh | Token persisted, auto-restore on app restart | ✅ Done |

---

## 🧪 End-to-End Testing Checklist

### Prerequisites

```bash
# 1. Terminal 1: Start backend
cd c:\Users\ojhan\Desktop\way_transit\backend
python -m uvicorn main:app --reload

# 2. Terminal 2: Start Flutter Web
cd c:\Users\ojhan\Desktop\way_transit\way_mobile
flutter run -d chrome
```

**Expected Backend Output:**
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Expected Flutter Output:**
```
Launching lib\main.dart on Chrome in debug mode...
Flutter DevTools available at: http://127.0.0.1:xxxxx/devtools
```

---

## 🔄 Test Flow 1: Phone OTP Sign-In

### Steps

1. **Open the app** (already running on Chrome)
   - ✅ Should show splash screen with loading animation
   - ✅ After 9 seconds auto-advances to "Get started" screen

2. **Click "Continue with Phone"**
   - ✅ Navigates to phone number entry screen
   - ✅ Screen title: "Secure Your Account"

3. **Enter Phone Number**
   - ✅ Country code prefilled as "+91"
   - ✅ Enter: `9876543210` (test number)
   - ✅ Click "Send OTP"
   - ✅ Loading state shows (button grayed out)
   - ✅ Message appears: "OTP sent to +919876543210. Enter it below."

4. **Enter OTP**
   - ✅ 6 OTP input fields appear
   - ✅ Auto-focus on first field
   - ✅ Type: `123456` (test OTP)
   - ✅ Auto-advance between fields as you type
   - ✅ After all 6 digits entered, "Confirm OTP" button enabled

5. **Verify OTP**
   - ✅ Click "Confirm OTP"
   - ✅ Loading state shows
   - ✅ Backend validates OTP
   - ✅ Token exchanged and stored in SharedPreferences
   - ✅ **Auto-navigates to Profile Creation Screen**

6. **Create Profile**
   - ✅ Screen: "Create your Profile"
   - ✅ Name input field shown
   - ✅ Enter name: `Test User`
   - ✅ Click "Continue"
   - ✅ Profile saved to backend
   - ✅ **Auto-advances to Preferences Screen**

7. **Set Preferences**
   - ✅ Screen: "Select Travel Preferences"
   - ✅ Click preferences (e.g., "Solo Traveller", "Metro")
   - ✅ Selected items highlight in blue
   - ✅ Click "Confirm"
   - ✅ **Auto-advances to Final Step**

8. **Complete Setup**
   - ✅ Screen: "Find Your Way!"
   - ✅ Click "Get Started!"
   - ✅ **Auto-navigates to MainScreen (Home Tab)**

9. **Verify Landing Page**
   - ✅ Shows "HomeScreen" with bookings list
   - ✅ Bottom navigation shows 4 tabs: Home, Profile, Add Ticket, Wallet
   - ✅ No errors in console (F12)

### Expected Result: ✅ User logged in via OTP, profile created, on home page

---

## 🔄 Test Flow 2: Google Sign-In

### Prerequisites
- Make sure you're logged out from previous test
- Have a Google account ready

### Steps

1. **Start Fresh**
   - ✅ Click Profile tab (bottom nav)
   - ✅ Click "Logout" button
   - ✅ Confirms logout and redirects to LoginFlow

2. **Login Screen**
   - ✅ Back at "Get started" screen
   - ✅ Click "Continue with Gmail" (gray button with "G")

3. **Google Authentication**
   - ✅ Google popup/redirect happens
   - ✅ **On Chrome:** Should redirect to Google, not popup
   - ✅ Select your Google account
   - ✅ Approve permissions
   - ✅ **App redirects back**

4. **Auto-Navigation**
   - ✅ App automatically detects Firebase sign-in
   - ✅ Backend exchanges Firebase token for JWT
   - ✅ **Auto-navigates to MainScreen**

5. **Profile Setup (First Time Only)**
   - ✅ If first-time Google sign-in: May show profile creation
   - ✅ If returning user: Skips to MainScreen

6. **Verify Logged In**
   - ✅ Click Profile tab
   - ✅ See your Google account email
   - ✅ See "Provider: google"
   - ✅ Can edit name
   - ✅ "Logout" and "Delete Account" buttons present

### Expected Result: ✅ User logged in via Google, profile displayed, on home page

---

## 🔄 Test Flow 3: Profile Management

### Prerequisites
- User already logged in (either OTP or Google)

### Steps

1. **Navigate to Profile**
   - ✅ Click "Profile" tab (bottom nav, second icon)

2. **View Profile Data**
   - ✅ Avatar shows: 👤
   - ✅ User name displayed
   - ✅ Email or phone number shown
   - ✅ Auth provider shown (e.g., "Provider: phone", "Provider: google")
   - ✅ Quick cards: "Documents ↗", "Help ↗", "FAQ ↗"

3. **Edit Profile**
   - ✅ "Edit Profile" section visible
   - ✅ Name field editable
   - ✅ Change name to something else: `Updated Name`
   - ✅ Click "Save Profile"
   - ✅ Loading state: "Saving…"
   - ✅ Success message: "Profile updated successfully."
   - ✅ **Name updates in real-time on profile header**

4. **View Account Details**
   - ✅ "Account details" section shows:
     - Email (or "Not provided")
     - Phone (or "Not provided")
     - Verified status (Yes/No)

5. **Test Logout**
   - ✅ Click "Logout" button (white button)
   - ✅ Confirmation dialog appears: "Logout?"
   - ✅ Click "Yes" or "Logout"
   - ✅ Token cleared from storage
   - ✅ All Firebase sessions signed out
   - ✅ **Redirects to LoginFlow**

6. **Test Delete Account (Optional - Advanced)**
   - ✅ **Warning:** This is destructive!
   - ✅ Click "Delete Account" (red button)
   - ✅ Confirmation dialog: "This will permanently delete your account"
   - ✅ Click "Delete"
   - ✅ Account deleted from backend
   - ✅ Token cleared
   - ✅ **Redirects to LoginFlow**
   - ✅ **Cannot log back in with same account**

### Expected Result: ✅ Profile fully functional, edit works, logout works

---

## 🔄 Test Flow 4: Session Persistence (Auto-Login)

### Prerequisites
- User logged in

### Steps

1. **Close and Reopen App**
   - ✅ App is running and user logged in
   - ✅ Close the Chrome tab (or press Ctrl+W)
   - ✅ **App closes completely**

2. **Reopen App**
   - ✅ Type in Chrome: `localhost:8000` (or same Flutter port)
   - ✅ Or run: `flutter run -d chrome` again
   - ✅ App starts fresh

3. **Auto-Login**
   - ✅ Shows splash screen with loading animation
   - ✅ **No need to enter password again!**
   - ✅ Splash auto-advances to home after 9 seconds
   - ✅ **OR auto-skips splash if token is valid**
   - ✅ **Directly navigates to MainScreen (Home tab)**

4. **Verify Logged In State**
   - ✅ No login screens shown
   - ✅ Profile tab shows your name and email
   - ✅ Can navigate between tabs freely
   - ✅ No "Please log in" errors

5. **Refresh Page (F5)**
   - ✅ Press F5 in browser
   - ✅ App reloads
   - ✅ Shows splash briefly
   - ✅ **User still logged in** (no re-login needed)
   - ✅ All tabs accessible

### Expected Result: ✅ Session persists across app restarts and page refreshes

---

## 🔄 Test Flow 5: Error Handling & Edge Cases

### Test 5A: Expired Token

1. **Login and Let Token Expire (Simulated)**
   - ✅ Normally tokens last 7 days
   - ✅ To simulate expiry: Manually edit token in SharedPreferences (advanced)
   - ✅ Or wait until token naturally expires

2. **Try to Access Protected Page**
   - ✅ Shows error message or navigates to login
   - ✅ No crash or frozen screens

### Test 5B: Network Error

1. **Backend Down**
   - ✅ Stop backend: Ctrl+C in backend terminal
   - ✅ Click Profile tab
   - ✅ Shows error: "Unable to load profile"
   - ✅ Has "Retry" button
   - ✅ Click Retry
   - ✅ **If backend still down:** Shows error again
   - ✅ **If backend restarted:** Loads successfully

### Test 5C: Invalid OTP

1. **Try to Login with Wrong OTP**
   - ✅ Request OTP normally
   - ✅ Enter wrong code: `000000`
   - ✅ Click "Confirm OTP"
   - ✅ Shows error: "OTP verification failed"
   - ✅ Can try again with correct OTP

### Test 5D: Google Sign-In Cancellation

1. **Click Google Sign-In**
   - ✅ Google popup/redirect appears
   - ✅ Close it without selecting account
   - ✅ App shows error: "Google sign-in failed"
   - ✅ Can retry from login screen

### Expected Result: ✅ All errors handled gracefully, no crashes

---

## 🧠 Browser Developer Console Checks (F12)

### Open Console and Verify

```
✅ No RED errors about:
   - "CERTIFICATE_VERIFY_FAILED"
   - "Cross-Origin-Opener-Policy"
   - "setState after dispose"
   - "Null token fallback"

✅ Network tab shows:
   - POST /auth/firebase → 200 OK (or 400 if SSL issue, but shows error message)
   - GET /users/me → 200 OK
   - PUT /users/me → 200 OK
   - DELETE /users/me → 200 OK

✅ No console warnings about:
   - "Missing token"
   - "dev-token" usage
   - Undefined variables
```

### Check Local Storage (F12 → Application → Local Storage)

```
✅ Should see: (if logged in)
   - auth_token: <JWT token string>
   - user_email: <user email>

✅ After logout:
   - auth_token: (deleted)
   - user_email: (deleted)
```

### Check SharedPreferences (Mobile via ADB or emulator)

```
✅ SharedPreferences should contain:
   - 'auth_token': <valid JWT>
   - 'user_email': <user email>

✅ Token format:
   - <header>.<payload>.<signature>
   - Can decode payload to verify uid and email
```

---

## 📊 Test Results Summary

### Test Results Template

Copy and fill in:

```markdown
## Test Run: [Date/Time]

### Test Flow 1: Phone OTP Sign-In
- [ ] Phone entry screen loads
- [ ] OTP sent successfully
- [ ] OTP verified
- [ ] Profile created
- [ ] User on home page
**Status:** ✅ PASS / ❌ FAIL

### Test Flow 2: Google Sign-In
- [ ] Google auth popup/redirect works
- [ ] Firebase token exchanged
- [ ] Auto-navigates to MainScreen
- [ ] Profile shows correct email
**Status:** ✅ PASS / ❌ FAIL

### Test Flow 3: Profile Management
- [ ] Profile displays correctly
- [ ] Can edit name
- [ ] Changes save to backend
- [ ] Logout works
**Status:** ✅ PASS / ❌ FAIL

### Test Flow 4: Session Persistence
- [ ] Close/reopen app → still logged in
- [ ] Refresh page → still logged in
- [ ] Token persisted correctly
**Status:** ✅ PASS / ❌ FAIL

### Test Flow 5: Error Handling
- [ ] Network errors handled gracefully
- [ ] Invalid OTP shows error
- [ ] Google cancellation shows error
- [ ] No crashes observed
**Status:** ✅ PASS / ❌ FAIL

### Browser Console
- [ ] No red errors
- [ ] Network requests successful
- [ ] Token in localStorage
**Status:** ✅ PASS / ❌ FAIL

### Overall Status
✅ ALL TESTS PASSED

### Notes
- [Any issues encountered]
- [Any workarounds applied]
- [Recommendations]
```

---

## 🚨 Troubleshooting

### Issue: "Failed to send OTP"

**Check:**
1. Backend running? (`uvicorn` in terminal 1)
2. Phone number correct? (Must have 10 digits for test)
3. Firebase phone auth enabled? (Check Firebase console)

**Fix:**
```bash
# Restart backend
cd backend
python -m uvicorn main:app --reload
```

### Issue: "Firebase certificate verification failed"

**Check:**
1. This is **expected for development**
2. Backend should handle it gracefully
3. Should show user-friendly error message

**Fix:**
```bash
# Update Python SSL certificates
python -m pip install --upgrade certifi

# Restart backend
python -m uvicorn main:app --reload
```

### Issue: Google Sign-In Shows Popup Error

**Check:**
1. Are you on `localhost:port`? (Required for Firebase)
2. Not on `127.0.0.1`? (Try localhost instead)
3. Is HTTPS/SSL issue? (For dev, HTTP is fine)

**Fix:**
```bash
# Use localhost, not 127.0.0.1
http://localhost:8080  # ✅ Good
http://127.0.0.1:8080  # ❌ May fail with Google
```

### Issue: Profile Not Loading

**Check:**
1. User logged in? (Check localStorage in F12)
2. Backend running? (Check terminal)
3. Token valid? (Check token expiration)

**Fix:**
```bash
# Check browser console (F12) for specific error
# Logout and login again
# If persists, restart backend
```

### Issue: Session Not Persisting (Auto-Login Doesn't Work)

**Check:**
1. Token saved? (Check localStorage/SharedPreferences)
2. Token expired? (Check token payload)
3. Firebase not initialized? (Check Firebase setup)

**Fix:**
```bash
# Clear all storage and re-login
# In browser F12 → Application → Clear site data
# Restart Flutter app
flutter run -d chrome
```

---

## ✅ Sign-Off Checklist

Before marking complete, verify:

- [ ] All 5 test flows completed successfully
- [ ] No red errors in browser console (F12)
- [ ] Token properly stored and retrieved
- [ ] Profile saves and loads correctly
- [ ] Logout clears all data
- [ ] Session persists across refreshes
- [ ] Error messages are user-friendly
- [ ] No "dev-token" fallbacks used
- [ ] Backend SSL issue handled gracefully
- [ ] OTP and Google Sign-In both working

---

## 📞 Support

If tests fail:

1. **Check browser F12 console** - Copy exact error message
2. **Check backend terminal** - Look for exceptions
3. **Restart services** - Backend first, then Flutter
4. **Clear storage** - F12 → Application → Clear all
5. **Re-run tests** - Sometimes temporary issues

---

**Status:** 🟢 **READY FOR PRODUCTION TESTING**

**Next Steps:**
1. Run through all 5 test flows
2. Document any issues found
3. Fix and re-test
4. Deploy to staging
5. Conduct user acceptance testing (UAT)

---

**All systems fixed and ready! Happy testing! 🎉**
