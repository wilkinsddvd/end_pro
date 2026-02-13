# System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          END_PRO BACKEND SYSTEM                              │
│                   JWT Authentication & User Data Isolation                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT REQUEST                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │   Authorization Header Check   │
                    │   "Bearer <JWT_TOKEN>"         │
                    └────────────────────────────────┘
                                     │
                ┌────────────────────┴────────────────────┐
                │                                         │
                ▼                                         ▼
    ┌───────────────────────┐              ┌──────────────────────────┐
    │   PUBLIC ENDPOINTS    │              │   PROTECTED ENDPOINTS    │
    │   (No Auth Required)  │              │   (Auth Required)        │
    ├───────────────────────┤              ├──────────────────────────┤
    │ POST /api/register    │              │ GET  /api/self           │
    │ POST /api/login       │              │ POST /api/logout         │
    └───────────────────────┘              │ GET  /api/posts          │
                │                          │ GET  /api/posts/{id}     │
                │                          │ GET  /api/siteinfo       │
                │                          │ GET  /api/menus          │
                │                          │ GET  /api/tickets        │
                │                          │ POST /api/tickets        │
                │                          │ GET  /api/tickets/{id}   │
                │                          │ PUT  /api/tickets/{id}   │
                │                          │ DELETE /api/tickets/{id} │
                │                          │ GET  /api/quick-replies  │
                │                          │ POST /api/quick-replies  │
                │                          │ GET  /api/quick-replies/{id} │
                │                          │ PUT  /api/quick-replies/{id} │
                │                          │ DELETE /api/quick-replies/{id} │
                │                          └──────────────────────────┘
                │                                         │
                │                                         ▼
                │                          ┌──────────────────────────┐
                │                          │   auth_utils.py          │
                │                          │   get_current_user()     │
                │                          ├──────────────────────────┤
                │                          │ 1. Extract Bearer token  │
                │                          │ 2. Validate JWT          │
                │                          │ 3. Decode payload        │
                │                          │ 4. Fetch User from DB    │
                │                          │ 5. Return User object    │
                │                          └──────────────────────────┘
                │                                         │
                │                                         │
                ▼                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATABASE LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │    User     │    │    Post     │    │   Ticket    │                     │
