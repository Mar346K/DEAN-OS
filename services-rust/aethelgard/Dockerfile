# --- STAGE 1: The Builder ---
FROM rust:slim-bookworm as builder

WORKDIR /usr/src/aethelgard

# Install system C-libraries required for compiling GPU/hardware metrics
RUN apt-get update && apt-get install -y pkg-config libssl-dev libdrm-dev

# Copy the source and compile
COPY . .
RUN cargo build --release

# --- STAGE 2: The Production Runtime ---
FROM debian:bookworm-slim

# Install runtime dependencies
# We add libdrm-amdgpu1 and libdrm-intel1 to satisfy the binary's linking requirements
RUN apt-get update && apt-get install -y \
    libssl-dev \
    sysstat \
    libdrm2 \
    libdrm-amdgpu1 \
    libdrm-intel1 \
    && rm -rf /var/lib/apt/lists/*

# Copy ONLY the compiled binary
COPY --from=builder /usr/src/aethelgard/target/release/aethelgard /usr/local/bin/aethelgard

# Expose the hardware telemetry port
EXPOSE 8003

# Run the binary
CMD ["aethelgard"]
