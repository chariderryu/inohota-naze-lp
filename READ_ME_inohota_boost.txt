
inohota_boost （LP販促ブースト：今日の注目章＋追従ミニ商品カード）
====================================================================

■ 置き方（index.htmlと同じフォルダ推奨）
  - inohota_boost.css
  - inohota_boost.js

■ index.html への追記（<head> 内と </body> 直前）
  <link rel="stylesheet" href="inohota_boost.css">
  ...
  <script src="inohota_boost.js" defer></script>

■ これでできること
  1) 「本日の注目章」を自動生成して、#about の前（なければcontainer冒頭）に追加
     - 既存の .topics-grid .topic-card から1件を“日替わり”で選んで表示
     - ロジックはUTC基準 (2025-01-01 起点)

  2) 追従ミニ商品カード（30%スクロールで表示）
     - 最小化（—）・閉じる（×）対応、閉じた日は再表示しません（localStorage）
     - フッター手前で自動的に下マージンを拡大して干渉を回避
     - 既存の .floating-cta と干渉しない位置（bottom:100px）

■ 画像とURL
  - 書影: ../lib/inohotanaze_front_cover_small.jpg
  - Amazon: https://amzn.to/4nmDn6Y
  - 楽天   : https://books.rakuten.co.jp/rb/18063859/

  ※ パスやURLを変える場合：inohota_boost.js の先頭設定を編集してください。

■ 既存DOMに依存する箇所（index.html由来）
  - .topics-grid .topic-card 内の <h3> と最初の <a href> を使用しており、
    “本日の注目章”は既存カードのクローンで描画されます。

■ 既知の注意
  - 1ページ内に topics-grid が無い場合は“本日の注目章”はスキップされます。
  - 既に #todays-pick セクションがある場合は、そこへ描画します。

