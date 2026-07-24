# easy_honey_bot
HTTP型ハニーボット README
============================

1. 目的
このプログラムは、管理者ログイン画面に見せかけた教育用のHTTPハニーボットです。
ブラウザからアクセスするとログイン画面を表示し、入力されたユーザー名、
パスワード、接続元IPアドレス、ポート番号、アクセス先をログへ記録します。

実際の認証処理は行わず、入力内容に関係なく403 Forbiddenと
「Login Failed」を返します。

授業で扱った次の内容を応用しています。

・http.server
・socketserver
・クラスとメソッド
・str型のstrip、replace、startswith、isdigit、format
・UTF-8のencode、decode
・logging
・if文、try文、with文

---動作環境---
・Python 3.9以上を推奨
・macOS、Windows、Linux

フォルダ構成
web_honeybot/
  honeyserver.py
  config.txt
  README.txt
  TEST_REPORT.txt
  logs/
    access.log
  test_client.py

---起動方法---
ターミナルまたはコマンドプロンプトでweb_honeybotフォルダへ移動します。

macOS / Linux:
  cd web_honeybot
  python3 honeyserver.py

Windows:
  cd web_honeybot
  python honeyserver.py

次の表示が出れば起動成功している。

  *** START HTTP HONEYBOT ***
  URL: http://127.0.0.1:18080

---ブラウザによる確認
ブラウザで次のURLを開き

  http://127.0.0.1:18080

ログイン画面が表示されたら、テスト用の値を入力。

例:
  User ID: test_student
  Password: qwerty1234

Loginボタンを押すと、Login Failedが表示される。

curlによる確認
GET確認:
  curl -i http://127.0.0.1:18080/

POST確認:
  curl -i -X POST \
    -d "username=test_student&password=qwerty1234" \
    http://127.0.0.1:18080/login

テストクライアントによる確認
サーバーを起動したまま、別のターミナルで実行。

macOS / Linux:
  python3 test/test_client.py

Windows:
  python test/test_client.py

正常時の例:
  GET status: 200
  login form: True
  POST status: 403
  failed page: True

ログの確認
ログは次のファイルへ保存される。

  logs/access.log

ログ例:
  2026-07-23 21:00:00,000 [INFO] HTTPハニーボット起動 host=127.0.0.1 port=18080
  2026-07-23 21:00:05,000 [INFO] GET address=127.0.0.1 port=50000 path=/
  2026-07-23 21:00:15,000 [DEBUG] LOGIN address=127.0.0.1 port=50001 user='test_student' password='pass1234' path=/login

終了方法
サーバーを実行している画面でCtrl+Cを押す。

11. 主な文字列処理
safe_text関数では、ログに改行文字がそのまま入らないように
replaceとstripを使用。

  text = text.replace("\r", "\\r")
  text = text.replace("\n", "\\n")
  text = text.strip()

POSTデータはbyte型で受け取るため、decodeでstr型へ戻している。

  post_text = post_bytes.decode("utf-8")

HTMLはstr型なので、送信前にencodeでbyte型へ変換している。

  response_bytes = html_text.encode("utf-8")


