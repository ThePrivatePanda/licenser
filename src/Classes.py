from pydantic import BaseModel
from typing import Literal, Union, Optional
import json


class New(BaseModel):
	limit_type: Literal["time_limit", "accounts_limit"]
	script: Literal["twitter_gen", "discord_gen", "twitter_tools", "discord_tools"]
	expire_limit: int
	generation_time: int

class Validate(BaseModel):
	script: Literal["twitter_gen", "discord_gen", "twitter_tools", "discord_tools"]
	hwid: str

class Update(BaseModel):
	expire_limit: int

class Activate(BaseModel):
	script: Literal["twitter_gen", "discord_gen", "twitter_tools", "discord_tools"]
	hwid: str

class Config:
	def __init__(self, fn: str) -> None:
		self.fn: str = fn
		self.config: dict = json.load(open(fn))

	def update(self, key: Union[dict, str], value: Union[dict, str, int, list]) -> None:
		self.config[key] = value
		json.dump(self.config, open(self.fn, "w"))

	def get(self, key: Union[str, dict]) -> Optional[Union[dict, str, int, list]]:
		self.config = json.load(open(self.fn))
		return self.config.get(key, None)
