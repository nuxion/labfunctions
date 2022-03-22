from pydantic import BaseModel


class AgentReq(BaseModel):
    agent_name: str
