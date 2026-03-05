import json
import requests
import time
import re

def load_cookies():
   
    with open("cookies.json", "r", encoding="utf-8") as f:
        raw = f.read().strip()

    
    try:
        cookie_dict = json.loads(raw)
        return "; ".join(f"{k}={v}" for k, v in cookie_dict.items())
    except:
        pass 

   
    return raw

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
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "x-tenant-id": "SHEIN",
        "cookie": cookie_string
    }

def parse_vouchers_file():
  
    vouchers = []
    current_price = None
    
    with open("vouchers.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
         
            if line.startswith("=== PRICE"):
                price_match = re.search(r'₹(\d+)', line)
                if price_match:
                    current_price = price_match.group(1)
                continue
            
            if line and not line.startswith("==="):
                vouchers.append({
                    'code': line,
                    'price': current_price
                })
    
    return vouchers

def check_voucher(voucher_code, headers):
 
    url = "https://www.sheinindia.in/api/cart/apply-voucher"
    
    payload = {
        "voucherId": voucher_code,
        "device": {
            "client_type": "web"
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        return response.status_code, response.json()
    except Exception as e:
        print(f"Error checking voucher {voucher_code}: {str(e)}")
        return None, None

def reset_voucher(voucher_code, headers):
    
    url = "https://www.sheinindia.in/api/cart/reset-voucher"
    
    payload = {
        "voucherId": voucher_code,
        "device": {
            "client_type": "web"
        }
    }
    
    try:
        requests.post(url, json=payload, headers=headers, timeout=30)
    except Exception as e:
        print(f"Error resetting voucher {voucher_code}: {str(e)}")

def is_voucher_applicable(response_data):
  
    if not response_data:
        return False
        
   
    if "errorMessage" in response_data:
        errors = response_data.get("errorMessage", {}).get("errors", [])
        for error in errors:
            if error.get("type") == "VoucherOperationError":
                if "not applicable" in error.get("message", "").lower():
                    return False
    
    
    return "errorMessage" not in response_data

def main():
 
    print("Loading cookies...")
    cookie_string = load_cookies()
    headers = get_headers(cookie_string)
    
    print("Parsing vouchers...")
    vouchers = parse_vouchers_file()
    print(f"Found {len(vouchers)} vouchers to check")
    
    applicable_vouchers = []
    not_applicable_vouchers = []
    
    for i, voucher in enumerate(vouchers, 1):
        voucher_code = voucher['code']
        price = voucher['price']
        
        print(f"Checking voucher {i}/{len(vouchers)}: {voucher_code} (₹{price})")
        
       
        status_code, response_data = check_voucher(voucher_code, headers)
        
        if status_code is None:
            print(f"  Failed to check voucher")
            continue
            
        print(f"  Status: {status_code}")
        
        if is_voucher_applicable(response_data):
            print(f"  ✅ Applicable")
            applicable_vouchers.append(voucher)
        else:
            print(f"  ❌ Not applicable")
            not_applicable_vouchers.append(voucher)
            
       
        reset_voucher(voucher_code, headers)
        
       
        time.sleep(1)
    
    
    print(f"\n=== RESULTS ===")
    print(f"Applicable vouchers: {len(applicable_vouchers)}")
    print(f"Not applicable vouchers: {len(not_applicable_vouchers)}")
    
   
    if applicable_vouchers:
        with open("applicable_vouchers.txt", "w", encoding="utf-8") as f:
            current_price = None
            for voucher in applicable_vouchers:
                if voucher['price'] != current_price:
                    current_price = voucher['price']
                    f.write(f"\n=== PRICE ₹{current_price} ===\n")
                f.write(f"{voucher['code']}\n")
        print(f"✅ Saved applicable vouchers to 'applicable_vouchers.txt'")
    
    
    if not_applicable_vouchers:
        with open("not_applicable_vouchers.txt", "w", encoding="utf-8") as f:
            current_price = None
            for voucher in not_applicable_vouchers:
                if voucher['price'] != current_price:
                    current_price = voucher['price']
                    f.write(f"\n=== PRICE ₹{current_price} ===\n")
                f.write(f"{voucher['code']}\n")
        print(f"📝 Saved not applicable vouchers to 'not_applicable_vouchers.txt'")

if __name__ == "__main__":
    main()