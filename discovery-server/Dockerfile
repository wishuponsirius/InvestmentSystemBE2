# ── Stage 1: Build ──────────────────────────────────────────────────────────
FROM maven:3.9.6-eclipse-temurin-17 AS builder

WORKDIR /build

# Copy parent POM first (layer caching)
COPY pom.xml .
COPY discovery-server/pom.xml discovery-server/

# Download dependencies (cached unless pom changes)
RUN mvn dependency:go-offline -pl discovery-server -am -q

# Copy source and build
COPY discovery-server/src discovery-server/src
RUN mvn clean package -pl discovery-server -am -DskipTests -q

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM eclipse-temurin:17-jre-alpine

# Non-root user for security
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

WORKDIR /app

# Copy the built jar
COPY --from=builder /build/discovery-server/target/*.jar app.jar

# Expose Eureka port
EXPOSE 8761

# JVM tuning for containers
ENV JAVA_OPTS="-XX:+UseContainerSupport \
               -XX:MaxRAMPercentage=75.0 \
               -XX:+UseG1GC \
               -Djava.security.egd=file:/dev/./urandom"

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
