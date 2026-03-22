"""
调试脚本 - 检查注册表中的原始数据
"""
import winreg
import sys

# 注册表路径
REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
TRIAL_NAME = "SystemComponentVersion"
ACTIVATION_NAME = "SystemComponentCache"

def check_raw_bytes():
    """检查注册表中的原始字节数据"""
    print("=" * 70)
    print("注册表原始数据检查")
    print("=" * 70)
    print()

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_READ
        )

        # 检查试用数据
        print("【试用数据】")
        try:
            # 使用 EnumValue 获取原始数据
            i = 0
            while True:
                try:
                    name, value, value_type = winreg.EnumValue(key, i)
                    if name == TRIAL_NAME:
                        print(f"  值名: {name}")
                        print(f"  值类型: {value_type}")
                        print(f"  数据类型: {type(value)}")

                        if isinstance(value, str):
                            print(f"  字符串长度: {len(value)}")
                            print(f"  字符串repr: {repr(value[:100])}")

                            # 检查每个字符
                            null_count = value.count('\x00')
                            if null_count > 0:
                                print(f"  ⚠️ 包含 {null_count} 个 null 字符！")

                            # 检查其他控制字符
                            ctrl_chars = [(j, ord(c)) for j, c in enumerate(value) if ord(c) < 32 or ord(c) > 126]
                            if ctrl_chars:
                                print(f"  ⚠️ 发现 {len(ctrl_chars)} 个非法字符:")
                                for pos, code in ctrl_chars[:10]:
                                    print(f"    位置 {pos}: ord={code}")
                            else:
                                print(f"  ✓ 所有字符都是可打印ASCII")

                        elif isinstance(value, bytes):
                            print(f"  字节长度: {len(value)}")
                            print(f"  原始字节: {value[:50]}")
                            print(f"  hex: {value[:50].hex()}")

                            # 尝试不同编码解码
                            for encoding in ['utf-8', 'gbk', 'latin-1', 'utf-16']:
                                try:
                                    decoded = value.decode(encoding)
                                    print(f"  尝试 {encoding} 解码: {repr(decoded[:50])}")
                                    break
                                except:
                                    pass

                        break
                    i += 1
                except OSError:
                    break

        except Exception as e:
            print(f"  错误: {e}")

        print()

        # 检查激活数据
        print("【激活数据】")
        try:
            i = 0
            while True:
                try:
                    name, value, value_type = winreg.EnumValue(key, i)
                    if name == ACTIVATION_NAME:
                        print(f"  值名: {name}")
                        print(f"  值类型: {value_type}")
                        print(f"  数据类型: {type(value)}")

                        if isinstance(value, str):
                            print(f"  字符串长度: {len(value)}")
                            print(f"  字符串repr: {repr(value[:100])}")

                            null_count = value.count('\x00')
                            if null_count > 0:
                                print(f"  ⚠️ 包含 {null_count} 个 null 字符！")

                            ctrl_chars = [(j, ord(c)) for j, c in enumerate(value) if ord(c) < 32 or ord(c) > 126]
                            if ctrl_chars:
                                print(f"  ⚠️ 发现 {len(ctrl_chars)} 个非法字符:")
                                for pos, code in ctrl_chars[:10]:
                                    print(f"    位置 {pos}: ord={code}")
                            else:
                                print(f"  ✓ 所有字符都是可打印ASCII")

                        elif isinstance(value, bytes):
                            print(f"  字节长度: {len(value)}")
                            print(f"  原始字节: {value[:50]}")

                        break
                    i += 1
                except OSError:
                    break

        except Exception as e:
            print(f"  错误: {e}")

        winreg.CloseKey(key)

    except Exception as e:
        print(f"❌ 打开注册表失败: {e}")

    print()
    print("=" * 70)

if __name__ == "__main__":
    check_raw_bytes()
    input("\n按回车键退出...")