│  ├─────────────┤    ├─────────────┤    ├─────────────┤                     │
│  │ id          │◄───│ author_id   │    │ id          │                     │
│  │ username    │    │ title       │    │ title       │                     │
│  │ password_hash│   │ content     │    │ description │                     │
│  │ created_at  │    │ date        │    │ category    │                     │
│  └─────────────┘    │ views       │    │ priority    │                     │
│         ▲           └─────────────┘    │ status      │                     │
│         │                              │ created_at  │                     │
│         │                              │ user_id     │◄────┐               │
│         │                              └─────────────┘     │               │
│         │                                                  │               │
│         │           ┌─────────────┐    ┌─────────────┐    │               │
│         │           │  SiteInfo   │    │    Menu     │    │               │
│         │           ├─────────────┤    ├─────────────┤    │               │
│         │           │ id          │    │ id          │    │               │
│         │           │ title       │    │ title       │    │               │
│         │           │ description │    │ path        │    │               │
│         │           │ icp         │    │ url         │    │               │
│         │           │ footer      │    └─────────────┘    │               │
│         │           └─────────────┘                       │               │
│         │                                                 │               │
│         │           ┌─────────────┐                       │               │
│         └───────────┤ QuickReply  │                       │               │
│                     ├─────────────┤                       │               │
│                     │ id          │                       │               │
│                     │ title       │                       │               │
│                     │ content     │                       │               │
│                     │ category    │                       │               │
│                     │ use_count   │                       │               │
│                     │ created_at  │                       │               │
│                     │ user_id     │───────────────────────┘               │
│                     └─────────────┘                                       │
│                                                                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER DATA ISOLATION                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  QuickReply Operations:                                                      │
│    • List:   WHERE user_id = current_user.id                                │
│    • Create: SET user_id = current_user.id                                  │
│    • Get:    WHERE id = {id} AND user_id = current_user.id                  │
│    • Update: WHERE id = {id} AND user_id = current_user.id                  │
│    • Delete: WHERE id = {id} AND user_id = current_user.id                  │
│                                                                              │
│  Ticket Operations:                                                          │
│    • List:   WHERE user_id = current_user.id                                │
│    • Create: SET user_id = current_user.id                                  │
│    • Get:    WHERE id = {id} AND user_id = current_user.id                  │
│    • Update: WHERE id = {id} AND user_id = current_user.id                  │
│    • Delete: WHERE id = {id} AND user_id = current_user.id                  │
│                                                                              │
│  Post Operations:                                                            │
│    • List:   WHERE author_id = current_user.id                              │
│    • Get:    WHERE id = {id} AND author_id = current_user.id                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         AUTHENTICATION FLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Step 1: User Registration                                                   │
│    POST /api/register                                                        │
│    Body: {"username": "user", "password": "pass"}                           │
│    Response: {"code": 201, "data": {"id": 1, "username": "user"}, ...}      │
│                                                                              │
│  Step 2: User Login                                                          │
│    POST /api/login                                                           │
│    Body: {"username": "user", "password": "pass"}                           │
│    Response: {"code": 200, "data": {"id": 1, "username": "user",            │
│               "token": "eyJhbGc..."}, "msg": "login success"}                │
│                                                                              │
│  Step 3: Access Protected Resource                                          │
│    GET /api/tickets                                                          │
│    Header: Authorization: Bearer eyJhbGc...                                  │
│    Response: {"code": 200, "data": {...}, "msg": "success"}                 │
│                                                                              │
│  Step 4: Token Validation (Automatic)                                        │
│    • get_current_user() extracts token from header                          │
│    • Validates token signature                                              │
│    • Checks expiration (default: 30 minutes)                                │
│    • Fetches User from database                                             │
│    • Returns User object to endpoint                                        │
│                                                                              │
│  Step 5: Authorization Check (Automatic)                                     │
│    • Endpoint uses current_user.id to filter queries                        │
│    • Only returns/modifies data owned by current user                       │
│    • Returns 404 if trying to access other user's data                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         SECURITY FEATURES                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ✅ JWT Token Authentication                                                 │
│     • Tokens signed with SECRET_KEY                                         │
│     • HS256 algorithm                                                       │
│     • 30-minute expiration (configurable)                                   │
│                                                                              │
│  ✅ Password Security                                                        │
│     • SHA-256 hashing                                                       │
│     • Stored as password_hash in database                                   │
│                                                                              │
│  ✅ User Data Isolation                                                      │
│     • All queries filter by user ownership                                  │
│     • No cross-user data access                                             │
│     • Validation at database query level                                    │
│                                                                              │
│  ✅ Error Handling                                                           │
│     • 401 for authentication failures                                       │
│     • 404 for unauthorized resource access                                  │
│     • Consistent error response format                                      │
│                                                                              │
│  ✅ Response Format Consistency                                              │
│     • All responses: {"code": xxx, "data": {...}, "msg": "..."}             │
│     • Success: code 200/201                                                 │
│     • Auth error: code 401                                                  │
│     • Not found: code 404                                                   │
│     • Server error: code 500                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         DEPLOYMENT CHECKLIST                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  □ Set JWT_SECRET_KEY environment variable                                  │
│  □ Set JWT_EXPIRE_MINUTES environment variable                              │
│  □ Set DATABASE_URL environment variable                                    │
│  □ Run database migration to add QuickReply.user_id if needed               │
│  □ Test authentication flow end-to-end                                      │
│  □ Verify user data isolation in production                                 │
│  □ Update API documentation                                                 │
│  □ Monitor authentication failures                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```
