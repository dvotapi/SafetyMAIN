# TASK — SafetyMAIN Database Server Deployment

---

## Goal

Prepare the dedicated database server for SafetyMAIN and deploy a production-ready PostgreSQL instance that will be used by the SafetyMAIN application running on a separate application server.

The database server must be isolated from public access, reachable only from approved infrastructure, securely configured, persistent, backed up, and ready for later application deployment.

---

## Context

SafetyMAIN will use a two-server architecture:

```text
Internet
   ↓
Application Server
├── Reverse Proxy
├── SafetyMAIN Frontend
└── SafetyMAIN Backend
         ↓
   Private network
         ↓
Database Server
└── PostgreSQL
```

The application server already hosts other services and already has a reverse proxy.

The database server is dedicated to database workloads.

SafetyMAIN uses PostgreSQL as its production database.

The application server and database server must communicate over a trusted private network or another protected network path.

The PostgreSQL database must not be exposed directly to the public Internet.

---

## Scope

### 1. Verify Database Server Environment

Before deployment, inspect the database server and document:

- operating system and version;
- CPU;
- available RAM;
- disk capacity;
- disk layout;
- filesystem;
- existing PostgreSQL installations;
- existing database services;
- Docker availability if containers are already used;
- firewall configuration;
- private network interfaces;
- server hostname;
- application-server IP address;
- backup storage location;
- available monitoring facilities.

Do not modify unrelated services.

---

### 2. Define PostgreSQL Deployment Model

Determine how PostgreSQL should run on the database server.

Prefer consistency with the existing server-management strategy.

The selected architecture must clearly define:

```text
PostgreSQL runtime
Persistent database storage
Configuration storage
Backup storage
Logs
Network access
Upgrade procedure
Recovery procedure
```

PostgreSQL may run directly on the host or inside a container, depending on the existing infrastructure conventions.

The important requirement is not the runtime method itself, but predictable persistence, backup, security, maintenance, and recovery.

Document the selected deployment model.

---

### 3. Install and Configure PostgreSQL

Deploy a supported PostgreSQL version suitable for SafetyMAIN.

The installation must provide:

- automatic startup after server reboot;
- persistent data storage;
- predictable configuration;
- database logging;
- controlled network binding;
- sufficient connection capacity for the SafetyMAIN backend;
- UTF-8 database encoding;
- correct timezone handling;
- reliable restart behavior.

Do not expose PostgreSQL on unnecessary interfaces.

---

### 4. Network Architecture

PostgreSQL must accept connections only from trusted infrastructure.

The expected network path is:

```text
SafetyMAIN Backend
      ↓
Application Server
      ↓
Private / protected network
      ↓
PostgreSQL
```

The database must not be reachable directly from the public Internet.

Configure firewall and PostgreSQL access rules so that:

- the application server can connect;
- localhost/database-server administration can connect where required;
- arbitrary external hosts cannot connect;
- unrelated servers cannot connect unless explicitly approved.

Prefer the private IP address of the application server rather than unrestricted network ranges.

---

### 5. Create SafetyMAIN Database

Create a dedicated production database for SafetyMAIN.

The database must be logically separated from other applications.

Use an explicit database name following the infrastructure naming convention.

Conceptually:

```text
PostgreSQL
├── other_application_db
├── another_service_db
└── safetymain
```

SafetyMAIN must not share an application database with unrelated services.

---

### 6. Create Dedicated Database User

Create a dedicated PostgreSQL user/service account for SafetyMAIN.

The SafetyMAIN backend must not connect using:

```text
postgres
```

or another administrator/superuser account.

The application account should have only the permissions necessary to operate the SafetyMAIN database.

Administrative and application identities must remain separate.

Conceptually:

```text
PostgreSQL administrator
    ↓
administration only

SafetyMAIN service user
    ↓
SafetyMAIN database only
```

Use a strong unique credential.

Do not reuse credentials from other applications.

---

### 7. Database Ownership and Permissions

Configure ownership and privileges so that the SafetyMAIN application account can:

- connect to the SafetyMAIN database;
- use the required schema;
- create and modify application tables through Alembic migrations;
- read and write application data;
- create required indexes and constraints.

