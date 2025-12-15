# Authentication Guide

## Overview

The Vaitikan E-Commerce Platform uses JWT (JSON Web Token) authentication to secure API endpoints. This guide explains how to authenticate users and manage tokens.

## Authentication Flow

```
┌──────────────┐
│   Register   │
│   New User   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    Login     │
│  (Get Tokens)│
└──────┬───────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌──────────────┐  ┌──────────────┐
│Access Token  │  │Refresh Token │
│(60 minutes)  │  │  (7 days)    │
└──────┬───────┘  └──────┬───────┘
       │                 │
       ▼                 │
┌──────────────┐         │
│  API Request │         │
│ with Token   │         │
└──────┬───────┘         │
       │                 │
       ▼                 │
┌──────────────┐         │
│Token Expired?│         │
└──────┬───────┘         │
       │                 │
       │ Yes             │
       ▼                 │
┌──────────────┐         │
│   Refresh    │◄────────┘
│Access Token  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Continue    │
│  API Calls   │
└──────────────┘
```

## Step 1: User Registration

Create a new user account with customer role by default.

### Request

```http
POST /api/users/register/
Content-Type: application/json

{
  "email": "customer@example.com",
  "full_name": "John Doe",
  "phone": "+919876543210",
  "password": "SecurePassword123!"
}
```

### Response

```json
{
  "id": 1,
  "email": "customer@example.com",
  "full_name": "John Doe",
  "phone": "+919876543210",
  "user_type": "customer",
  "account_status": "active",
  "date_joined": "2024-01-15T10:30:00Z"
}
```

### Password Requirements

- Minimum 8 characters
- Must contain at least one uppercase letter
- Must contain at least one lowercase letter
- Must contain at least one number
- Must contain at least one special character

## Step 2: User Login

Authenticate with email and password to receive JWT tokens.

### Request

```http
POST /api/users/login/
Content-Type: application/json

{
  "email": "customer@example.com",
  "password": "SecurePassword123!"
}
```

### Response

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTY0MjgzNDgwMCwiaWF0IjoxNjQyMjMwMDAwLCJqdGkiOiJhYmMxMjMiLCJ1c2VyX2lkIjoxfQ.signature",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjQyMjMzNjAwLCJpYXQiOjE2NDIyMzAwMDAsImp0aSI6ImRlZjQ1NiIsInVzZXJfaWQiOjF9.signature"
}
```

### Token Details

**Access Token**:

- Used for API authentication
- Expires in 60 minutes
- Include in Authorization header

**Refresh Token**:

- Used to get new access tokens
- Expires in 7 days
- Store securely (httpOnly cookie recommended)

## Step 3: Making Authenticated Requests

Include the access token in the Authorization header for all protected endpoints.

### Request Format

```http
GET /api/users/profile/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### JavaScript Example

```javascript
const accessToken = localStorage.getItem("access_token");

fetch("/api/users/profile/", {
  method: "GET",
  headers: {
    Authorization: `Bearer ${accessToken}`,
    "Content-Type": "application/json",
  },
})
  .then((response) => response.json())
  .then((data) => console.log(data));
```

### Python Example

```python
import requests

access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

response = requests.get('http://example.com/api/users/profile/', headers=headers)
data = response.json()
```

## Step 4: Refreshing Access Token

When the access token expires, use the refresh token to get a new one.

### Request

```http
POST /api/users/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Response

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.newAccessToken..."
}
```

### Automatic Token Refresh (JavaScript)

```javascript
async function refreshAccessToken() {
  const refreshToken = localStorage.getItem("refresh_token");

  const response = await fetch("/api/users/token/refresh/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ refresh: refreshToken }),
  });

  if (response.ok) {
    const data = await response.json();
    localStorage.setItem("access_token", data.access);
    return data.access;
  } else {
    // Refresh token expired, redirect to login
    window.location.href = "/login/";
  }
}

// Intercept 401 responses and refresh token
async function authenticatedFetch(url, options = {}) {
  let accessToken = localStorage.getItem("access_token");

  options.headers = {
    ...options.headers,
    Authorization: `Bearer ${accessToken}`,
  };

  let response = await fetch(url, options);

  if (response.status === 401) {
    // Token expired, try to refresh
    accessToken = await refreshAccessToken();
    options.headers["Authorization"] = `Bearer ${accessToken}`;
    response = await fetch(url, options);
  }

  return response;
}
```

## Step 5: User Logout

Invalidate the refresh token to log out the user.

### Request

