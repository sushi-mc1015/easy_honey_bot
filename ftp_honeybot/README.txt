HoneyFTP（教育用FTP風ハニーボット）
====================================

1. 目的
------
このプログラムは、FTPサーバーのような応答を返し、接続元、入力された認証情報、
FTP風コマンドをJSON Lines形式で記録する教育用ハニーボットです。
実際のファイル操作、OSコマンド実行、認証処理は行いません。

元資料のTelnet風ハニーボットとの差異：
・FTP風プロトコル（USER / PASS / PWD / LISTなど）を模擬
・複数クライアントを非同期処理
・YAML設定ファイルによりポートやタイムアウトを変更可能
・ログを解析しやすいJSON Lines形式で保存
・長すぎる入力、切断、タイムアウトも記録
・自動機能テストと単体テストを同梱

2. 安全上の注意
--------------
初期設定は host=127.0.0.1、port=2121 です。ローカルPC内だけで試験してください。
大学・会社・自宅のルーターで外部公開しないでください。
実在するIDやパスワードを入力しないでください。
ログには入力した認証情報が平文で残るため、提出前に内容を確認してください。

3. フォルダ構成
--------------
ftp_honeybot/
├── honeyftp.py                 実行プログラム
├── config.yaml                設定データ
├── requirements.txt           必要ライブラリ
├── README.txt                 操作手順書
├── TEST_REPORT.txt            テスト仕様・結果報告書
├── logs/
│   └── access.jsonl           実行時に生成されるログ
└── tests/
    ├── test_client.py         ローカル機能テスト
    └── test_unit.py           単体テスト

4. 必要環境
----------
・Python 3.10以上
・macOS / Windows / Linux
・PyYAML 6.0.2

5. セットアップ手順
------------------
【macOS / Linux】
1) ターミナルで本フォルダへ移動
   cd ftp_honeybot

2) 仮想環境を作成
   python3 -m venv .venv

3) 仮想環境を有効化
   source .venv/bin/activate

4) ライブラリをインストール
   python -m pip install -r requirements.txt

【Windows PowerShell】
1) 本フォルダへ移動
   cd ftp_honeybot

2) 仮想環境を作成・有効化
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1

3) ライブラリをインストール
   python -m pip install -r requirements.txt

6. 実行手順
----------
1) サーバーを起動
   python honeyftp.py --config config.yaml

2) 別のターミナルで機能テストを実行
   python tests/test_client.py

3) サーバーを停止
   起動側のターミナルで Ctrl+C

4) ログを確認
   macOS / Linux: cat logs/access.jsonl
   Windows:       Get-Content logs/access.jsonl

7. 手動接続例
------------
netcatが使用できる場合：
   nc 127.0.0.1 2121

接続後の入力例：
   USER student
   PASS test-password
   PWD
   LIST
   RETR backup.zip
   QUIT

8. 単体テスト
------------
プロジェクト直下で次を実行：
   python -m unittest discover -s tests -p "test_unit.py" -v

9. 設定ファイル
--------------
config.yaml の主な設定：
・host: 待受アドレス。安全のため127.0.0.1を推奨
・port: 待受ポート。2121など1024より大きい値を推奨
・idle_timeout_seconds: 無操作切断までの秒数
・max_command_length: 1行の最大長
・log_file: ログ保存先

10. ログ例
---------
{"timestamp":"2026-07-23T12:00:00.000+00:00","event":"connection_opened","client_ip":"127.0.0.1","client_port":50000}
{"timestamp":"2026-07-23T12:00:01.000+00:00","event":"credential_submitted","client_ip":"127.0.0.1","client_port":50000,"username":"student","password":"test-password"}
{"timestamp":"2026-07-23T12:00:02.000+00:00","event":"command_received","client_ip":"127.0.0.1","client_port":50000,"command":"RETR","argument":"backup.zip"}

11. 終了コード
-------------
0: 正常終了
1: 設定不備、ポート使用中などによる起動失敗
