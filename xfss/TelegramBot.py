import os

import requests


class TelegramBot:
	def __init__(self, groupId: str):
		self.groupId = groupId
		self.messages: list = []
		self.url: str = os.getenv("TELEGRAM_URL")
		self.complete_url = self.url + self.groupId + "&text="

	def add_message(self, message: str) -> None:
		self.messages.append(message + "\n")

	def send(self, message: str = None) -> None:
		payload = None
		if message is None and len(self.messages) > 0:
			for single_message in self.messages:
				payload = self.complete_url + single_message
			self.messages.clear()
		else:
			payload = self.complete_url + message
		if payload is not None:
			requests.get(payload)
