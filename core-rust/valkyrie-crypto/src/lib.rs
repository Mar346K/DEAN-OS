use pyo3::prelude::*;
use pyo3::types::PyModule;
use jsonwebtoken::{encode, decode, Header, Algorithm, Validation, EncodingKey, DecodingKey};
use serde::{Deserialize, Serialize};
use chrono::{Utc, Duration};
use std::fs;
use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};
use regex::Regex;

// --- [NEW] Vault Cryptography Imports ---
use aes_gcm::{
    aead::{Aead, AeadCore, KeyInit, OsRng},
    Aes256Gcm, Key, Nonce,
};
use sha2::{Sha256, Digest};

// --- Data Structures ---
#[derive(Debug, Serialize, Deserialize)]
struct Policy {
    roles: HashMap<String, RolePolicy>,
    admins: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct RolePolicy {
    scopes: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct Budget {
    task_limit_usd: f32,
}

#[derive(Debug, Serialize, Deserialize)]
struct Claims {
    sub: String,
    exp: usize,
    role: String,
    scopes: Vec<String>,
    is_admin: bool,
}

// --- FinOps Global Ledger ---
static LEDGER: OnceLock<Mutex<HashMap<String, f32>>> = OnceLock::new();

fn get_ledger() -> &'static Mutex<HashMap<String, f32>> {
    LEDGER.get_or_init(|| Mutex::new(HashMap::new()))
}

// --- Helpers ---
fn load_policy() -> Policy {
    let yaml_str = fs::read_to_string("infrastructure/policy.yaml")
        .unwrap_or_else(|_| panic!("CRITICAL: Valkyrie PDP Firewall cannot find policy.yaml"));
    serde_yaml::from_str(&yaml_str).expect("Failed to parse policy.yaml")
}

fn load_budget() -> Budget {
    let yaml_str = fs::read_to_string("infrastructure/budget.yaml")
        .unwrap_or_else(|_| panic!("CRITICAL: Valkyrie cannot find budget.yaml"));
    serde_yaml::from_str(&yaml_str).expect("Failed to parse budget.yaml")
}

// --- PHASE 4: ZERO-KNOWLEDGE VAULT (AES-256-GCM) ---

const VAULT_PATH: &str = "infrastructure/.vault.json";

// Helper to derive a perfect 32-byte AES key from your variable-length DAEN secret
fn derive_master_key(secret: &str) -> Key<Aes256Gcm> {
    let mut hasher = Sha256::new();
    hasher.update(secret.as_bytes());
    let result = hasher.finalize();
    *Key::<Aes256Gcm>::from_slice(&result)
}

#[pyfunction]
fn seal_key(key_id: String, plaintext_api_key: String, master_secret: String) -> PyResult<bool> {
    let key = derive_master_key(&master_secret);
    let cipher = Aes256Gcm::new(&key);
    let nonce = Aes256Gcm::generate_nonce(&mut OsRng); // 96-bits; unique per encryption

    // Encrypt the API key
    let ciphertext = match cipher.encrypt(&nonce, plaintext_api_key.as_bytes()) {
        Ok(ct) => ct,
        Err(_) => return Ok(false),
    };

    // Combine nonce + ciphertext and encode as hex for safe JSON storage
    let mut combined = nonce.to_vec();
    combined.extend_from_slice(&ciphertext);
    let hex_payload = hex::encode(combined);

    // Read existing vault or create new
    let mut vault: HashMap<String, String> = match fs::read_to_string(VAULT_PATH) {
        Ok(data) => serde_json::from_str(&data).unwrap_or_else(|_| HashMap::new()),
        Err(_) => HashMap::new(),
    };

    // Store and save
    vault.insert(key_id.clone(), hex_payload);
    let json_data = serde_json::to_string_pretty(&vault).unwrap();

    match fs::write(VAULT_PATH, json_data) {
        Ok(_) => {
            println!("[VALKYRIE VAULT] 🔒 Key '{}' sealed and encrypted securely.", key_id);
            Ok(true)
        },
        Err(_) => Ok(false)
    }
}

#[pyfunction]
fn unseal_key(key_id: String, master_secret: String) -> PyResult<Option<String>> {
    // Read the vault
    let vault: HashMap<String, String> = match fs::read_to_string(VAULT_PATH) {
        Ok(data) => serde_json::from_str(&data).unwrap_or_else(|_| HashMap::new()),
        Err(_) => return Ok(None),
    };

    // Find the hex payload
    let hex_payload = match vault.get(&key_id) {
        Some(val) => val,
        None => return Ok(None),
    };

    // Decode hex
    let combined = match hex::decode(hex_payload) {
        Ok(bytes) => bytes,
        Err(_) => return Ok(None),
    };

    if combined.len() < 12 { return Ok(None); }

    // Split nonce and ciphertext
    let (nonce_bytes, ciphertext) = combined.split_at(12);
    let nonce = Nonce::from_slice(nonce_bytes);

    // Decrypt
    let key = derive_master_key(&master_secret);
    let cipher = Aes256Gcm::new(&key);

    match cipher.decrypt(nonce, ciphertext) {
        Ok(plaintext_bytes) => {
            println!("[VALKYRIE VAULT] 🔓 Key '{}' unsealed for execution.", key_id);
            Ok(Some(String::from_utf8(plaintext_bytes).unwrap()))
        },
        Err(_) => {
            println!("[VALKYRIE VAULT] 🛑 DECRYPTION FAILED for '{}'. Tampering detected or wrong master secret!", key_id);
            Ok(None)
        }
    }
}

// --- Original Endpoints ---

#[pyfunction]
fn forge_token(agent_name: String, role: String, secret: String) -> PyResult<String> {
    let policy = load_policy();
    let is_admin = policy.admins.contains(&agent_name);
    let scopes = if is_admin {
        vec!["*".to_string()]
    } else if let Some(role_policy) = policy.roles.get(&role) {
        role_policy.scopes.clone()
    } else {
        vec![]
    };

    let expiration = Utc::now()
        .checked_add_signed(Duration::try_minutes(60).unwrap())
        .expect("valid timestamp")
        .timestamp() as usize;

    let claims = Claims { sub: agent_name, exp: expiration, role, scopes, is_admin };
    let header = Header::new(Algorithm::HS256);
    let token = encode(&header, &claims, &EncodingKey::from_secret(secret.as_ref()))
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(token)
}

#[pyfunction]
fn validate_token(token: String, secret: String) -> PyResult<bool> {
    let mut validation = Validation::new(Algorithm::HS256);
    validation.validate_exp = true;
    match decode::<Claims>(&token, &DecodingKey::from_secret(secret.as_ref()), &validation) {
        Ok(_) => Ok(true),
        Err(_) => Ok(false),
    }
}

#[pyfunction]
fn enforce_scope(token: String, secret: String, required_scope: String) -> PyResult<bool> {
    let mut validation = Validation::new(Algorithm::HS256);
    validation.validate_exp = true;
    match decode::<Claims>(&token, &DecodingKey::from_secret(secret.as_ref()), &validation) {
        Ok(token_data) => {
            let claims = token_data.claims;
            if claims.is_admin || claims.scopes.contains(&required_scope) || claims.scopes.contains(&"*".to_string()) {
                Ok(true)
            } else {
                println!("[VALKYRIE FIREWALL] 🛑 Identity '{}' (Role: {}) blocked. Missing scope: '{}'", claims.sub, claims.role, required_scope);
                Ok(false)
            }
        },
        Err(_) => Ok(false),
    }
}

#[pyfunction]
fn enforce_finops(trace_id: String, tokens_used: usize, cost_per_1k: f32) -> PyResult<bool> {
    let budget = load_budget();
    let cost_of_request = (tokens_used as f32 / 1000.0) * cost_per_1k;

    let mut ledger = get_ledger().lock().unwrap();
    let current_spend = ledger.entry(trace_id.clone()).or_insert(0.0);
    *current_spend += cost_of_request;

    if *current_spend > budget.task_limit_usd {
        println!("\n[VALKYRIE FINOPS 🛑] BUDGET_EXCEEDED for Task '{}'!", trace_id);
        println!("Attempted Spend: ${:.4} | Strict Limit: ${:.2}", current_spend, budget.task_limit_usd);
        println!("ACTION: Revoking Execution Rights. Halting Swarm.");
        ledger.remove(&trace_id);
        Ok(false)
    } else {
        println!("[VALKYRIE FINOPS] Charge Approved. Task '{}' Cumulative Spend: ${:.4} / ${:.2}", trace_id, current_spend, budget.task_limit_usd);
        Ok(true)
    }
}

#[pyfunction]
fn enforce_dlp_egress(mut payload: String) -> PyResult<String> {
    let aws_regex = Regex::new(r"AKIA[0-9A-Z]{16}").unwrap();
    payload = aws_regex.replace_all(&payload, "[REDACTED_AWS_KEY]").to_string();

    let jwt_regex = Regex::new(r"eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*").unwrap();
    payload = jwt_regex.replace_all(&payload, "[REDACTED_JWT_TOKEN]").to_string();

    let proprietary_terms = vec![
        "daen-internal-dev-secret-2026",
        "HR_DB_PASSWORD",
        "nexus_risk_solana_key"
    ];

    for term in proprietary_terms {
        payload = payload.replace(term, "[REDACTED_PROPRIETARY_SECRET]");
    }
    Ok(payload)
}

#[pymodule]
fn valkyrie_crypto(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(forge_token, m)?)?;
    m.add_function(wrap_pyfunction!(validate_token, m)?)?;
    m.add_function(wrap_pyfunction!(enforce_scope, m)?)?;
    m.add_function(wrap_pyfunction!(enforce_finops, m)?)?;
    m.add_function(wrap_pyfunction!(enforce_dlp_egress, m)?)?;
    // [NEW] Expose the Vault functions to Python
    m.add_function(wrap_pyfunction!(seal_key, m)?)?;
    m.add_function(wrap_pyfunction!(unseal_key, m)?)?;
    Ok(())
}
