import httpx

SLACK_API = "https://slack.com/api/"
DISCORD_API = "https://discord.com/api/webhooks/"
EMOJI_ERROR = "🤬"
EMOJI_OK = "👌"


class SlackCient:
    def __init__(self, tkn, addr=SLACK_API):
        self._headers = {"Authorization": f"Bearer {tkn}"}
        self._addr = addr

    def list_channels(self):
        r = httpx.get(f"{self._addr}/conversations.list", headers=self._headers)
        return r.json()

    def send(self, channel, text):
        r = httpx.post(
            f"{self._addr}/chat.postMessage",
            headers=self._headers,
            data=dict(channel=channel, text=text),
        )
        return r.json()


class DiscordClient:
    def __init__(self, addr=DISCORD_API):
        self._addr = addr

    def send(self, channel, text, username="NB Workflows"):
        fullurl = f"{self._addr}{channel}"
        r = httpx.post(fullurl, json={"content": text, "username": username})
        return r.text
