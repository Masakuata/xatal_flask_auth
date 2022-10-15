import threading
from datetime import datetime
from functools import update_wrapper
from time import sleep

from flask import request, Response

from xf_auth.Auth import Auth
from xf_auth.HTTPStatus import UNAUTHORIZED, SESSION_EXPIRED, FORBIDDEN
from xf_auth.TelegramBot import TelegramBot


class StatefulSession:
	r"""
	A helper class to handle sessions from remote clients through HTTP.

	You can set the lifetime of the session in seconds like this:

	>>> # Setting the session lifetime to 5 minutes
	>>> StatefulSession.set_session_lifetime(300)

	Create a new session with the following code:

	>>> user = {"email": "mail@mail", "password": "g00dP4ssw0rD", "role": "admin"}
	>>> session_token = StatefulSession.new_session(user)

	Documentation still on the works.
	If you need any help, do not think twice about writing an email to:

	edsonmanuelcarballovera@gmail.com

	or look for me on Twitter at:

	@EdsonManuelVera

	:copyright: (c) 2022 by Edson Manuel Carballo Vera
	:license: MIT.
	"""
	session: list = []
	session_lifetime: int = 600

	@staticmethod
	def set_session_lifetime(seconds: int) -> None:
		r"""Set the amount of seconds a session should last alive without interaction.

		:param seconds:The amount of seconds until the session is deleted.
		:raises TypeError: If the value provided is invalid or None.
		:raises ValueError: If the amount of seconds is below 60 or above 1,800.
		No session should last less than a minute or more than half an hour.
		"""
		if type(seconds) != int:
			if 60 <= seconds <= 1_800:
				StatefulSession.session_lifetime = seconds
			else:
				raise ValueError("Session lifetime should be between 60 and 1,800 seconds")
		else:
			raise TypeError("The value provided is not valid")

	@staticmethod
	def new_session(data: dict) -> str:
		r"""Creates a new session and stores the provided data.

		:param data: The data to save along the session.
		:return: A session token. You should pass it to the client. He will need it later.
		"""
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
		r"""THIS METHOD IS NOT SUPPOSED TO BE USED FROM THE OUTSIDE.

		STEP BACK.
		"""
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
		r"""Returns the session stored data

		:param token: The session token provided when the session was started.
		:param stateless: This param is not in use yet.
		:return: A dict with the stored data.
		None if the session does not exist.
		"""
		data: dict or None = None
		for session in StatefulSession.session:
			if session["token"] == token:
				data = session["data"]
				break
		# if data is None and stateless:
		# 	data = Auth.decode_token(token)
		return data

	@staticmethod
	def get_session(token: str) -> dict or None:
		r"""Returns the whole session, including the token and the start timestamp.

		:param token: The session token provided when the session was started.
		:return: A dict with the token, the session data and the session start timestamp.
		"""
		session: dict or None = None
		for saved_session in StatefulSession.session:
			if saved_session["token"] == token:
				session = saved_session
				break
		return session

	@staticmethod
	def delete_session(token: str) -> bool:
		r"""Deletes a session.

		THIS ACTION IS DESTRUCTIVE AND CANNOT BE REVERTED.

		:param token: The session token provided when the session was started.
		:return: A boolean indicating if the session was deleted successfully or not.
		Any way, after this action, the session should be considered gone.
		If you do not delete the session, the session reaper will.
		"""
		deleted: bool = False
		stored_session: dict = StatefulSession.get_session(token)
		if stored_session is not None:
			StatefulSession.session.remove(stored_session)
			deleted = True
		return deleted

	@staticmethod
	def requires_token(operation):
		r""" Use this oneliner decorator to indicate that a route operation requires a token to be processed.

		If the token is not present, adequate responses will be sent according to the case.
		"""

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
		r"""Use this oneliner decorator to indicate that a route operation requires a specific user role to be processed.
		If you use this, there is no need to use StatefulSession.requires_token.
		If the token is not present, or the user role does not match, adequate responses will be sent according to the case.
		"""

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
		r"""THIS METHOD IS NOT SUPPOSED TO BE USED FROM THE OUTSIDE.

		STEP BACK.
		"""
		token: str or None = None
		for session in StatefulSession.session:
			if session["data"]["email"] == data["email"] and session["data"]["password"] == data["password"]:
				token = session["token"]
		return token

	@staticmethod
	def __is_session_in(data: dict) -> bool:
		r"""THIS METHOD IS NOT SUPPOSED TO BE USED FROM THE OUTSIDE.

		STEP BACK.
		"""
		is_in: bool = False
		if data is not None:
			for session in StatefulSession.session:
				if session["data"]["email"] == data["email"] and session["data"]["password"] == data["password"]:
					is_in = True
					break
		return is_in


class SessionGarbageCollector:
	r"""
	THIS CLASS IS NOT SUPPOSED TO BE USED FROM THE OUTSIDE.

	STEP BACK.
	"""
	is_running: bool = False
	bot: TelegramBot = TelegramBot("xf_session")

	@staticmethod
	def start_collection() -> None:
		r"""THIS METHOD IS NOT SUPPOSED TO BE USED FROM THE OUTSIDE.

		STEP BACK.
		"""
		SessionGarbageCollector.is_running = True

		while len(StatefulSession.session) > 0:
			SessionGarbageCollector.notify_session_count()
			now = datetime.now()
			for session in StatefulSession.session:
				session_time = (now - session["session_start"]).total_seconds()
				if session_time > StatefulSession.session_lifetime:
					StatefulSession.session.remove(session)
			sleep(180)
		SessionGarbageCollector.is_running = False

	@staticmethod
	def notify_session_count():
		r"""THIS METHOD IS NOT SUPPOSED TO BE USED FROM THE OUTSIDE.

		STEP BACK.
		"""
		count: int = len(StatefulSession.session)
		message: str = f"{count} active sessions"
		SessionGarbageCollector.bot.send(message)
