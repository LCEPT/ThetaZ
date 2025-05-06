#!/usr/bin/env python3
import OpenEXR
import sys

def print_exr_header(exr_path):
    """
    指定した EXR ファイルのヘッダ情報をターミナルに表示する
    """
    try:
        exr = OpenEXR.InputFile(exr_path)
    except Exception as e:
        sys.exit(f"Error opening EXR file '{exr_path}': {e}")

    hdr = exr.header()  # ヘッダは dict として取得できる
    print(f"--- Header for '{exr_path}' ---")
    for key, val in hdr.items():
        print(f"{key}: {val}")
    exr.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path/to/file.exr>")
        sys.exit(1)

    exr_file = sys.argv[1]
    print_exr_header(exr_file)
