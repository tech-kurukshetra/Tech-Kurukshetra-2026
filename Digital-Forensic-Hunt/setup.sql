-- Run this in MySQL before starting the server
CREATE DATABASE IF NOT EXISTS systrace_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- If using root without password, nothing else needed.
-- Otherwise: CREATE USER 'systrace'@'localhost' IDENTIFIED BY 'yourpassword';
-- GRANT ALL PRIVILEGES ON systrace_db.* TO 'systrace'@'localhost';
-- FLUSH PRIVILEGES;
