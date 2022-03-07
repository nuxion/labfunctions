import httpx

SLACK_API = "https://slack.com/api/"
EMOJI_ERROR = "🤬"
EMOJI_OK = "👌"


class SlackCient:
    def __init__(self, tkn):
        self._headers = {"Authorization": f"Bearer {tkn}"}

    def list_channels(self):
        r = httpx.get(f"{SLACK_API}/conversations.list", headers=self._headers)
        return r.json()

    def send(self, channel, text):
        r = httpx.post(
            f"{SLACK_API}/chat.postMessage",
            headers=self._headers,
            data=dict(channel=channel, text=text),
        )
        return r.json()


class DiscordClient:
    def __init__(self, tkn=None):
        pass

    def send(self, channel, text, username="NB Workflows"):
        r = httpx.post(channel, json={"content": text, "username": username})
        return r.text
