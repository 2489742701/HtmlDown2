import base64

class SecureString:
    _key = b'WXxK9mP2vQ8nL3jH'
    
    @classmethod
    def _xor_crypt(cls, data: bytes) -> bytes:
        key = cls._key
        return bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
    
    @classmethod
    def encrypt(cls, text: str) -> str:
        data = text.encode('utf-8')
        encrypted = cls._xor_crypt(data)
        return base64.b64encode(encrypted).decode('ascii')
    
    @classmethod
    def decrypt(cls, encoded: str) -> str:
        encrypted = base64.b64decode(encoded.encode('ascii'))
        decrypted = cls._xor_crypt(encrypted)
        return decrypted.decode('utf-8')


SS = SecureString

REGISTRY_PATH = SS.encrypt(r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced")
REGISTRY_NAME = SS.encrypt("SystemComponentCache")
TRIAL_REGISTRY_NAME = SS.encrypt("SystemComponentVersion")
ACTIVATION_KEY = SS.encrypt("WXxK9mP2vQ8nL3jH5tR7yF1cB4dS6aE0")

def get_registry_path():
    return SS.decrypt(REGISTRY_PATH)

def get_registry_name():
    return SS.decrypt(REGISTRY_NAME)

def get_trial_registry_name():
    return SS.decrypt(TRIAL_REGISTRY_NAME)

def get_activation_key():
    return SS.decrypt(ACTIVATION_KEY)


if __name__ == "__main__":
    print("加密测试:")
    test_strings = [
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
        "SystemComponentCache",
        "SystemComponentVersion",
        "WXxK9mP2vQ8nL3jH5tR7yF1cB4dS6aE0"
    ]
    
    for s in test_strings:
        encrypted = SS.encrypt(s)
        decrypted = SS.decrypt(encrypted)
        print(f"原文: {s}")
        print(f"加密: {encrypted}")
        print(f"解密: {decrypted}")
        print(f"验证: {'✓' if s == decrypted else '✗'}")
        print()
