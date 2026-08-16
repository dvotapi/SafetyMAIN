SafetyMAIN — Application Server Deployment Agent Instruction
Objective
Deploy SafetyMAIN on the existing application VDS and connect it to the already deployed PostgreSQL database on the separate database server.
The application server already hosts other services and already has a reverse proxy.
The deployment must therefore be additive and non-destructive:

* do not replace the existing reverse proxy;
* do not stop or reconfigure unrelated services;
* do not reuse ports already occupied by other applications;
* do not deploy PostgreSQL on the application server;
* do not expose the SafetyMAIN backend directly to the public Internet;
* do not expose production secrets in Git, logs, shell history, or documentation.

The expected architecture is:

```
Internet
    │
    ▼
Existing Reverse Proxy
    │
    ├── SafetyMAIN frontend
    │
    └── /api/ → SafetyMAIN backend
                     │
                     ▼
              Database Server
                PostgreSQL
```

1. Inspect Before Changing Anything
Before making changes, inspect the VDS and produce a short deployment inventory.
Determine:

* Linux distribution and version;
* available CPU, RAM, and disk;
* Docker installation and version;
* Docker Compose availability;
* existing containers;
* existing Docker networks;
* ports currently in use;
* existing reverse-proxy technology;
* reverse-proxy configuration location;
* existing virtual hosts/domains;
* existing TLS/certificate management;
* firewall configuration;
* application deployment directories;
* existing conventions used by other applications on this server.

Do not modify anything during this inspection.
Explicitly identify which ports can safely be used for SafetyMAIN internally.
Prefer localhost-only bindings for application services.
2. Obtain the Correct SafetyMAIN Source
Repository:

```
https://github.com/dvotapi/SafetyMAIN
```

Deploy the approved current release branch.
Preferred deployment source:

```
main
```

However, before deployment verify that `main` contains the completed P9-007 Risk Control Management UI.
If PR #1 has not yet been merged, STOP and report:

```
P9-007 is not present in main.
Deployment should not continue from an outdated main branch.
```

Do not silently deploy an old version.
Do not automatically merge GitHub branches unless explicitly authorized.
Record the exact Git commit SHA being deployed.
3. Review Existing Project Deployment State
Inspect the repository before creating deployment files.
Pay particular attention to:

```
README.md
.env.example
frontend/.env.example
docs/architecture/ProductionSecurityConfiguration.md
docker-compose.yml
pyproject.toml
frontend/package.json
alembic.ini
backend/
frontend/
infrastructure/
.github/workflows/
```

Determine:

* backend startup entry point;
* backend Python dependency/install strategy;
* frontend build/start strategy;
* current environment variables;
* database configuration;
* Alembic migration flow;
* authentication requirements;
* existing health endpoints;
* whether Dockerfiles already exist;
* whether production Compose definitions already exist.

Do not assume the root `docker-compose.yml` is the production application deployment.
The existing development Compose configuration may be PostgreSQL-only.
4. Production Deployment Architecture
Use Docker for SafetyMAIN application services.
Target:

```
Application VDS

/srv/safetymain/
    │
    ├── source or deployment metadata
    ├── production environment/secrets
    └── Docker Compose deployment

Docker:
    safetymain-backend
    safetymain-frontend
```

PostgreSQL runs on the separate database server and must NOT be added to this Compose stack.
The production application stack should conceptually be:

```
safetymain-frontend
        │
        │ HTTP
        ▼
Existing Reverse Proxy

safetymain-backend
        │
        │ PostgreSQL connection
        ▼
Dedicated Database Server
```

Use explicit container restart policies so the application returns automatically after VDS reboot.
5. Create Production Dockerization If Missing
If production Dockerfiles do not exist, create them.
Backend
Create a production backend image that:

* uses the project's supported Python version;
* installs only required dependencies;
* copies the application code;
* runs as a non-root user where practical;
* does not contain `.env` files or production secrets;
* exposes only the internal backend application port;
* starts the actual FastAPI application using the project's real application entry point;
* produces useful startup logs;
* supports graceful shutdown.

Do not invent a new backend architecture.
Determine the correct FastAPI application entry point from the repository.
Frontend
Create a production frontend image that:

* uses the supported Node version;
* performs deterministic dependency installation;
* builds design tokens before/through the production build;
* performs the Next.js production build;
* runs the production Next.js server;
* does not include production secrets in public variables;
* runs only the minimum required runtime content where practical.

Inspect the Next.js configuration.
If `output: "standalone"` is already supported, use it.
If it is not configured, determine whether enabling standalone output is a safe deployment-only improvement. Do not change application behavior merely for convenience.
6. Create a Production Compose Definition
Create a production deployment definition under a clear deployment/infrastructure location.
Prefer a structure such as:

```
infrastructure/
└── production/
    ├── compose.yml
    ├── .env.example
    └── README.md
```

or follow an already established repository convention if one exists.
The production Compose stack should contain only application-server services required here.
At minimum:

