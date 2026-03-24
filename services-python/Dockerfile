# --- STAGE 1: Rust Valkyrie Compiler ---
FROM python:3.11-slim as builder

# Install Rust, Cargo, and Maturin dependencies
RUN apt-get update && apt-get install -y curl build-essential
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /build
# Install the tool that bridges Python and Rust
RUN pip install maturin

# Copy the Rust crypto module from the root context
COPY core-rust/valkyrie-crypto ./valkyrie-crypto

# Compile the Python wheel
WORKDIR /build/valkyrie-crypto
RUN maturin build --release --out /wheels


# --- STAGE 2: Production Python Runtime ---
FROM python:3.11-slim

WORKDIR /app

# Copy the compiled Valkyrie Crypto wheel from Stage 1
COPY --from=builder /wheels /wheels
# Install the custom Rust wheel into Python
RUN pip install /wheels/*.whl

# Install the rest of the standard Python dependencies
COPY services-python/requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy the microservice code
COPY services-python/ .

# We do not define a CMD here because docker-compose.yml
# overrides it to run api, mnemosyne, or oubliette independently!
