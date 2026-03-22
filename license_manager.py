import hashlib
import platform
import uuid
import os
import json
import base64
import winreg
from datetime import datetime, timedelta
from secure_strings import get_registry_path, get_registry_name, get_trial_registry_name, get_activation_key

class LicenseManager:
    TRIAL_COUNT = 200
    
    def __init__(self):
        self.machine_id = self._get_machine_id()
        self.REGISTRY_PATH = get_registry_path()
        self.REGISTRY_NAME = get_registry_name()
        self.TRIAL_REGISTRY_NAME = get_trial_registry_name()
        self.ACTIVATION_KEY = get_activation_key()
    
    def _get_machine_id(self):
        try:
            import subprocess
            result = subprocess.run(
                ['wmic', 'csproduct', 'get', 'UUID'],
                capture_output=True, text=True, timeout=5
            )
            uuid_str = result.stdout.strip().split('\n')[-1].strip()
            if uuid_str and uuid_str != "UUID":
                return hashlib.sha256(uuid_str.encode()).hexdigest()[:32]
        except:
            pass
        
        mac = uuid.getnode()
        cpu_id = platform.processor()
        combined = f"{mac}-{cpu_id}"
        return hashlib.sha256(combined.encode()).hexdigest()[:32]
    
    def _generate_activation_hash(self, card_key):
        combined = f"{self.machine_id}-{card_key}-{self.ACTIVATION_KEY}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def validate_card_key(self, card_key):
        if not card_key or len(card_key) < 8:
            return False
        
        if card_key.startswith("WX-") and len(card_key) >= 14:
            parts = card_key.split("-")
            if len(parts) >= 3:
                hash_part = parts[1]
                if len(hash_part) == 8 and all(c in "0123456789ABCDEFabcdef" for c in hash_part):
                    return True
        
        test_keys = [
            "WX-TEST-2024",
            "WX-DEMO-2024",
        ]
        if card_key in test_keys:
            return True
        
        return False
    
    def _encode_activation_data(self, card_key, timestamp):
        data = {
            "mid": self.machine_id,
            "key": hashlib.sha256(card_key.encode()).hexdigest()[:16],
            "time": timestamp,
            "hash": self._generate_activation_hash(card_key)
        }
        json_str = json.dumps(data, separators=(',', ':'))
        return base64.b64encode(json_str.encode()).decode()
    
    def _decode_activation_data(self, encoded):
        try:
            json_str = base64.b64decode(encoded.encode()).decode()
            return json.loads(json_str)
        except:
            return None
    
    def save_activation(self, card_key):
        try:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            encoded_data = self._encode_activation_data(card_key, timestamp)
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REGISTRY_PATH,
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, self.REGISTRY_NAME, 0, winreg.REG_SZ, encoded_data)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"保存激活信息失败: {e}")
            return False
    
    def check_activation(self):
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REGISTRY_PATH,
                0,
                winreg.KEY_READ
            )
            encoded_data, _ = winreg.QueryValueEx(key, self.REGISTRY_NAME)
            winreg.CloseKey(key)
            
            data = self._decode_activation_data(encoded_data)
            if not data:
                return False, "激活数据损坏"
            
            if data.get("mid") != self.machine_id:
                return False, "机器码不匹配"
            
            return True, "已激活"
            
        except FileNotFoundError:
            return False, "未激活"
        except Exception as e:
            return False, f"验证错误: {e}"
    
    def clear_activation(self):
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REGISTRY_PATH,
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.DeleteValue(key, self.REGISTRY_NAME)
            winreg.CloseKey(key)
            return True
        except:
            return False
    
    def get_machine_id_display(self):
        return f"{self.machine_id[:8]}-{self.machine_id[8:16]}-{self.machine_id[16:24]}-{self.machine_id[24:32]}"
    
    def _init_trial(self):
        try:
            trial_data = {
                "mid": self.machine_id,
                "remaining": self.TRIAL_COUNT,
                "total": self.TRIAL_COUNT
            }
            encoded = base64.b64encode(json.dumps(trial_data, separators=(',', ':')).encode()).decode()
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REGISTRY_PATH,
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, self.TRIAL_REGISTRY_NAME, 0, winreg.REG_SZ, encoded)
            winreg.CloseKey(key)
            return True
        except:
            return False
    
    def get_trial_status(self):
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REGISTRY_PATH,
                0,
                winreg.KEY_READ
            )
            encoded_data, _ = winreg.QueryValueEx(key, self.TRIAL_REGISTRY_NAME)
            winreg.CloseKey(key)
            
            data = json.loads(base64.b64decode(encoded_data.encode()).decode())
            
            if data.get("mid") != self.machine_id:
                return False, 0, "机器码不匹配"
            
            remaining = data.get("remaining", 0)
            total = data.get("total", self.TRIAL_COUNT)
            
            return True, remaining, total
        except FileNotFoundError:
            return True, self.TRIAL_COUNT, self.TRIAL_COUNT
        except Exception as e:
            return False, 0, self.TRIAL_COUNT
    
    def check_trial(self):
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REGISTRY_PATH,
                0,
                winreg.KEY_READ | winreg.KEY_SET_VALUE
            )
            encoded_data, _ = winreg.QueryValueEx(key, self.TRIAL_REGISTRY_NAME)
            
            data = json.loads(base64.b64decode(encoded_data.encode()).decode())
            
            if data.get("mid") != self.machine_id:
                winreg.CloseKey(key)
                return False, 0, "机器码不匹配"
            
            remaining = data.get("remaining", 0)
            
            if remaining <= 0:
                winreg.CloseKey(key)
                return False, 0, "试用次数已用完"
            
            remaining -= 1
            data["remaining"] = remaining
            encoded = base64.b64encode(json.dumps(data, separators=(',', ':')).encode()).decode()
            winreg.SetValueEx(key, self.TRIAL_REGISTRY_NAME, 0, winreg.REG_SZ, encoded)
            winreg.CloseKey(key)
            
            return True, remaining, f"剩余 {remaining} 次启动"
            
        except FileNotFoundError:
            if self._init_trial():
                return True, self.TRIAL_COUNT, f"试用期开始，剩余 {self.TRIAL_COUNT} 次启动"
            return False, 0, "无法启动试用"
        except Exception as e:
            return False, 0, f"试用验证错误: {e}"
    
    def _update_last_check(self):
        pass
    
    def check_license_or_trial(self):
        is_activated, msg = self.check_activation()
        if is_activated:
            return True, "已激活", "activated"
        
        is_trial, remaining, trial_msg = self.check_trial()
        if is_trial:
            return True, trial_msg, "trial"
        
        return False, msg, "none"
    
    def should_show_activation_dialog(self):
        today = datetime.now().strftime("%Y%m%d")
        
        is_activated, _ = self.check_activation()
        if is_activated:
            return False
        
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REGISTRY_PATH,
                0,
                winreg.KEY_READ
            )
            encoded_data, _ = winreg.QueryValueEx(key, self.TRIAL_REGISTRY_NAME)
            winreg.CloseKey(key)
            
            data = json.loads(base64.b64decode(encoded_data.encode()).decode())
            last_dialog_date = data.get("last_dialog_date", "")
            
            if last_dialog_date == today:
                return False
            
        except FileNotFoundError:
            pass
        except Exception:
            pass
        
        return True
    
    def mark_dialog_shown_today(self):
        today = datetime.now().strftime("%Y%m%d")
        
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REGISTRY_PATH,
                0,
                winreg.KEY_READ | winreg.KEY_SET_VALUE
            )
            
            try:
                encoded_data, _ = winreg.QueryValueEx(key, self.TRIAL_REGISTRY_NAME)
                data = json.loads(base64.b64decode(encoded_data.encode()).decode())
            except FileNotFoundError:
                data = {
                    "mid": self.machine_id,
                    "remaining": self.TRIAL_COUNT,
                    "total": self.TRIAL_COUNT
                }
            
            data["last_dialog_date"] = today
            encoded = base64.b64encode(json.dumps(data, separators=(',', ':')).encode()).decode()
            winreg.SetValueEx(key, self.TRIAL_REGISTRY_NAME, 0, winreg.REG_SZ, encoded)
            winreg.CloseKey(key)
            
        except Exception as e:
            print(f"记录弹窗日期失败: {e}")
