<?php
// db.config.php — reads connection details from environment variables
$servername = getenv('DB_HOST') ?: 'db';
$dbusername = getenv('DB_USER') ?: 'website';
$dbpassword = getenv('DB_PASS') ?: 'tartans@1';
$dbname     = getenv('DB_NAME') ?: 'ecommerce';

$conn = new mysqli($servername, $dbusername, $dbpassword, $dbname);

if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}
?>
