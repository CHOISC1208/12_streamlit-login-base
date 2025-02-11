# Streamlit マルチページアプリケーション

## 概要
このアプリケーションは、Streamlitを使用したマルチページWebアプリケーションの基本構造を提供します。ログイン機能を備え、複数のページを持つダッシュボード形式のアプリケーションです[1]。

## 機能
- ユーザー認証（ログイン/ログアウト）
- サイドバーによるナビゲーション
- 5つの独立したページ構成
- ファイルアップロード機能

## 必要なパッケージ
- streamlit
- streamlit-option-menu
- pyyaml
- pandas
- streamlit-aggrid

- ## ログイン設定
`configs/login.yaml`に以下のようにユーザー認証情報を設定します[1]：

```yaml
login:
  users:
    - username: user1
      password: pass1
    - username: user2
      password: pass2
```
