from http import client
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import os # Dùng để kiểm tra logic 2 ngày/lần
import re 

# --- CẤU HÌNH ---
GOLD_XML_URL = "http://giavang.doji.vn/api/giavang/?api_key=258fbd2a72ce8481089d88c678e9fe4f&fbclid=IwZXh0bgNhZW0CMTAAYnJpZBExeGhpYm14RWZBTUcya3dET3NydGMGYXBwX2lkEDIyMjAzOTE3ODgyMDA4OTIAAR4Dk6frzlq-39ImD9sqyhSv6RLI-zAD4Ghj1W3fgQJY7satBljvr9BpOyNlog_aem_GEOCdYOMTzpF7L7wJKVemQ"
LOG_FILE = "./gold_price_log.txt"  # Thay đổi đường dẫn này
LAST_RUN_FILE = "./last_run.txt"      # File lưu thời gian chạy lần cuối

def string_to_float(value):
    """Chuyển các chuỗi giá phổ biến thành float hoặc trả về None nếu không parse được.
    Xử lý:
        - '150,300' -> 150300.0
        - '1.234,56' -> 1234.56
        - '1500.50' -> 1500.5
        - 'N/A', '', None -> None
    Input: value: str hoặc số
    Output: float hoặc None
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.upper() in ("N/A", "-", "NULL"):
        return None

    # Giữ lại chỉ chữ số, dấu ., dấu , và dấu -
    s = re.sub(r"[^\d\.,\-]", "", s)

    # Nếu cả '.' và ',' xuất hiện, đoán kiểu:
    if '.' in s and ',' in s:
        # Nếu dấu ',' xuất hiện sau dấu '.' -> coi ',' là dấu thập phân (ví dụ "1.234,56")
        if s.rfind(',') > s.rfind('.'):
            s = s.replace('.', '').replace(',', '.')
        else:
            # Ngược lại coi ',' là phân tách ngàn
            s = s.replace(',', '')
    elif ',' in s:
        # Nếu phần sau dấu ',' có độ dài 3 => nhiều khả năng là phân tách ngàn -> loại bỏ ','
        if len(s.split(',')[-1]) == 3:
            s = s.replace(',', '')
        else:
            # Ngược lại coi ',' là dấu thập phân
            s = s.replace(',', '.')
    # else: chỉ có '.' hoặc chỉ chữ số -> để nguyên

    try:
        return float(s)
    except Exception:
        return None

def check_run_frequency():
    """Kiểm tra xem đã đủ 2 ngày kể từ lần chạy cuối chưa."""
    if not os.path.exists(LAST_RUN_FILE):
        return True # Lần đầu chạy, luôn thực hiện

    try:
        with open(LAST_RUN_FILE, 'r') as f:
            last_run_str = f.read().strip()
        last_run_date = datetime.strptime(last_run_str, "%Y-%m-%d")
        
        current_date = datetime.now()
        delta = current_date - last_run_date
        
        # Chạy nếu đã qua ít nhất 48 giờ (hoặc chỉ cần kiểm tra ngày > 2)
        if delta.days >= 2:
            return True
        else:
            return False
    except Exception as e:
        print(f"Lỗi khi kiểm tra tần suất chạy: {e}. Thực hiện chạy.")
        return True

def update_last_run_file():
    """Cập nhật thời gian chạy thành công."""
    try:
        with open(LAST_RUN_FILE, 'w') as f:
            f.write(datetime.now().strftime("%Y-%m-%d"))
    except Exception as e:
        print(f"Cảnh báo: Không thể cập nhật file lần chạy cuối: {e}")


def fetch_and_parse_gold_price():
    """Thực hiện tải XML và phân tích dữ liệu giá vàng."""
    try:
        # 1. Tải XML từ HTTP
        response = requests.get(GOLD_XML_URL, timeout=10)
        response.raise_for_status() # Kiểm tra lỗi HTTP

        xml_data = response.content
        
        # 2. Phân tích XML
        root = ET.fromstring(xml_data)
        
        # Dùng XPath để tìm kiếm thông tin mong muốn
        
        # Lấy thời gian cập nhật của DGPList (Giá Vàng DOJI)
        dgp_datetime_tag = root.find(".//DGPList/DateTime")
        last_updated_doji = dgp_datetime_tag.text if dgp_datetime_tag is not None else "N/A"
        
        # Lấy giá Vàng 24k (trong JewelryList)
        vang_24k_row = root.find(".//JewelryList/Row[@Key='vang24k']")
        
        gold_24k_sell = vang_24k_row.get('Sell') if vang_24k_row is not None else "N/A"
        gold_24k_buy = vang_24k_row.get('Buy') if vang_24k_row is not None else "N/A"
        
        # Lấy giá DOJI HCM lẻ (trong DGPList)
        doji_hcm_le_row = root.find(".//JewelryList/Row[@Key='dojihanoile']")
        
        doji_hcm_le_sell = doji_hcm_le_row.get('Sell') if doji_hcm_le_row is not None else "N/A"
        doji_hcm_le_buy = doji_hcm_le_row.get('Buy') if doji_hcm_le_row is not None else "N/A"
        doji_hcm_le_buy = string_to_float(doji_hcm_le_buy) * 1000
        doji_hcm_le_sell = string_to_float(doji_hcm_le_sell) * 1000

        # 3. Định dạng kết quả
        result = {
            "timestamp_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_doji_xml": last_updated_doji,
            "vang_24k_ban": gold_24k_sell,
            "vang_24k_mua": gold_24k_buy,
            "doji_hcm_le_ban": doji_hcm_le_sell,
            "doji_hcm_le_mua": doji_hcm_le_buy
        }
        
        return result

    except requests.exceptions.RequestException as e:
        return {"error": f"Lỗi HTTP/Kết nối: {e}"}
    except ET.ParseError as e:
        return {"error": f"Lỗi phân tích XML: {e}"}
    except Exception as e:
        return {"error": f"Lỗi không xác định: {e}"}

def log_data(data):
    """Ghi dữ liệu vào file log."""
    log_message = f"[{data.get('timestamp_run')}] Cập nhật XML lúc: {data.get('timestamp_doji_xml')} | 24K: Mua={data.get('vang_24k_mua')}, Bán={data.get('vang_24k_ban')} | DOJI HCM Lẻ: Mua={data.get('doji_hcm_le_mua')}, Bán={data.get('doji_hcm_le_ban')}\n"
    
    if "error" in data:
        log_message = f"[{data.get('timestamp_run')}] LỖI: {data.get('error')}\n"

    try:
        with open(LOG_FILE, 'a') as f:
            f.write(log_message)
    except Exception as e:
        print(f"Lỗi khi ghi vào file log: {e}")

def log_data_to_supabase(data):
    """Ghi dữ liệu vào Supabase (đọc SUPABASE_URL và SUPABASE_KEY từ .env)."""
    try:
        # Thử load .env nếu python-dotenv có sẵn (không bắt buộc)
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except Exception:
            pass

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        table = os.getenv("SUPABASE_TABLE", "gold_price")

        if not supabase_url or not supabase_key:
            print("Supabase URL/KEY không được cấu hình (SUPABASE_URL / SUPABASE_KEY). Bỏ qua ghi Supabase.")
            return False

        from supabase import create_client
        client = create_client(supabase_url, supabase_key)

        endpoint = f"{supabase_url.rstrip('/')}/rest/v1/{table}"

        print(data)
        payload = {
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_name": "doji.vn",
            "item_name": "Vàng SJC DOJI Bán Lẻ (1 lượng)",
            "item_key": 'doji_hcm_le',
            "weight_unit": "1 lượng",
            "sell_price": float(data.get("doji_hcm_le_ban")),
            "buy_price": float(data.get("doji_hcm_le_mua"))
        }

        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

        #resp = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        #resp.raise_for_status()
        resp = client.table(table).insert(payload).execute()

        print("Ghi dữ liệu vào Supabase thành công.")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi ghi Supabase: {e}")
        return False
    except Exception as e:
        print(f"Lỗi không xác định khi ghi Supabase: {e}")
        return False

if __name__ == "__main__":
    if True: #check_run_frequency():
        print("Đã đến lúc chạy. Đang thực hiện tác vụ tải giá vàng...")
        gold_data = fetch_and_parse_gold_price()
        log_data(gold_data)
        log_data_to_supabase(gold_data)
        
        if "error" not in gold_data:
            update_last_run_file()
            print("Tác vụ hoàn thành và đã cập nhật file thời gian chạy.")
        else:
            print(f"Tác vụ gặp lỗi: {gold_data['error']}. Không cập nhật file thời gian chạy.")
            
    else:
        print("Chưa đủ 2 ngày. Bỏ qua lần chạy này.")