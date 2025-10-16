/// Encode data field according to SPECIFICATION.md §5
///
/// Returns a String where:
/// - JSON-escapable characters (§5.1.1) are returned as actual characters (serde_json will escape them)
/// - Percent and other non-JSON-escapable bytes (§5.1.2) are percent-encoded
/// - Printable ASCII (§5.1.3) is preserved as-is
pub fn encode_data(data: &[u8]) -> String {
    let mut result = String::with_capacity(data.len());

    for &byte in data {
        match byte {
            // JSON escape sequences (§5.1.1) - return actual characters, serde_json will escape
            b'"' => result.push('"'),
            b'\\' => result.push('\\'),
            b'\n' => result.push('\n'),
            b'\r' => result.push('\r'),
            b'\t' => result.push('\t'),
            0x08 => result.push('\x08'), // backspace
            0x0C => result.push('\x0C'), // form feed

            // Percent character (meta-character, §5.1.2)
            b'%' => result.push_str("%25"),

            // Other control characters (§5.1.2)
            0x00..=0x07 | 0x0B | 0x0E..=0x1F | 0x7F => {
                result.push_str(&format!("%{:02X}", byte));
            }

            // Non-ASCII bytes (§5.1.2)
            0x80..=0xFF => {
                result.push_str(&format!("%{:02X}", byte));
            }

            // Printable ASCII (§5.1.3) - preserved as-is
            0x20..=0x7E => {
                result.push(byte as char);
            }
        }
    }

    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_printable_ascii() {
        assert_eq!(encode_data(b"Hello World"), "Hello World");
    }

    #[test]
    fn test_json_escapes() {
        // Returns actual characters, serde_json will escape them
        assert_eq!(encode_data(b"Line1\nLine2"), "Line1\nLine2");
        assert_eq!(encode_data(b"\r\n"), "\r\n");
        assert_eq!(encode_data(b"Tab\there"), "Tab\there");
        assert_eq!(encode_data(b"Say \"Hi\""), "Say \"Hi\"");
        assert_eq!(encode_data(b"Path\\to\\file"), "Path\\to\\file");
        assert_eq!(encode_data(b"\x08\x0C"), "\x08\x0C");
    }

    #[test]
    fn test_percent_encoding() {
        assert_eq!(encode_data(b"100%"), "100%25");
        assert_eq!(encode_data(b"50% off\n"), "50%25 off\\n");
    }

    #[test]
    fn test_control_chars() {
        assert_eq!(encode_data(b"\x00"), "%00");
        assert_eq!(encode_data(b"\x01\x02"), "%01%02");
        assert_eq!(encode_data(b"\x7F"), "%7F");
    }

    #[test]
    fn test_non_ascii() {
        assert_eq!(encode_data(b"\x89PNG"), "%89PNG");
        assert_eq!(encode_data(b"\xFF\xFE"), "%FF%FE");
        // café in UTF-8: 0x63 0x61 0x66 0xC3 0xA9
        assert_eq!(encode_data(b"caf\xC3\xA9"), "caf%C3%A9");
    }
}