```http
POST /api/users/logout/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Response

```json
{
  "message": "Logout successful"
}
```

### JavaScript Logout Example

```javascript
async function logout() {
  const accessToken = localStorage.getItem("access_token");
  const refreshToken = localStorage.getItem("refresh_token");

  await fetch("/api/users/logout/", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ refresh: refreshToken }),
  });

  // Clear tokens from storage
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");

  // Redirect to login
  window.location.href = "/login/";
}
```

## Role-Based Access Control

The platform supports three user roles:

### User Roles

1. **Customer** (default)

   - Browse products
   - Manage cart
   - Place orders
   - Submit inquiries and feedback
   - View own orders and payments

2. **Operator**

   - All customer permissions
   - Manage inventory
   - Manage manufacturing specifications
   - View material requirements

3. **Admin**
   - All operator permissions
   - Manage products
   - Manage all orders
   - View analytics dashboard
   - Manage inquiries and quotations
   - Resolve complaints

### Checking User Role

The user's role is included in the profile response:

```json
{
  "id": 1,
  "email": "admin@example.com",
  "full_name": "Admin User",
  "user_type": "admin",
  "account_status": "active"
}
```

### Role-Based UI Rendering

```javascript
async function getUserProfile() {
  const response = await authenticatedFetch("/api/users/profile/");
  const user = await response.json();

  // Show/hide UI elements based on role
  if (user.user_type === "admin") {
    document.getElementById("admin-menu").style.display = "block";
  }

  if (user.user_type === "operator" || user.user_type === "admin") {
    document.getElementById("inventory-menu").style.display = "block";
  }
}
```

## Error Handling

### Common Authentication Errors

#### 401 Unauthorized

**Cause**: Missing or invalid access token

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Solution**: Include valid access token in Authorization header

#### 403 Forbidden

**Cause**: Insufficient permissions for the requested resource

```json
{
  "detail": "You do not have permission to perform this action."
}
```

**Solution**: Ensure user has required role (admin/operator)

#### 400 Bad Request (Login)

**Cause**: Invalid credentials

```json
{
  "detail": "No active account found with the given credentials"
}
```

**Solution**: Verify email and password are correct

## Security Best Practices

### Token Storage

**Frontend (Browser)**:

- ✅ Store access token in memory or localStorage
- ✅ Store refresh token in httpOnly cookie (recommended)
- ❌ Never store tokens in regular cookies accessible by JavaScript
- ❌ Never log tokens to console in production

**Mobile Apps**:

- ✅ Use secure storage (Keychain on iOS, Keystore on Android)
- ❌ Never store in plain text files

### Token Transmission

- ✅ Always use HTTPS in production
- ✅ Include tokens only in Authorization header
- ❌ Never include tokens in URL parameters
- ❌ Never include tokens in request body (except refresh endpoint)

### Token Lifecycle

- ✅ Implement automatic token refresh
- ✅ Clear tokens on logout
- ✅ Handle token expiration gracefully
- ✅ Implement token blacklisting on logout

### Password Security

- ✅ Enforce strong password requirements
- ✅ Hash passwords with bcrypt/PBKDF2
- ✅ Implement rate limiting on login attempts
- ✅ Use HTTPS for all authentication requests

## Complete Authentication Example

### HTML + JavaScript

```html
<!DOCTYPE html>
<html>
  <head>
    <title>Authentication Example</title>
  </head>
  <body>
    <div id="login-form">
      <h2>Login</h2>
      <input type="email" id="email" placeholder="Email" />
      <input type="password" id="password" placeholder="Password" />
      <button onclick="login()">Login</button>
    </div>

    <div id="user-profile" style="display: none;">
      <h2>Welcome, <span id="user-name"></span></h2>
      <button onclick="logout()">Logout</button>
    </div>

    <script>
      const API_BASE = "http://localhost:8000/api";

      // Login function
      async function login() {
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        try {
          const response = await fetch(`${API_BASE}/users/login/`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ email, password }),
          });

          if (response.ok) {
            const data = await response.json();

            // Store tokens
            localStorage.setItem("access_token", data.access);
            localStorage.setItem("refresh_token", data.refresh);

            // Load user profile
            await loadProfile();
          } else {
            alert("Login failed");
          }
        } catch (error) {
          console.error("Login error:", error);
        }
      }

      // Load user profile
      async function loadProfile() {
        const accessToken = localStorage.getItem("access_token");

        try {
          const response = await fetch(`${API_BASE}/users/profile/`, {
            headers: {
              Authorization: `Bearer ${accessToken}`,
            },
          });

          if (response.ok) {
            const user = await response.json();

            // Show profile
            document.getElementById("login-form").style.display = "none";
            document.getElementById("user-profile").style.display = "block";
            document.getElementById("user-name").textContent = user.full_name;
          } else if (response.status === 401) {
            // Try to refresh token
            await refreshToken();
            await loadProfile();
          }
        } catch (error) {
          console.error("Profile error:", error);
        }
      }

      // Refresh access token
      async function refreshToken() {
        const refreshToken = localStorage.getItem("refresh_token");

        try {
          const response = await fetch(`${API_BASE}/users/token/refresh/`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ refresh: refreshToken }),
          });

          if (response.ok) {
            const data = await response.json();
            localStorage.setItem("access_token", data.access);
          } else {
            // Refresh token expired, redirect to login
            logout();
          }
        } catch (error) {
          console.error("Refresh error:", error);
        }
      }

      // Logout function
      async function logout() {
        const accessToken = localStorage.getItem("access_token");
        const refreshToken = localStorage.getItem("refresh_token");

        try {
          await fetch(`${API_BASE}/users/logout/`, {
            method: "POST",
            headers: {
              Authorization: `Bearer ${accessToken}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ refresh: refreshToken }),
          });
        } catch (error) {
          console.error("Logout error:", error);
        }

        // Clear tokens
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");

        // Show login form
        document.getElementById("login-form").style.display = "block";
        document.getElementById("user-profile").style.display = "none";
      }

      // Check if user is already logged in
      window.onload = function () {
        const accessToken = localStorage.getItem("access_token");
        if (accessToken) {
          loadProfile();
        }
      };
    </script>
  </body>
</html>
```

## Troubleshooting

### Issue: "Authentication credentials were not provided"

**Cause**: Authorization header missing or malformed

**Solution**:

```javascript
// Correct format
headers: {
  'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
}

// Common mistakes to avoid
headers: {
  'Authorization': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...' // Missing "Bearer"
  'Authorization': 'bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...' // Lowercase "bearer"
}
```

### Issue: Token expired but refresh fails

**Cause**: Refresh token also expired (after 7 days)

**Solution**: Redirect user to login page

```javascript
if (response.status === 401) {
  window.location.href = "/login/";
}
```

### Issue: CORS errors during authentication

**Cause**: Frontend and backend on different domains

**Solution**: Configure CORS in Django settings

```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://your-frontend-domain.com"
]

CORS_ALLOW_CREDENTIALS = True
```

---

**Document Version**: 1.0  
**Last Updated**: January 15, 2024
