"""Download Kaggle dataset: synthetic-banking-dataset-csv-sql-sqlite.
Requires kaggle.json in ~/.kaggle/ (or env KAGGLE_USERNAME / KAGGLE_KEY).

Lưu vào raw_kaggle/ (đồng bộ với transform_kaggle_data.py).
Nếu thư mục đã có CSV thì có thể bỏ qua bước này.
"""
import os, subprocess, sys

DATASET = "akrambelha/synthetic-banking-dataset-csv-sql-sqlite"
OUT = os.path.join(os.path.dirname(__file__), "raw_kaggle")


def main():
    os.makedirs(OUT, exist_ok=True)
    try:
        import kaggle  # noqa
    except ImportError:
        print("Installing kaggle...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "kaggle"])
    subprocess.check_call(
        ["kaggle", "datasets", "download", "-d", DATASET, "-p", OUT, "--unzip"]
    )
    print(f"✅ Downloaded to {OUT}")


if __name__ == "__main__":
    main()
