package com.rawprox;

import java.util.concurrent.atomic.AtomicLong;

public class ConnId {
    private static final String BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    private static final AtomicLong counter;

    static {
        long timestamp = System.currentTimeMillis() / 1000;
        counter = new AtomicLong(timestamp);
    }

    public static String next() {
        long value = counter.getAndIncrement();
        return toBase62(value, 5);
    }

    private static String toBase62(long value, int length) {
        // Convert to base62
        StringBuilder result = new StringBuilder();
        long v = value;
        for (int i = 0; i < length; i++) {
            result.insert(0, BASE62.charAt((int) (v % 62)));
            v /= 62;
        }
        // Result is exactly 'length' characters (last N digits)
        return result.toString();
    }

    public static void _TEST_toBase62_encoding() {
        // Test base62 encoding with known values
        String result = toBase62(0, 5);
        if (!result.equals("00000")) {
            throw new AssertionError("Expected 00000, got: " + result);
        }

        result = toBase62(61, 5);
        if (!result.equals("0000z")) {
            throw new AssertionError("Expected 0000z, got: " + result);
        }

        result = toBase62(62, 5);
        if (!result.equals("00010")) {
            throw new AssertionError("Expected 00010, got: " + result);
        }

        result = toBase62(3843, 5); // 62^2 - 1
        if (!result.equals("000zz")) {
            throw new AssertionError("Expected 000zz, got: " + result);
        }
    }

    public static void _TEST_next_format() {
        // Test that next() returns proper format
        String id1 = next();
        if (id1.length() != 5) {
            throw new AssertionError("Expected length 5, got: " + id1.length());
        }

        // Test uniqueness
        String id2 = next();
        if (id1.equals(id2)) {
            throw new AssertionError("IDs should be unique: " + id1 + " == " + id2);
        }

        // Test all characters are valid base62
        for (char c : id2.toCharArray()) {
            if (BASE62.indexOf(c) == -1) {
                throw new AssertionError("Invalid character in ID: " + c);
            }
        }
    }
}
