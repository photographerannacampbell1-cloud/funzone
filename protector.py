import json
import requests
import time
import signal
import sys
import os
import datetime

# ==========================================
#   Dev: @SheinAalu x @sheingiveawayghost
# ==========================================

# --- Configuration ---
VOUCHER_VALUES = {
    "SVH": 4000,
    "SV3": 5000,
    "SVC": 1000,
    "SVD": 2000,
    "SVA": 500,
    "SVG": 500
}

# 8 Minutes in seconds
CHECK_INTERVAL_SECONDS = 480 

def signal_handler(sig, frame):
    print("\n\n🔚 Terminating session gracefully... (Credits: @SheinAalu x @sheingiveawayghost)")
    sys.exit(0)

def get_current_time():
    return datetime.datetime.now().strftime("%H:%M:%S")

def load_cookies():
    if not os.path.exists("cookies.json"):
        print("❌ Error: 'cookies.json' file not found!")
        return ""
        
    try:
        with open("cookies.json", "r", encoding="utf-8") as f:
            raw = f.read().strip()
            
        data = json.loads(raw)
        
        # Case 1: Standard Browser Export (List of objects)
        if isinstance(data, list):
            cookies = []
            for item in data:
                if isinstance(item, dict) and "name" in item and "value" in item:
                    cookies.append(f"{item['name']}={item['value']}")
            return "; ".join(cookies)
            
        # Case 2: Simple Dictionary (Key:Value)
        elif isinstance(data, dict):
            return "; ".join(f"{k}={v}" for k, v in data.items())
            
    except Exception as e:
        print(f"⚠️ Error parsing cookies.json: {str(e)}")
    
    return ""

def get_headers(cookie_string):
    return {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "origin": "https://www.sheinindia.in",
        "pragma": "no-cache",
        "referer": "https://www.sheinindia.in/cart",
        "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": "\"Android\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "x-tenant-id": "SHEIN",
        "cookie": cookie_string
    }

def get_voucher_value(code):
    prefix = code[:3].upper()
    return VOUCHER_VALUES.get(prefix, None)

def parse_vouchers_file():
    if not os.path.exists("vouchers.txt"):
        print("❌ Error: 'vouchers.txt' file not found!")
        return []

    vouchers = []
    with open("vouchers.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("==="):
                continue
            vouchers.append({'code': line})
    return vouchers

def check_voucher(voucher_code, headers):
    url = "https://www.sheinindia.in/api/cart/apply-voucher"
    payload = {
        "voucherId": voucher_code,
        "device": {
            "client_type": "mobile_web"
        }
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        try:
            json_data = response.json()
        except json.JSONDecodeError:
            return response.status_code, None
            
        return response.status_code, json_data
    except Exception as e:
        print(f"⚠️ Validation error for {voucher_code}: {str(e)}")
        return None, None

def reset_voucher(voucher_code, headers):
    url = "https://www.sheinindia.in/api/cart/reset-voucher"
    payload = {
        "voucherId": voucher_code,
        "device": {
            "client_type": "mobile_web"
        }
    }
    try:
        requests.post(url, json=payload, headers=headers, timeout=30)
    except:
        pass

def is_voucher_applicable(response_data):
    if not response_data:
        return False
    
    if "errorMessage" in response_data:
        errors = response_data.get("errorMessage", {}).get("errors", [])
        for error in errors:
            if error.get("type") == "VoucherOperationError":
                if "not applicable" in error.get("message", "").lower():
                    return False
        return False 
        
    return True

# --- New Protection Logic ---
def run_protection_loop(vouchers, headers):
    print(f"\n🛡️ Protection Mode Active! (Interval: 8 Minutes)")
    print(f"🕒 Start Time: {get_current_time()}\n")
    
    cycle_count = 1
    
    while True:
        cycle_start = time.time()
        print(f"🔄 Cycle #{cycle_count} started at [{get_current_time()}]")
        
        valid_in_this_cycle = []
        
        for i, voucher in enumerate(vouchers, 1):
            code = voucher['code']
            
            # Check the code
            status, data = check_voucher(code, headers)
            
            if is_voucher_applicable(data):
                val = get_voucher_value(code)
                print(f"   ✅ {code} is ALIVE! (Value: ₹{val if val else '???'})")
                valid_in_this_cycle.append(code)
            else:
                # Uncomment next line if you want to see failed codes too
                # print(f"   ❌ {code} failed.")
                pass
            
            # Reset immediately so cart is clean for next check
            reset_voucher(code, headers)
            
            # Small delay to prevent rate limiting (2 seconds)
            time.sleep(2) 
            
        print(f"🏁 Cycle #{cycle_count} finished. {len(valid_in_this_cycle)} valid codes.")
        
        # Calculate how long to sleep
        elapsed = time.time() - cycle_start
        sleep_time = CHECK_INTERVAL_SECONDS - elapsed
        
        if sleep_time > 0:
            next_scan_time = datetime.datetime.now() + datetime.timedelta(seconds=sleep_time)
            print(f"😴 Next scan at: {next_scan_time.strftime('%H:%M:%S')}")
            
            # Visible Countdown Timer
            try:
                for remaining in range(int(sleep_time), 0, -1):
                    # \r overwrites the current line
                    sys.stdout.write(f"\r⏳ Next scan in: {remaining}s   ")
                    sys.stdout.flush()
                    time.sleep(1)
                sys.stdout.write("\r🚀 Starting next scan...          \n")
            except KeyboardInterrupt:
                raise
        else:
            print("⚠️ Scan took longer than 8 mins, restarting immediately!")
            
        cycle_count += 1
        print("-" * 40)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    print("====================================================")
    print("🛡️  SHEIN Voucher Checker + Protector (Termux Ver) 🛡️")
    print("🤝  Credits: @SheinAalu x @sheingiveawayghost")
    print("====================================================")
    
    cookie_string = load_cookies()
    if not cookie_string:
        return

    headers = get_headers(cookie_string)
    vouchers = parse_vouchers_file()
    
    if not vouchers:
        print("❌ No vouchers in vouchers.txt to protect.")
        return

    print(f"📝 Loaded {len(vouchers)} vouchers.")
    print("\n🔄 Enable Protection Mode (Check every 8 mins)? (y/n): ")
    choice = input().strip().lower()
    
    if choice == 'y':
        try:
            run_protection_loop(vouchers, headers)
        except KeyboardInterrupt:
            print("\n👋 Protection mode stopped by user.")
    else:
        # Run a single scan immediately
        print("\n🚀 Running single scan...")
        for voucher in vouchers:
            code = voucher['code']
            s, d = check_voucher(code, headers)
            if is_voucher_applicable(d):
                val = get_voucher_value(code)
                print(f"✅ {code} -> VALID (₹{val})")
            else:
                print(f"❌ {code} -> INVALID")
            reset_voucher(code, headers)
        print("👋 Done.")

if __name__ == "__main__":
    main()