The account must not receive unnecessary rights over:

- other databases;
- unrelated schemas;
- server administration;
- PostgreSQL user management;
- system configuration.

Apply the principle of least privilege.

---

### 8. Connection Security

Define how the application server connects to PostgreSQL.

The configuration must specify:

```text
Database host
Database port
Database name
Service user
Authentication method
Transport security
```

If traffic crosses anything other than a trusted isolated private network, enable encrypted database connections.

Even when private networking is used, the architecture should remain compatible with TLS later.

Do not place production database credentials in the Git repository.

---

### 9. Secrets Management

Store the SafetyMAIN database credential outside source control.

The application server will later receive a production connection secret containing the required database parameters.

Production secrets must be separate from:

- development;
- testing;
- staging.

Do not reuse local development credentials in production.

Document:

- where the production database credential is stored;
- who can access it;
- how it can be rotated.

Do not include the actual password in project documentation.

---

### 10. Persistent Storage

Database data must survive:

- PostgreSQL restart;
- service restart;
- server reboot;
- application deployment;
- application container replacement.

Clearly identify the PostgreSQL persistent data location.

Database data must not reside only inside an ephemeral container filesystem.

Document:

```text
Data location
Expected capacity
Current free space
Expansion strategy
```

---

### 11. Backup Architecture

Configure automated PostgreSQL backups.

The backup design must define:

- backup frequency;
- retention period;
- backup location;
- backup naming;
- backup failure detection;
- cleanup policy.

At minimum, maintain regular backups sufficient to recover SafetyMAIN after:

- accidental data deletion;
- failed migration;
- database corruption;
- application deployment failure;
- server failure.

Backups should preferably be stored independently from the live PostgreSQL data directory.

A backup located only on the same failed disk is not sufficient as the final production strategy.

---

### 12. Restore Verification

A backup is not considered production-ready until restore has been verified.

Perform a controlled restore test into a separate test database or isolated PostgreSQL environment.

Verify that:

```text
Backup
   ↓
Restore
   ↓
Database starts
   ↓
Schema exists
   ↓
Application data is readable
```

Document the restore procedure.

The production SafetyMAIN database must not be overwritten during the restore test.

---

### 13. Migration Readiness

Prepare the database for SafetyMAIN Alembic migrations.

The expected deployment sequence later will be:

```text
Application release prepared
        ↓
Database backup
        ↓
Alembic migration
        ↓
Backend startup
        ↓
Health verification
```

Confirm that the SafetyMAIN application database user has sufficient rights to execute the existing migrations.

Do not manually recreate the SafetyMAIN schema if Alembic already owns schema creation.

The database server provides PostgreSQL.

The application repository remains the authority for SafetyMAIN schema migrations.

---

### 14. Initial Migration Test

After network connectivity from the application environment becomes available, verify that the current SafetyMAIN migration chain can initialize an empty production-style database.

Expected result:

```text
Empty SafetyMAIN database
        ↓
Alembic upgrade to head
        ↓
Current schema created
        ↓
Alembic reports expected head
```

The current project migration chain must be used rather than manually creating application tables.

Any migration failure must be resolved before production application deployment.

---

### 15. Connectivity Test

Verify connection from the application server to the database server.

Test:

```text
Application Server
       ↓
SafetyMAIN DB user
       ↓
Database Server
       ↓
SafetyMAIN database
```

Confirm:

- DNS or IP resolution;
- network reachability;
- PostgreSQL authentication;
- database selection;
- required permissions.

Also confirm that an unauthorized external machine cannot connect.

---

### 16. Database Health

Define basic database health indicators.

At minimum monitor or make observable:

- PostgreSQL service state;
- successful startup;
- connection availability;
- disk space;
- database size;
- active connections;
- failed authentication attempts where available;
- backup success/failure.

The initial implementation does not require a full observability platform, but database failure must not remain invisible.

---

### 17. Logging

Configure PostgreSQL logging appropriate for production operation.

Logs must support investigation of:

