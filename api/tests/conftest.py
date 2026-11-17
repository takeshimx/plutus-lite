import os

# app.main はインポート時に設定を読むため、テスト用の値を先に入れる
os.environ.setdefault("GCP_PROJECT_ID", "demo-test")
