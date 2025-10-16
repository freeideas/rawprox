package com.rawprox;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.AsynchronousSocketChannel;
import java.nio.channels.CompletionHandler;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.Arrays;

public class ProxyConnection {
    private static final int BUFFER_SIZE = 32768;
    private static final DateTimeFormatter ISO_FORMATTER =
        DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'").withZone(ZoneOffset.UTC);

    private final AsynchronousSocketChannel clientSocket;
    private final Main.PortForwarding forwarding;
    private final BufferedOutput output;
    private final String connId;
    private AsynchronousSocketChannel serverSocket;

    public ProxyConnection(AsynchronousSocketChannel clientSocket, Main.PortForwarding forwarding, BufferedOutput output) {
        this.clientSocket = clientSocket;
        this.forwarding = forwarding;
        this.output = output;
        this.connId = ConnId.next();
    }

    public void start() throws IOException {
        serverSocket = AsynchronousSocketChannel.open();
        InetSocketAddress serverAddress = new InetSocketAddress(forwarding.targetHost, forwarding.targetPort);

        serverSocket.connect(serverAddress, null, new CompletionHandler<Void, Void>() {
            @Override
            public void completed(Void result, Void attachment) {
                try {
                    logOpen();
                    startForwarding();
                } catch (IOException e) {
                    cleanup();
                }
            }

            @Override
            public void failed(Throwable exc, Void attachment) {
                cleanup();
            }
        });
    }

    private void logOpen() throws IOException {
        String clientAddr = getAddress(clientSocket);
        String serverAddr = forwarding.targetHost + ":" + forwarding.targetPort;

        String json = String.format(
            "{\"time\":\"%s\",\"ConnID\":\"%s\",\"event\":\"open\",\"from\":\"%s\",\"to\":\"%s\"}",
            ISO_FORMATTER.format(Instant.now()), connId, clientAddr, serverAddr
        );

        output.append(json + "\n");
    }

    private void logClose(String from, String to) {
        String json = String.format(
            "{\"time\":\"%s\",\"ConnID\":\"%s\",\"event\":\"close\",\"from\":\"%s\",\"to\":\"%s\"}",
            ISO_FORMATTER.format(Instant.now()), connId, from, to
        );

        output.append(json + "\n");
    }

    private void logData(byte[] data, int length, String from, String to) {
        String encoded = Encoding.encode(Arrays.copyOf(data, length));

        String json = String.format(
            "{\"time\":\"%s\",\"ConnID\":\"%s\",\"data\":\"%s\",\"from\":\"%s\",\"to\":\"%s\"}",
            ISO_FORMATTER.format(Instant.now()), connId, encoded, from, to
        );

        output.append(json + "\n");
    }

    private void startForwarding() throws IOException {
        String clientAddr = getAddress(clientSocket);
        String serverAddr = forwarding.targetHost + ":" + forwarding.targetPort;

        forwardData(clientSocket, serverSocket, clientAddr, serverAddr);
        forwardData(serverSocket, clientSocket, serverAddr, clientAddr);
    }

    private void forwardData(AsynchronousSocketChannel source, AsynchronousSocketChannel dest,
                            String fromAddr, String toAddr) {
        ByteBuffer buffer = ByteBuffer.allocate(BUFFER_SIZE);

        @SuppressWarnings("unchecked")
        CompletionHandler<Integer, ByteBuffer>[] handlerRef = new CompletionHandler[1];

        handlerRef[0] = new CompletionHandler<Integer, ByteBuffer>() {
            @Override
            public void completed(Integer bytesRead, ByteBuffer buf) {
                if (bytesRead == -1) {
                    logClose(fromAddr, toAddr);
                    cleanup();
                    return;
                }

                buf.flip();
                byte[] data = new byte[buf.remaining()];
                buf.get(data);

                logData(data, data.length, fromAddr, toAddr);

                ByteBuffer writeBuffer = ByteBuffer.wrap(data);
                dest.write(writeBuffer, writeBuffer, new CompletionHandler<Integer, ByteBuffer>() {
                    @Override
                    public void completed(Integer bytesWritten, ByteBuffer wb) {
                        if (wb.hasRemaining()) {
                            dest.write(wb, wb, this);
                        } else {
                            buf.clear();
                            source.read(buf, buf, handlerRef[0]);
                        }
                    }

                    @Override
                    public void failed(Throwable exc, ByteBuffer wb) {
                        logClose(toAddr, fromAddr);
                        cleanup();
                    }
                });
            }

            @Override
            public void failed(Throwable exc, ByteBuffer buf) {
                logClose(fromAddr, toAddr);
                cleanup();
            }
        };

        source.read(buffer, buffer, handlerRef[0]);
    }

    private void cleanup() {
        try {
            if (clientSocket != null && clientSocket.isOpen()) {
                clientSocket.close();
            }
        } catch (IOException ignored) {
        }

        try {
            if (serverSocket != null && serverSocket.isOpen()) {
                serverSocket.close();
            }
        } catch (IOException ignored) {
        }
    }

    private String getAddress(AsynchronousSocketChannel socket) throws IOException {
        InetSocketAddress addr = (InetSocketAddress) socket.getRemoteAddress();
        String host = addr.getAddress().getHostAddress();
        if (host.contains(":")) {
            return "[" + host + "]:" + addr.getPort();
        }
        return host + ":" + addr.getPort();
    }

    public static void _TEST_iso_formatter() {
        // Test that ISO_FORMATTER produces valid timestamps
        Instant now = Instant.ofEpochMilli(1234567890123L);
        String formatted = ISO_FORMATTER.format(now);

        // Should be in format: yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'
        if (!formatted.matches("\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\.\\d{6}Z")) {
            throw new AssertionError("Invalid timestamp format: " + formatted);
        }

        // Should contain expected date
        if (!formatted.startsWith("2009-02-13T23:31:30.")) {
            throw new AssertionError("Unexpected timestamp value: " + formatted);
        }
    }
}
