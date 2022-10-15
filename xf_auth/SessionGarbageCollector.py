from datetime import datetime
from time import sleep

from xf_auth.StatefulSession import StatefulSession
from xf_auth.TelegramBot import TelegramBot


class SessionGarbageCollector:
	is_running: bool = False
	bot: TelegramBot = TelegramBot("xf_session")

	@staticmethod
	def start_collection() -> None:
		SessionGarbageCollector.is_running = True

		while len(StatefulSession.session) > 0:
			SessionGarbageCollector.notify_session_count()
			now = datetime.now()
			for session in StatefulSession.session:
				if (now - session["session_start"]).total_seconds() > StatefulSession.session_lifetime:
					StatefulSession.session.remove(session)
			sleep(180)
		SessionGarbageCollector.is_running = False

	@staticmethod
	def notify_session_count():
		count: int = len(StatefulSession.session)
		message: str = f"{count} active sessions"
		SessionGarbageCollector.bot.send(message)