```
backend
frontend
```

Do NOT include PostgreSQL.
Requirements:

* unique container names;
* clear restart policies;
* isolated Docker network where appropriate;
* localhost-only host port bindings if the reverse proxy runs on the host;
* no unnecessary privileged mode;
* no Docker socket mounting;
* no production secrets embedded directly in Compose;
* health checks where technically appropriate.

7. Backend Production Environment
Create the production backend runtime configuration outside Git.
SafetyMAIN production security requirements must be respected.
Configure at minimum the actual project equivalents of:

```
APP_ENV=production
AUTH_ENFORCEMENT=true

DATABASE_URL=<production PostgreSQL connection>

JWT_SECRET_KEY=<strong production secret>
JWT_ALGORITHM=HS256
JWT_ISSUER=<stable production issuer>

JWT_ACCESS_TOKEN_TTL_SECONDS=<valid value>
JWT_REFRESH_TOKEN_TTL_SECONDS=<valid value>
```

Use the exact names and validation rules implemented by the project.
Generate a cryptographically strong production JWT secret.
Do not reuse:

```
secret
changeme
development
dev-secret
test-secret
dev-insecure-change-me
```

or any development/test value.
Do not print the JWT secret in the final report.
Do not commit it.
The production database credential must also stay outside Git.
8. Database Connectivity
The PostgreSQL database is already hosted on a separate database server.
Before running migrations, verify from the application VDS:

```
Application VDS
      ↓
Database network address
      ↓
PostgreSQL
      ↓
SafetyMAIN database
```

Confirm:

* network connectivity;
* PostgreSQL port reachability;
* authentication;
* correct database;
* correct SafetyMAIN database user;
* required schema/migration permissions.

Do not change the database-server firewall unless necessary and explicitly understood.
If connectivity fails, identify whether the cause is:

```
network
firewall
PostgreSQL pg_hba
credentials
database name
DNS/IP
TLS configuration
```

and report it before making broad security changes.
9. Run Database Migrations
Do not manually create SafetyMAIN tables.
Use the repository's Alembic migration chain.
Before application startup:

```
Verify database connection
        ↓
Run Alembic migration to current head
        ↓
Verify Alembic head
        ↓
Start backend
```

If migration fails:
STOP.
Do not start a backend against a partially migrated production schema.
Report:

* failing migration;
* error;
* current database revision;
* expected head.

Do not downgrade or reset the production database automatically.
10. Frontend Production Environment
The frontend currently expects environment-specific application and API URLs.
Configure production equivalents of:

```
NEXT_PUBLIC_APP_URL
NEXT_PUBLIC_API_BASE_URL
NEXT_PUBLIC_APP_ENV
```

Use the final public SafetyMAIN URL.
Prefer routing the API through the same public origin where practical:

```
https://<SafetyMAIN-domain>/api/...
```

rather than exposing the backend on another public port.
Do not place secrets into any `NEXT_PUBLIC_*` variable.
Anything under `NEXT_PUBLIC_*` must be assumed visible to browser users.
11. Reverse Proxy Integration
The server already has a reverse proxy.
Do NOT replace it.
Inspect its existing configuration and add a dedicated SafetyMAIN virtual host using the same conventions.
Preferred public architecture:

```
https://<SafetyMAIN-domain>/
        │
        ├── /      → SafetyMAIN frontend
        │
        └── /api/  → SafetyMAIN backend
```

Prefer backend/frontend bindings such as:

```
127.0.0.1:<frontend-port>
127.0.0.1:<backend-port>
```

rather than:

```
0.0.0.0:<port>
```

unless the existing infrastructure requires another safe design.
Ensure that:

* unrelated virtual hosts remain unchanged;
* existing services continue working;
* proxy headers are correct;
* client IP/protocol forwarding follows existing server conventions;
* request sizes and timeouts are reasonable;
* websocket configuration is added only if actually required.

Validate reverse-proxy configuration before reloading it.
Reload rather than unnecessarily restarting the whole proxy service.
12. Domain and HTTPS
If a SafetyMAIN DNS name already points to the VDS:

* configure the virtual host;
* use the existing TLS management mechanism;
* obtain/attach a valid certificate;
* redirect HTTP to HTTPS.

If DNS is not yet configured:
do not invent a production domain.
Deploy the services internally, verify them locally, and report exactly which DNS record is required from the owner.
Do not disable TLS verification as a workaround.
13. Health Verification
Use the existing SafetyMAIN readiness endpoint where available.
Verify the backend readiness endpoint equivalent to:

```
/api/v1/ready
```

A successful deployment requires that readiness confirms database availability.
Verify separately:

```
Backend process healthy
Database reachable
Frontend responding
Reverse proxy responding
HTTPS responding
```

Do not declare deployment successful merely because Docker containers are in `running` state.
14. Authentication Verification
Production must run with:

```
AUTH_ENFORCEMENT=true
```

