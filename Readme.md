## 前準備
### flaskのインストール
`pip install flask`

### python-slack-events-apiをインストールする
`pip install slackeventsapi`


### Event Subscriptionsにフック先のURLを登録する

- slackアプリのEvent Subscriptionsを開いて、Request Eventsにさっき立ち上げたサーバのエンドポイントを登録する
- baseURL + /slack/eventsというように、Flaskのslack_events_adapteに登録したリソースと同じように入力する

https://api.slack.com/apps


> 参考 https://qiita.com/0ba/items/f5f46af0364efd843295