package com.rawprox;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.channels.AsynchronousServerSocketChannel;
import java.nio.channels.AsynchronousSocketChannel;
import java.nio.channels.CompletionHandler;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.CountDownLatch;

public class Main {
    private static final List<PortForwarding> forwardings = new ArrayList<>();
    private static String outputFile = null;
    private static long flushIntervalMs = 2000;
    private static BufferedOutput output;

    public static void main(String[] args) {
        if (args.length == 0) {
            printUsage();
            System.exit(1);
        }

        if (!parseArgs(args)) {
            System.exit(1);
        }

        try {
            output = new BufferedOutput(outputFile, flushIntervalMs);

            // Add shutdown hook to flush buffers on exit
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                if (output != null) {
                    output.close();
                }
            }));

            startProxyServers();
        } catch (IOException e) {
            System.err.println("Error: " + e.getMessage());
            System.exit(1);
        }
    }

    private static boolean parseArgs(String[] args) {
        Set<Integer> usedPorts = new HashSet<>();

        for (String arg : args) {
            if (arg.startsWith("@")) {
                outputFile = arg.substring(1);
            } else if (arg.startsWith("--flush-interval-ms=")) {
                try {
                    flushIntervalMs = Long.parseLong(arg.substring("--flush-interval-ms=".length()));
                } catch (NumberFormatException e) {
                    System.err.println("Error: Invalid flush interval: " + arg);
                    return false;
                }
            } else {
                PortForwarding pf = parsePortForwarding(arg);
                if (pf == null) {
                    return false;
                }
                if (usedPorts.contains(pf.localPort)) {
                    System.err.println("Error: Duplicate local port: " + pf.localPort);
                    return false;
                }
                usedPorts.add(pf.localPort);
                forwardings.add(pf);
            }
        }

        if (forwardings.isEmpty()) {
            System.err.println("Error: At least one port forwarding rule required");
            printUsage();
            return false;
        }

        if (outputFile != null) {
            try {
                Path path = Paths.get(outputFile);
                Path parent = path.getParent();
                if (parent != null) {
                    Files.createDirectories(parent);
                }
            } catch (Exception e) {
                System.err.println("Error: Cannot create output directory: " + e.getMessage());
                return false;
            }
        }

        return true;
    }

    private static PortForwarding parsePortForwarding(String arg) {
        String[] parts = arg.split(":");
        if (parts.length != 3) {
            System.err.println("Error: Invalid port forwarding format: " + arg);
            System.err.println("Expected: LOCAL_PORT:TARGET_HOST:TARGET_PORT");
            return null;
        }

        try {
            int localPort = Integer.parseInt(parts[0]);
            String targetHost = parts[1];
            int targetPort = Integer.parseInt(parts[2]);

            if (localPort < 1 || localPort > 65535 || targetPort < 1 || targetPort > 65535) {
                System.err.println("Error: Port numbers must be between 1 and 65535");
                return null;
            }

            return new PortForwarding(localPort, targetHost, targetPort);
        } catch (NumberFormatException e) {
            System.err.println("Error: Invalid port number in: " + arg);
            return null;
        }
    }

    private static void startProxyServers() throws IOException {
        CountDownLatch latch = new CountDownLatch(1);

        for (PortForwarding pf : forwardings) {
            AsynchronousServerSocketChannel serverChannel = AsynchronousServerSocketChannel.open();
            try {
                serverChannel.bind(new InetSocketAddress("0.0.0.0", pf.localPort));
            } catch (IOException e) {
                if (e.getMessage().contains("Address already in use")) {
                    System.err.println("Error: Port " + pf.localPort + " is already in use");
                } else {
                    System.err.println("Error: Cannot bind to port " + pf.localPort + ": " + e.getMessage());
                }
                System.exit(1);
            }

            acceptConnections(serverChannel, pf);
        }

        try {
            latch.await();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    private static void acceptConnections(AsynchronousServerSocketChannel serverChannel, PortForwarding pf) {
        serverChannel.accept(null, new CompletionHandler<AsynchronousSocketChannel, Void>() {
            @Override
            public void completed(AsynchronousSocketChannel clientSocket, Void attachment) {
                acceptConnections(serverChannel, pf);

                try {
                    new ProxyConnection(clientSocket, pf, output).start();
                } catch (IOException e) {
                    try {
                        clientSocket.close();
                    } catch (IOException ignored) {
                    }
                }
            }

            @Override
            public void failed(Throwable exc, Void attachment) {
                System.err.println("Accept failed: " + exc.getMessage());
                acceptConnections(serverChannel, pf);
            }
        });
    }

    private static void printUsage() {
        System.err.println("Usage: rawprox [ARGS ...]");
        System.err.println();
        System.err.println("Arguments:");
        System.err.println("  LOCAL_PORT:TARGET_HOST:TARGET_PORT  Port forwarding rule (required, at least one)");
        System.err.println("  @FILEPATH                           Write output to file instead of stdout (optional)");
        System.err.println("  --flush-interval-ms=MILLISECONDS    Buffer flush interval (default: 2000)");
        System.err.println();
        System.err.println("Examples:");
        System.err.println("  rawprox 8080:example.com:80");
        System.err.println("  rawprox 8080:api.example.com:80 3306:db.example.com:3306");
        System.err.println("  rawprox 9000:server.com:443 @traffic.ndjson");
        System.err.println("  rawprox 8080:api.example.com:80 --flush-interval-ms=100 @debug.ndjson");
    }

    static class PortForwarding {
        final int localPort;
        final String targetHost;
        final int targetPort;

        PortForwarding(int localPort, String targetHost, int targetPort) {
            this.localPort = localPort;
            this.targetHost = targetHost;
            this.targetPort = targetPort;
        }
    }

    public static void _TEST_parsePortForwarding() {
        // Test valid port forwarding
        PortForwarding pf = parsePortForwarding("8080:example.com:80");
        if (pf == null || pf.localPort != 8080 || !pf.targetHost.equals("example.com") || pf.targetPort != 80) {
            throw new AssertionError("Failed to parse valid port forwarding");
        }

        // Test invalid format
        pf = parsePortForwarding("invalid");
        if (pf != null) {
            throw new AssertionError("Should reject invalid format");
        }

        // Test invalid port numbers
        pf = parsePortForwarding("70000:example.com:80");
        if (pf != null) {
            throw new AssertionError("Should reject invalid port number");
        }

        // Test with IPv4 address
        pf = parsePortForwarding("8080:192.168.1.1:443");
        if (pf == null || !pf.targetHost.equals("192.168.1.1") || pf.targetPort != 443) {
            throw new AssertionError("Failed to parse IPv4 address");
        }
    }

    public static void _TEST_flush_interval_parsing() {
        // Test that flush interval can be parsed
        String[] args = {"--flush-interval-ms=5000"};
        // Reset state
        flushIntervalMs = 2000;
        forwardings.clear();

        // Parse should fail (no port forwarding)
        if (parseArgs(args)) {
            throw new AssertionError("Should require at least one port forwarding");
        }

        // Should have updated flush interval despite failing
        if (flushIntervalMs != 5000) {
            throw new AssertionError("Expected flush interval 5000, got: " + flushIntervalMs);
        }

        // Reset
        flushIntervalMs = 2000;
    }
}