- startup failures;
- authentication failures;
- connection problems;
- database errors;
- unexpected shutdowns;
- migration failures.

Avoid excessive logging of sensitive application data.

Define a log-retention strategy so database logs cannot fill the server disk indefinitely.

---

### 18. Resource Limits and Capacity

Review database-server capacity.

Document:

```text
Total RAM
Expected PostgreSQL allocation
Total storage
Available storage
Expected SafetyMAIN database growth
Backup storage requirements
```

Do not aggressively tune PostgreSQL without evidence.

Start with conservative production settings and leave room for:

- OS;
- PostgreSQL;
- backups;
- maintenance operations;
- future growth.

---

### 19. Server Restart Verification

Reboot or otherwise perform an approved restart test.

Verify:

```text
Database Server starts
        ↓
PostgreSQL starts automatically
        ↓
SafetyMAIN database mounts correctly
        ↓
Application user can connect
        ↓
Data remains intact
```

Database deployment is not complete until restart persistence is confirmed.

---

### 20. Security Review

Verify:

- PostgreSQL is not publicly exposed;
- administrator credentials are not used by the application;
- the SafetyMAIN account is database-scoped;
- strong authentication is enabled;
- production credentials are outside Git;
- firewall rules are restrictive;
- PostgreSQL host-access rules are restrictive;
- unrelated applications cannot use the SafetyMAIN credentials;
- unnecessary default accounts or unsafe access rules are not present.

Document any exceptions.

---

### 21. Documentation

Create infrastructure documentation describing:

```text
Database server
PostgreSQL deployment model
PostgreSQL version
SafetyMAIN database name
SafetyMAIN service-user name
Network architecture
Allowed application-server address
Persistent storage location
Backup location
Backup policy
Restore procedure
Migration procedure
Monitoring procedure
Restart procedure
Credential rotation procedure
```

Do not put secrets into the documentation.

---

## Acceptance Criteria

The database-server task is complete when:

1. PostgreSQL is deployed on the dedicated database server.

2. PostgreSQL starts automatically after reboot.

3. PostgreSQL storage is persistent.

4. A dedicated SafetyMAIN database exists.

5. A dedicated SafetyMAIN database service user exists.

6. The SafetyMAIN application does not use a PostgreSQL superuser.

7. The application user has only required privileges.

8. PostgreSQL is not publicly accessible.

9. The application server is allowed to connect.

10. Unapproved external hosts cannot connect.

11. Production credentials are not stored in Git.

12. Database connection parameters are ready for application-server configuration.

13. Automated backup is configured.

14. Backup retention is defined.

15. Backup failures can be detected.

16. A restore test has been successfully completed.

17. Database logs are available.

18. Log retention is controlled.

19. Disk-space monitoring is available or documented.

20. PostgreSQL health can be checked.

21. Current SafetyMAIN Alembic migrations can run against the database.

22. The schema can be created from an empty database through Alembic.

23. Database connectivity from the application server is verified.

24. Cross-network access restrictions are verified.

25. Server restart persistence is verified.

26. Database architecture and recovery procedures are documented.

---

## Non-Goals

This task does not deploy:

- SafetyMAIN backend;
- SafetyMAIN frontend;
- reverse proxy configuration;
- public domain;
- HTTPS certificates;
- CI/CD;
- Docker registry;
- application server;
- Redis;
- MinIO;
- background workers;
- monitoring platform;
- Kubernetes.

Those belong to subsequent deployment tasks.

---

## Expected Outcome

The infrastructure state after this task is:

```text
Application Server
        │
        │ approved private connection
        ▼
┌─────────────────────────┐
│    Database Server      │
│                         │
│   PostgreSQL            │
│       │                 │
│       └── safetymain    │
│                         │
│   persistent storage    │
│   automated backups     │
│   restricted firewall   │
│   database monitoring   │
└─────────────────────────┘
```

The database layer is production-ready and independent from the future application deployment.

The next deployment task can then focus on:

```text
SafetyMAIN Backend
SafetyMAIN Frontend
Application Server
Reverse Proxy integration
Environment configuration
Database connection
Health checks
```

without needing to redesign the database infrastructure.