After deployment verify:

```
/login
```

and the authenticated application flow.
Confirm:

* unauthenticated protected routes redirect/deny correctly;
* login reaches the backend;
* valid production user can authenticate;
* `/api/v1/auth/session` works after authentication;
* active organization context works;
* Hazard pages load;
* Risk Assessment pages load;
* Risk Control pages load.

Do not seed fake development users into production unless explicitly authorized.
If no production administrator/user exists yet:
STOP at this step and report that production identity bootstrap is required.
Do not create undocumented production credentials.
15. Functional Smoke Test
Perform a non-destructive production smoke test.
At minimum verify:

```
Frontend opens
Login page works
Backend readiness works
Authentication works
Hazard Registry opens
Risk Assessment Registry opens
Risk Control Registry opens
Object pages load
Audit-backed Activity endpoints respond
```

Do not create, approve, archive, or mutate production safety records merely to test deployment unless a designated test organization/user exists.
16. Security Requirements
Verify before completion:

* backend port is not publicly exposed;
* frontend internal port is not unnecessarily exposed;
* database is not publicly exposed through this VDS;
* secrets are outside Git;
* JWT secret is production-grade;
* `APP_ENV=production`;
* `AUTH_ENFORCEMENT=true`;
* no dev credentials are present;
* no default PostgreSQL password is used by the application;
* containers do not run privileged;
* unnecessary ports are not opened;
* unrelated services remain intact.

Do not weaken firewall or reverse-proxy security to make deployment easier.
17. Persistence and Restart Test
Restart the SafetyMAIN application stack.
Verify it returns successfully.
If allowed operationally, verify behaviour after Docker daemon/server restart without disrupting unrelated services.
Confirm:

```
frontend returns
backend returns
database reconnects
readiness returns healthy
```

Do not reboot the entire VDS if that would disrupt unrelated production services without owner approval.
18. Logging
Ensure logs can be inspected for:

```
backend startup
backend application errors
frontend startup
reverse proxy errors
database connectivity errors
```

Avoid unbounded disk consumption.
Do not log:

```
JWT_SECRET_KEY
DATABASE_URL with password
access tokens
refresh tokens
passwords
```

19. Deployment Documentation
Create/update deployment documentation in the repository describing:

```
Application server architecture
Docker services
Internal ports
Reverse proxy routing
Required environment variable names
Database dependency
Migration procedure
Startup procedure
Shutdown procedure
Update procedure
Rollback procedure
Health checks
Log locations
Known limitations
```

Never commit real production secret values.
Provide `.env.example` using placeholders only.
20. Do Not Implement CI/CD Yet
This task is the first controlled application-server deployment.
Do not build a full CI/CD pipeline as part of this deployment unless it already exists and only needs safe integration.
First establish a known-good manual deployment procedure.
The next task will automate this deployment through CI/CD.
However, design the deployment files so that future CI/CD can execute the same process without redesign.
21. Final Deployment Report
At completion provide a concise report containing:

```
Deployed Git branch
Deployed Git commit SHA

Application directory

Frontend:
- container/service
- internal address/port
- health result

Backend:
- container/service
- internal address/port
- readiness result

Database:
- server/address WITHOUT credentials
- database name
- connectivity result
- Alembic revision

Reverse proxy:
- technology
- SafetyMAIN virtual host
- frontend upstream
- backend upstream

HTTPS:
- status

Authentication:
- enforcement status
- login smoke-test result

Smoke tests:
- Hazard UI
- Risk Assessment UI
- Risk Control UI

Existing services:
- confirmation they remained operational

Changes made:
- files/configs changed on VDS
- repository deployment files created

Remaining actions:
- anything requiring the owner
```

Never include secret values in the report.
Stop Conditions
STOP rather than improvising if any of the following occurs:

1. `main` does not contain the approved P9-007 implementation.
2. Database credentials are unavailable.
3. Application VDS cannot reach the database server.
4. Alembic migration fails.
5. Production security validation rejects configuration.
6. No safe unused internal ports are available.
7. Reverse-proxy changes would disrupt existing services.
8. DNS/domain information is required but unavailable.
9. TLS cannot be configured safely.
10. Production identity bootstrap is required but undefined.
11. Deployment would require deleting existing data.
12. Deployment would require modifying unrelated services.
13. A production secret would need to be committed to Git.

Report the exact blocker and wait for owner input.
Expected Outcome
The resulting architecture must be:

```
                      Internet
                          │
                        HTTPS
                          │
                Existing Reverse Proxy
                          │
               ┌──────────┴──────────┐
               │                     │
               ▼                     ▼
        SafetyMAIN Frontend    SafetyMAIN Backend
          Docker container      Docker container
                                     │
                                     │ protected DB connection
                                     ▼
                             PostgreSQL Server
                                SafetyMAIN DB
```

The deployment must be reproducible, documented, secure, and ready to become the target of a later CI/CD pipeline.