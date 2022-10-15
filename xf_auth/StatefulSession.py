import threading
from datetime import datetime
from functools import update_wrapper
from time import sleep

from flask import request, Response

from xf_auth.Auth import Auth
from xf_auth.HTTPStatus import UNAUTHORIZED, SESSION_EXPIRED, FORBIDDEN
from xf_auth.TelegramBot import TelegramBot


class StatefulSession:
	session: list = []
	session_lifetime: int = 6_000

	@staticmethod
	def new_session(data: dict) -> str or None:
		stored_token = StatefulSession.__get_token_from_data(data)
		if stored_token is not None:
			return stored_token

		token: str = StatefulSession.__new_token(data)
		StatefulSession.session.append({
			"token": token,
			"data": data,
			"session_start": datetime.now()
		})
		if not SessionGarbageCollector.is_running:
			threading.Thread(target=SessionGarbageCollector.start_collection).start()
		return token

	@staticmethod
	def __new_token(data: dict) -> str:
		if Auth.class_name is not None:
			aux_obj = Auth.class_name()
			for key, value in data.items():
				if key in aux_obj.__dict__:
					aux_obj.__setattr__(key, value)
				else:
					raise AttributeError("Attribute is not part of provided User origin class")
			return Auth.generate_token(aux_obj)
		else:
			raise TypeError("User origin is not set. Set it before setting user keys with Auth.set_user_origin")

	@staticmethod
	def get_data(token: str, stateless: bool = False) -> dict or None:
		data: dict or None = None
		for session in StatefulSession.session:
			if session["token"] == token:
				data = session["data"]
				break
		if data is None and stateless:
			data = Auth.decode_token(token)
		return data

	@staticmethod
	def get_session(token: str) -> dict or None:
		session: dict or None = None
		for saved_session in StatefulSession.session:
			if saved_session["token"] == token:
				session = saved_session
				break
		return session

	@staticmethod
	def delete_session(token: str) -> bool:
		deleted: bool = False
		stored_session: dict = StatefulSession.get_session(token)
		if stored_session is not None:
			StatefulSession.session.remove(stored_session)
			deleted = True
		return deleted

	@staticmethod
	def requires_token(operation):
		def verify_auth(*args, **kwargs):
			token = request.headers.get("token")
			if token is not None:
				session = StatefulSession.get_session(token)
				if session is not None:
					now = datetime.now()
					if (now - session["session_start"]).total_seconds() < StatefulSession.session_lifetime:
						session["session_start"] = now
						response = operation(*args, **kwargs)
					else:
						StatefulSession.delete_session(token)
						response = Response(status=SESSION_EXPIRED)
				else:
					response = Response(status=UNAUTHORIZED)
			else:
				response = Response(status=UNAUTHORIZED)
			return response

		return update_wrapper(verify_auth, operation)

	@staticmethod
	def requires_role(role: str):
		def decorator(operation):
			def verify_role(*args, **kwargs):
				if Auth.role_attribute is not None:
					token = request.headers.get("token")
					if token is not None:
						session = StatefulSession.get_session(token)
						if session is not None:
							now = datetime.now()
							if (now - session["session_start"]).total_seconds() < StatefulSession.session_lifetime:
								if str(session["data"][Auth.role_attribute]).lower() == role.lower():
									session["session_start"] = now
									response = operation(*args, **kwargs)
								else:
									response = Response(status=FORBIDDEN)
							else:
								response = Response(status=SESSION_EXPIRED)
						else:
							response = Response(status=SESSION_EXPIRED)
					else:
						response = Response(status=UNAUTHORIZED)
				else:
					raise TypeError(
						"User role attribute is not set. Set it with Auth.set_role_attribute")
				return response

			return update_wrapper(verify_role, operation)

		return decorator

	@staticmethod
	def __get_token_from_data(data: dict) -> str or None:
		token: str or None = None
		for session in StatefulSession.session:
			if session["data"]["email"] == data["email"] and session["data"]["password"] == data["password"]:
				token = session["token"]
		return token

	@staticmethod
	def __is_session_in(data: dict) -> bool:
		is_in: bool = False
		if data is not None:
			for session in StatefulSession.session:
				if session["data"]["email"] == data["email"] and session["data"]["password"] == data["password"]:
					is_in = True
					break
		return is_in


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
