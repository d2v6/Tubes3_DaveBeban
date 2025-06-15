import os
import time
import random


class MasterKeyGenerator:
    def __init__(self):
        self.charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*_+-=,.?"

    def _get_entropy_sources(self):
        entropy_data = []

        current_time = time.time()
        entropy_data.append(int(current_time * 1000000))

        try:
            entropy_data.append(os.getpid())
        except:
            entropy_data.append(12345)

        temp_objects = [[], {}, set(), "entropy"]
        for obj in temp_objects:
            entropy_data.append(id(obj))

        try:
            if hasattr(os, 'urandom'):
                random_bytes = os.urandom(8)
                for byte in random_bytes:
                    entropy_data.append(byte)
        except:
            for i in range(8):
                entropy_data.append(int(time.time() * 1000000 + i) % 256)

        return entropy_data

    def generate_master_key(self, length=64):
        key_chars = []

        key_chars.append(random.choice(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
        key_chars.append(random.choice(
            "abcdefghijklmnopqrstuvwxyz"))
        key_chars.append(random.choice("0123456789")
                         )

        for _ in range(length - len(key_chars)):
            key_chars.append(random.choice(self.charset))

        random.shuffle(key_chars)

        return ''.join(key_chars)


def main():
    generator = MasterKeyGenerator()
    print("Generating master key...")
    master_key = generator.generate_master_key(length=64)
    print("Printing master key...")
    print(master_key)


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
