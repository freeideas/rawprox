use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

const BASE62_CHARS: &[u8] = b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";

pub struct ConnIdGenerator {
    counter: AtomicU64,
}

impl ConnIdGenerator {
    pub fn new() -> Self {
        // Initial value: last 5 base62 digits of Unix timestamp
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();

        ConnIdGenerator {
            counter: AtomicU64::new(now),
        }
    }

    pub fn next(&self) -> String {
        let value = self.counter.fetch_add(1, Ordering::SeqCst);
        encode_base62(value)
    }
}

fn encode_base62(mut value: u64) -> String {
    let mut result = Vec::new();

    // Generate all base62 digits
    if value == 0 {
        result.push(BASE62_CHARS[0]);
    } else {
        while value > 0 {
            result.push(BASE62_CHARS[(value % 62) as usize]);
            value /= 62;
        }
    }

    result.reverse();

    // Take only last 5 characters (or pad if less than 5)
    let s = String::from_utf8(result).unwrap();
    if s.len() > 5 {
        s.chars().skip(s.len() - 5).collect()
    } else {
        format!("{:0>5}", s)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_encode_base62() {
        assert_eq!(encode_base62(0), "00000");
        assert_eq!(encode_base62(1), "00001");
        assert_eq!(encode_base62(61), "0000z");
        assert_eq!(encode_base62(62), "00010");
    }
}
