package com.rawprox;

import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class BufferedOutput {
    private final String outputFile;
    private final long flushIntervalMs;
    private final Lock lock = new ReentrantLock();
    private StringBuilder inputBuffer = new StringBuilder();
    private StringBuilder outputBuffer = new StringBuilder();
    private Thread writerThread;
    private volatile boolean running = true;

    public BufferedOutput(String outputFile, long flushIntervalMs) throws IOException {
        // Normalize path for Windows compatibility
        if (outputFile != null) {
            Path path = Paths.get(outputFile).toAbsolutePath().normalize();
            this.outputFile = path.toString();
            System.err.println("[DEBUG] Normalized output path: " + this.outputFile);
        } else {
            this.outputFile = null;
        }

        this.flushIntervalMs = flushIntervalMs;

        if (this.outputFile != null) {
            Path path = Paths.get(this.outputFile);
            Path parent = path.getParent();
            if (parent != null) {
                Files.createDirectories(parent);
            }
        }

        startWriterThread();
    }

    public void append(String data) {
        System.err.println("[DEBUG] Appending " + data.length() + " bytes to inputBuffer");
        lock.lock();
        try {
            inputBuffer.append(data);
            System.err.println("[DEBUG] inputBuffer now has " + inputBuffer.length() + " bytes");
        } finally {
            lock.unlock();
        }
    }

    private void startWriterThread() {
        System.err.println("[DEBUG] Starting writer thread with interval=" + flushIntervalMs + "ms");
        writerThread = new Thread(() -> {
            System.err.println("[DEBUG] Writer thread started");
            while (running) {
                try {
                    System.err.println("[DEBUG] Writer thread sleeping for " + flushIntervalMs + "ms");
                    Thread.sleep(flushIntervalMs);
                    System.err.println("[DEBUG] Writer thread woke up");
                } catch (InterruptedException e) {
                    System.err.println("[DEBUG] Writer thread interrupted");
                    // Thread interrupted, exit loop
                    break;
                }

                swapAndWrite();
            }
            System.err.println("[DEBUG] Writer thread exiting");
        });
        writerThread.setDaemon(true);
        writerThread.start();
        System.err.println("[DEBUG] Writer thread started (async)");
    }

    private void swapAndWrite() {
        lock.lock();
        try {
            if (inputBuffer.length() == 0) {
                System.err.println("[DEBUG] swapAndWrite: inputBuffer empty, skipping");
                return;
            }

            System.err.println("[DEBUG] swapAndWrite: swapping " + inputBuffer.length() + " bytes");
            StringBuilder temp = inputBuffer;
            inputBuffer = outputBuffer;
            outputBuffer = temp;
        } finally {
            lock.unlock();
        }

        try {
            if (outputFile == null) {
                System.err.println("[DEBUG] Writing to stdout: " + outputBuffer.length() + " bytes");
                System.out.write(outputBuffer.toString().getBytes(StandardCharsets.UTF_8));
                System.out.flush();
            } else {
                System.err.println("[DEBUG] Writing to file " + outputFile + ": " + outputBuffer.length() + " bytes");
                // Simple: open, append, close
                try (FileWriter fw = new FileWriter(outputFile, true)) {
                    fw.write(outputBuffer.toString());
                }
                System.err.println("[DEBUG] File write completed");
            }
        } catch (IOException e) {
            System.err.println("Error writing output: " + e.getMessage());
            System.exit(1);
        }

        outputBuffer.setLength(0);
    }

    public void close() {
        running = false;
        if (writerThread != null) {
            writerThread.interrupt();
            try {
                writerThread.join();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
        swapAndWrite();
    }

    public static void _TEST_double_buffering() throws IOException, InterruptedException {
        // Create a temp file for testing
        String tempFile = System.getProperty("java.io.tmpdir") + "/test_buffered_output.txt";
        BufferedOutput output = new BufferedOutput(tempFile, 100);

        // Append some data
        output.append("line1\n");
        output.append("line2\n");

        // Wait for flush
        Thread.sleep(150);

        // Append more while flushing
        output.append("line3\n");

        output.close();

        // Read file and verify
        String content = new String(java.nio.file.Files.readAllBytes(java.nio.file.Paths.get(tempFile)));
        if (!content.contains("line1") || !content.contains("line2") || !content.contains("line3")) {
            throw new AssertionError("Expected all lines in output, got: " + content);
        }

        // Cleanup
        java.nio.file.Files.deleteIfExists(java.nio.file.Paths.get(tempFile));
    }
}
