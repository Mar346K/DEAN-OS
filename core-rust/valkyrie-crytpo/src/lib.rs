use pyo3::prelude::*;
use pyo3::types::PyModule;
use jsonwebtoken::{encode, decode, Header, Algorithm, Validation, EncodingKey, DecodingKey};
use serde::{Deserialize, Serialize};
use chrono::{Utc, Duration};

#[derive(Debug, Serialize, Deserialize)]
struct Claims {
    sub: String, // Subject (e.g., "scout-agent")
    exp: usize,  // Expiration time
    role: String,
}

#[pyfunction]
fn forge_token(agent_name: String, role: String, secret: String) -> PyResult<String> {
    // Tokens expire exactly 60 minutes from creation
    let expiration = Utc::now()
        .checked_add_signed(Duration::try_minutes(60).unwrap())
        .expect("valid timestamp")
        .timestamp() as usize;

    let claims = Claims {
        sub: agent_name,
        exp: expiration,
        role,
    };

    let header = Header::new(Algorithm::HS256);
    let token = encode(&header, &claims, &EncodingKey::from_secret(secret.as_ref()))
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    Ok(token)
}

#[pyfunction]
fn validate_token(token: String, secret: String) -> PyResult<bool> {
    let mut validation = Validation::new(Algorithm::HS256);
    validation.validate_exp = true; // Automatically reject expired tokens

    match decode::<Claims>(&token, &DecodingKey::from_secret(secret.as_ref()), &validation) {
        Ok(_) => Ok(true),
        Err(_) => Ok(false),
    }
}

// Updated for PyO3 0.28.2 Bound API to support Python 3.13
#[pymodule]
fn valkyrie_crypto(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(forge_token, m)?)?;
    m.add_function(wrap_pyfunction!(validate_token, m)?)?;
    Ok(())
}
