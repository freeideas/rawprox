package com.rawprox;

public class Encoding {
    public static String encode(byte[] data) {
        StringBuilder result = new StringBuilder(data.length * 2);

        for (byte b : data) {
            int unsigned = b & 0xFF;

            if (unsigned == 0x22) { // "
                result.append("\\\"");
            } else if (unsigned == 0x5C) { // \
                result.append("\\\\");
            } else if (unsigned == 0x0A) { // \n
                result.append("\\n");
            } else if (unsigned == 0x0D) { // \r
                result.append("\\r");
            } else if (unsigned == 0x09) { // \t
                result.append("\\t");
            } else if (unsigned == 0x08) { // \b
                result.append("\\b");
            } else if (unsigned == 0x0C) { // \f
                result.append("\\f");
            } else if (unsigned == 0x25) { // %
                result.append("%25");
            } else if (unsigned >= 0x20 && unsigned <= 0x7E) {
                result.append((char) unsigned);
            } else {
                result.append(String.format("%%%02X", unsigned));
            }
        }

        return result.toString();
    }

    public static void _TEST_encode_special_chars() {
        // Test JSON special characters
        String result = encode("\"\\".getBytes());
        if (!result.equals("\\\"\\\\")) {
            throw new AssertionError("Expected \\\"\\\\, got: " + result);
        }

        // Test whitespace characters
        result = encode("\n\r\t\b\f".getBytes());
        if (!result.equals("\\n\\r\\t\\b\\f")) {
            throw new AssertionError("Expected \\n\\r\\t\\b\\f, got: " + result);
        }

        // Test percent encoding
        result = encode("%".getBytes());
        if (!result.equals("%25")) {
            throw new AssertionError("Expected %25, got: " + result);
        }

        // Test printable ASCII
        result = encode("Hello".getBytes());
        if (!result.equals("Hello")) {
            throw new AssertionError("Expected Hello, got: " + result);
        }

        // Test non-printable bytes
        result = encode(new byte[]{0x00, 0x1F, (byte) 0xFF});
        if (!result.equals("%00%1F%FF")) {
            throw new AssertionError("Expected %00%1F%FF, got: " + result);
        }

        // Test empty array
        result = encode(new byte[]{});
        if (!result.equals("")) {
            throw new AssertionError("Expected empty string, got: " + result);
        }
    }
}
