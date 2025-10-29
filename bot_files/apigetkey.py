#python 3.12 - chỉ có anti hook nhẹ
import os
import json
import string
import random
import time
import requests
import platform
import socket
import urllib3
from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from hashlib import sha256

# ======= Tắt warnings SSL =======
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ======= Cấu hình =======
API_BASE = "https://mttool.x10.mx"
LINK4M_API = "https://link4m.co/st?api=68bae045a8aae101577b33f0&url=" #thay bằng api link4m của bạn 
APPDATA_DIR = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "MTTOOL")
KEY_FILE = os.path.join(APPDATA_DIR, "key.json")
ORIGIN = "mtoolvip"
USER_AGENT = "sieunhansiplord"
EXPIRE_SECONDS = 86400  # 24h
ENC_PASSWORD = "mtt@@l010920||12"  # mật khẩu để mã hóa AES

# ======= AES Encrypt/Decrypt =======
def aes_encrypt(data: str, password: str) -> str:
    key = sha256(password.encode()).digest()
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data.encode(), AES.block_size))
    iv = b64encode(cipher.iv).decode('utf-8')
    ct = b64encode(ct_bytes).decode('utf-8')
    return json.dumps({"iv": iv, "ciphertext": ct})

def aes_decrypt(enc_data: str, password: str) -> str:
    try:
        b64 = json.loads(enc_data)
        iv = b64decode(b64['iv'])
        ct = b64decode(b64['ciphertext'])
        key = sha256(password.encode()).digest()
        cipher = AES.new(key, AES.MODE_CBC, iv)
        pt = unpad(cipher.decrypt(ct), AES.block_size)
        return pt.decode('utf-8')
    except:
        return None

# ======= Tạo key mt1XYYXXXYXXY (chỉ dùng gửi request, không lưu) =======
def generate_key():
    chars = string.ascii_letters
    nums_special = string.digits + "!@#$%^&*"
    key = "mt1"
    key += ''.join(random.choice(chars) for _ in range(1))
    key += ''.join(random.choice(nums_special) for _ in range(2))
    key += ''.join(random.choice(chars) for _ in range(3))
    key += ''.join(random.choice(nums_special) for _ in range(1))
    key += ''.join(random.choice(chars) for _ in range(2))
    key += ''.join(random.choice(nums_special) for _ in range(1))
    return key

# ======= Lấy IMEI hoặc IP =======
def get_device_id():
    if platform.system().lower() == "linux" and "ANDROID_ROOT" in os.environ:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    else:
        try:
            import uuid
            return str(uuid.getnode())
        except:
            return "127.0.0.1"

# ======= Lưu key vào file (mã hóa) =======
def save_key(key, device_id):
    if not os.path.exists(APPDATA_DIR):
        os.makedirs(APPDATA_DIR)
    data = {
        "key": key,
        "device_id": device_id,
        "timestamp": int(time.time())
    }
    enc = aes_encrypt(json.dumps(data), ENC_PASSWORD)
    with open(KEY_FILE, "w") as f:
        f.write(enc)

# ======= Load key nếu còn hạn (giải mã) =======
def load_valid_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r") as f:
            enc = f.read()
        dec = aes_decrypt(enc, ENC_PASSWORD)
        if dec:
            data = json.loads(dec)
            if "key" in data and "timestamp" in data:
                if int(time.time()) - data["timestamp"] < EXPIRE_SECONDS:
                    return data["key"]
    return None

# ======= Gửi request tới link4m và lấy redirect =======
def send_link4m_request(key):
    url = LINK4M_API + f"{API_BASE}/secretapi.php?key={key}"
    r = requests.get(url, allow_redirects=True, verify=False)
    return r.url

# ======= Gửi skey request =======
def send_skey_request(key, device_id):
    url = f"{API_BASE}/checkkey.php?skey=mttoolsrv-{key}"
    headers = {
        "Origin": ORIGIN,
        "User-Agent": USER_AGENT,
        "X-IMEI": device_id
    }
    r = requests.get(url, headers=headers, verify=False)
    try:
        data = r.json()
        print(f"SKey Status: {data.get('status')}")
        return data.get('status') == 'success'
    except:
        print("SKey request failed")
        return False

# ======= Gửi ckey request =======
def send_ckey_request(device_id):
    key_input = input("Enter key to check and save: ").strip()
    if not key_input.startswith("mttoolsrv-"):
        key_input = "mttoolsrv-" + key_input
    url = f"{API_BASE}/checkkey.php?ckey={key_input}"
    headers = {
        "Origin": ORIGIN,
        "User-Agent": USER_AGENT,
        "X-IMEI": device_id
    }
    r = requests.get(url, headers=headers, verify=False)
    try:
        data = r.json()
        expires_sec = data.get('expires_in_seconds', 0)
        hours = expires_sec // 3600
        minutes = (expires_sec % 3600) // 60
        print(f"CKey Status: {data.get('status')}, Expires in: {hours}h {minutes}m")
        if data.get('status') == 'success':
            save_key(key_input.replace("mttoolsrv-", ""), device_id)
            print("Key saved to key.json (encrypted)")
    except:
        print("CKey request failed")

# ======= Main =======
def main():
    device_id = get_device_id()

    # Kiểm tra key đã có hợp lệ trong 24h chưa
    key = load_valid_key()
    if key:
        print(f"Using existing key (within 24h): {key}")
    else:
        key = generate_key()
        print(f"Generated temporary Key (not saved): {key}")

    print(f"Device ID: {device_id}")

    redirected_url = send_link4m_request(key)
    print(f"Redirected URL: {redirected_url}")

    print("Waiting 60 seconds before sending skey request...")
    time.sleep(60)

    send_skey_request(key, device_id)

    # Nhập key từ user để check và lưu (mã hóa)
    send_ckey_request(device_id)

if __name__ == "__main__":
    main()
