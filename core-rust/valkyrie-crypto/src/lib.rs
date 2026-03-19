use pyo3::prelude::*;
use pyo3::types::PyModule;
use jsonwebtoken::{encode, decode, Header, Algorithm, Validation, EncodingKey, DecodingKey};
use serde::{Deserialize, Serialize};
use chrono::{Utc, Duration};
use std::fs;
use std::collections::HashMap;

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

// --- JWT Claims ---
#[derive(Debug, Serialize, Deserialize)]
struct Claims {
    sub: String,
    exp: usize,
    role: String,
    scopes: Vec<String>, // [NEW] Baked-in access control
    is_admin: bool,      // [NEW] Master override
}

// Helper to read the policy file
fn load_policy() -> Policy {
    let yaml_str = fs::read_to_string("infrastructure/policy.yaml")
        .unwrap_or_else(|_| panic!("CRITICAL: Valkyrie PDP Firewall cannot find policy.yaml"));
    serde_yaml::from_str(&yaml_str).expect("Failed to parse policy.yaml")
}

#[pyfunction]
fn forge_token(agent_name: String, role: String, secret: String) -> PyResult<String> {
    let policy = load_policy();

    // Evaluate Identity
    let is_admin = policy.admins.contains(&agent_name);

    // Map scopes based on role
    let scopes = if is_admin {
        vec!["*".to_string()] // Admins get wildcard access
    } else if let Some(role_policy) = policy.roles.get(&role) {
        role_policy.scopes.clone()
    } else {
        vec![] // Unknown roles get zero permissions
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

// Original validate function (keeps endpoints not yet upgraded working)
#[pyfunction]
fn validate_token(token: String, secret: String) -> PyResult<bool> {
    let mut validation = Validation::new(Algorithm::HS256);
    validation.validate_exp = true;

    match decode::<Claims>(&token, &DecodingKey::from_secret(secret.as_ref()), &validation) {
        Ok(_) => Ok(true),
        Err(_) => Ok(false),
    }
}

// [NEW] Strict RBAC Validation Endpoint
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

#[pymodule]
fn valkyrie_crypto(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(forge_token, m)?)?;
    m.add_function(wrap_pyfunction!(validate_token, m)?)?;
    m.add_function(wrap_pyfunction!(enforce_scope, m)?)?; // Expose new function
    Ok(())
}
