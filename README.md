# Microservices Platform

Spring Boot microservices scaffold with **Eureka Discovery Server** and **API Gateway**.

---

## Architecture

```
Internet
    │
    ▼
┌─────────────┐        ┌──────────────────┐
│  API Gateway │◄──────►│ Discovery Server  │
│   :8080      │        │  (Eureka) :8761   │
└──────┬───────┘        └──────────────────┘
       │  lb:// routing                ▲
       ▼                               │ register
┌────────────┐  ┌────────────┐        │
│user-service│  │order-service│ ───────┘
│  (future)  │  │  (future)   │
└────────────┘  └────────────┘
```

---

## Spring Profiles

| Profile | When to use | Eureka URL |
|---|---|---|
| `local` | Running services directly on your machine | `localhost:8761` |
| `docker` | Running via Docker Compose (EC2 or local Docker) | `discovery-server:8761` |

Each service has three config files:
```
application.yml          ← shared, profile-agnostic settings
application-local.yml    ← local overrides (plain passwords, localhost URLs)
application-docker.yml   ← docker overrides (env vars, Docker service names)
```

---

## Quick Start — Local Dev (no Docker)

```bash
# Terminal 1 — start Eureka
mvn spring-boot:run -pl discovery-server -Dspring-boot.run.profiles=local

# Terminal 2 — start API Gateway
mvn spring-boot:run -pl api-gateway -Dspring-boot.run.profiles=local

# Eureka Dashboard → http://localhost:8761  (admin / admin)
# API Gateway      → http://localhost:8080
```

**Or in IntelliJ:** Edit Run Configuration → Spring Boot → Active Profiles = `local`

---

## Quick Start — Docker (local machine)

```bash
cp .env .env      # set credentials
docker compose up --build

# Eureka Dashboard → http://localhost:8761
# API Gateway      → http://localhost:8080
```

---

## Deploy to EC2

### Prerequisites
- EC2 instance (t3.small or larger recommended)
- Docker + Docker Compose installed
- Ports 8080 and 8761 open in Security Group

### Steps

```bash
# Copy project files to EC2
scp -r . ec2-user@<your-ec2-ip>:~/microservices-project
ssh ec2-user@<your-ec2-ip>
cd ~/microservices-project

# Configure environment
cp .env .env
nano .env    # set real passwords, SPRING_PROFILES_ACTIVE=docker

# Start
docker compose up -d
docker compose ps
docker compose logs -f
```

---

## Adding a New Microservice

1. Create a new Maven module under the parent
2. Add Eureka client dependency:
   ```xml
   <dependency>
       <groupId>org.springframework.cloud</groupId>
       <artifactId>spring-cloud-starter-netflix-eureka-client</artifactId>
   </dependency>
   ```
3. Add three config files mirroring the api-gateway pattern:
   - `application.yml` — shared settings
   - `application-local.yml` — `defaultZone: http://admin:admin@localhost:8761/eureka/`
   - `application-docker.yml` — `defaultZone: http://${EUREKA_USERNAME}:${EUREKA_PASSWORD}@discovery-server:8761/eureka/`
4. Uncomment / add a route in both `application-local.yml` and `application-docker.yml` of the api-gateway
5. Copy the service template block in `docker-compose.yml`

---

## Module Overview

| Module | Port | Purpose |
|---|---|---|
| `discovery-server` | 8761 | Eureka service registry & dashboard |
| `api-gateway` | 8080 | Single entry point, load-balanced routing |

---

## Useful Commands

```bash
# Local — run a single service with a profile
mvn spring-boot:run -pl discovery-server -Dspring-boot.run.profiles=local

# Docker — view logs
docker compose logs -f

# Docker — restart a single service
docker compose restart api-gateway

# Docker — tear down
docker compose down
```
