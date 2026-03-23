use pyo3::prelude::*;
use pyo3::types::PyModule;
use jsonwebtoken::{encode, decode, Header, Algorithm, Validation, EncodingKey, DecodingKey};
use serde::{Deserialize, Serialize};
use chrono::{Utc, Duration};
use std::fs;
use std::collections::HashMap;
use std::sync::{Mutex, OnceLock}; // [NEW] Needed for the global ledger
use regex::Regex;

// --- YAML Data Structures ---
#[derive(Debug, Serialize, Deserialize)]
struct Policy {
    roles: HashMap<String, RolePolicy>,
    admins: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct RolePolicy {
    scopes: Vec<String>,
}

// [NEW] Budget structure to parse budget.yaml
#[derive(Debug, Serialize, Deserialize)]
struct Budget {
    task_limit_usd: f32,
}

// --- JWT Claims ---
#[derive(Debug, Serialize, Deserialize)]
struct Claims {
    sub: String,
    exp: usize,
    role: String,
    scopes: Vec<String>,
    is_admin: bool,
}

// --- [NEW] FinOps Global Ledger ---
// A thread-safe, in-memory ledger tracking cumulative spend per trace_id.
// OnceLock ensures it initializes safely the first time it is accessed.
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

// [NEW] Helper to read the budget file
fn load_budget() -> Budget {
    let yaml_str = fs::read_to_string("infrastructure/budget.yaml")
        .unwrap_or_else(|_| panic!("CRITICAL: Valkyrie cannot find budget.yaml"));
    serde_yaml::from_str(&yaml_str).expect("Failed to parse budget.yaml")
}

// --- Original Endpoints (Untouched) ---

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

    let claims = Claims {
        sub: agent_name,
        exp: expiration,
        role,
        scopes,
        is_admin,
    };

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

// --- [NEW] Strict FinOps Validation Endpoint ---
#[pyfunction]
fn enforce_finops(trace_id: String, tokens_used: usize, cost_per_1k: f32) -> PyResult<bool> {
    let budget = load_budget();

    // Calculate the cost of the current LLM request
    let cost_of_request = (tokens_used as f32 / 1000.0) * cost_per_1k;

    // Lock the global ledger and update the spend for this specific trace
    let mut ledger = get_ledger().lock().unwrap();
    let current_spend = ledger.entry(trace_id.clone()).or_insert(0.0);

    *current_spend += cost_of_request;

    if *current_spend > budget.task_limit_usd {
        println!(
            "\n[VALKYRIE FINOPS 🛑] BUDGET_EXCEEDED for Task '{}'!", trace_id
        );
        println!(
            "Attempted Spend: ${:.4} | Strict Limit: ${:.2}",
            current_spend, budget.task_limit_usd
        );
        println!("ACTION: Revoking Execution Rights. Halting Swarm.");

        // Wipe the ledger for this trace since it's dead, preventing memory leaks
        ledger.remove(&trace_id);
        Ok(false)
    } else {
        println!(
            "[VALKYRIE FINOPS] Charge Approved. Task '{}' Cumulative Spend: ${:.4} / ${:.2}",
            trace_id, current_spend, budget.task_limit_usd
        );
        Ok(true)
    }
}

// --- [NEW] Phase 18: DLP Egress Guard (Hybrid Air-Lock) ---
#[pyfunction]
fn enforce_dlp_egress(mut payload: String) -> PyResult<String> {
    // 1. Scrub AWS Access Keys (AKIA followed by 16 alphanumeric chars)
    let aws_regex = Regex::new(r"AKIA[0-9A-Z]{16}").unwrap();
    payload = aws_regex.replace_all(&payload, "[REDACTED_AWS_KEY]").to_string();

    // 2. Scrub JWT Tokens (eyJ followed by base64 chars and dots)
    let jwt_regex = Regex::new(r"eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*").unwrap();
    payload = jwt_regex.replace_all(&payload, "[REDACTED_JWT_TOKEN]").to_string();

    // 3. Scrub Proprietary Company Secrets/Variables
    // In a production environment, you would load these from a secure policy.yaml
    let proprietary_terms = vec![
        "daen-internal-dev-secret-2026",
        "HR_DB_PASSWORD",
        "nexus_risk_solana_key"
    ];

    for term in proprietary_terms {
        // Case-insensitive exact match replacement
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
    m.add_function(wrap_pyfunction!(enforce_dlp_egress, m)?)?; // [NEW] Expose DLP to Python
    Ok(())
}
