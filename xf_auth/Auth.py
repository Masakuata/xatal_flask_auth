from datetime import datetime
from functools import update_wrapper
from typing import Type

from cryptography.fernet import Fernet
from flask import Response, request, session
from werkzeug.security import generate_password_hash, check_password_hash

from xf_auth.HTTPStatus import UNAUTHORIZED, SESSION_EXPIRED, FORBIDDEN, NOT_ACCEPTABLE
from xf_auth.Util import decode, included, encode


class Auth:
	secret_password: bytes = None
	class_name: Type[object] = None
	user_keys: list = None
	role_attribute: str = None

	@staticmethod
	def set_password():
		Auth.secret_password = Fernet.generate_key()

	@staticmethod
	def set_user_origin(class_name: Type[object]) -> None:
		Auth.class_name = class_name

	@staticmethod
	def set_user_keys(keys: list) -> None:
		if Auth.class_name is not None:
			aux = Auth.class_name()
			keys.sort()
			for key in keys:
				try:
					aux.__getattribute__(key)
				except AttributeError as exception:
					raise Exception(
						"Attribute not in instance of class. Attributes should initialize on init") from exception
			Auth.user_keys = keys
		else:
			raise TypeError("User origin is not set. Set it before setting user keys with Auth.set_user_origin")

	@staticmethod
	def set_role_attribute(attribute_name: str) -> None:
		if Auth.class_name is not None:
			aux = Auth.class_name()
			try:
				aux.__getattribute__(attribute_name)
			except AttributeError as exception:
				raise Exception(
					"Attribute is not in instance of class. Attributes should initialize on init") from exception
			Auth.role_attribute = attribute_name
		else:
			raise TypeError("User origin is not set. Set it before setting role attribute with Auth.set_user_origin")

	@staticmethod
	def requires_stateless_token(operation):
		def verify_auth(*args, **kwargs):
			token = request.headers.get("token")
			saved_token = None
			try:
				saved_token = session["token"]
				response = Response(status=UNAUTHORIZED)
				if token is not None and saved_token is not None and token == saved_token:
					session.modified = True
					response = operation(*args, **kwargs)
			except KeyError:
				response = Response(status=UNAUTHORIZED)
				if token is not None and saved_token is None:
					response = Response(status=SESSION_EXPIRED)
			return response

		return update_wrapper(verify_auth, operation)

	@staticmethod
	def requires_role(role: str):
		def decorator(operation):
			def verify_role(*args, **kwargs):
				token = request.headers.get("token")
				response = Response(status=FORBIDDEN)
				if token is not None:
					values = Auth.decode_token(token)
					response = Response(status=FORBIDDEN)
					if str(values["is_owner"]) == str(role):
						response = operation(*args, **kwargs)
				return response

			return update_wrapper(verify_role, operation)

		return decorator

	@staticmethod
	def requires_payload(required_fields: set):
		def decorator(operation):
			def verify_payload(*args, **kwargs):
				if not included(required_fields, request.json):
					response = Response(status=NOT_ACCEPTABLE)
				else:
					response = operation(*args, **kwargs)
				return response

			return update_wrapper(verify_payload, operation)

		return decorator

	@staticmethod
	def generate_token(user) -> str or None:
		response: str or None
		if Auth.class_name is not None:
			if isinstance(user, Auth.class_name):
				if Auth.secret_password is None:
					Auth.set_password()
				timestamp = datetime.now().strftime("%H:%M:%S")

				value: str = ""
				for key in Auth.user_keys:
					value += user.__getattribute__(key) + "/"

				if Auth.role_attribute is not None:
					current_role = user.__getattribute__(Auth.role_attribute)
					if current_role is not None:
						value += current_role + "/"
					else:
						value += "NONE/"

				value += timestamp
				response = encode(value, Auth.secret_password)
			else:
				raise TypeError("Provided user is not instance of User origin")
		else:
			raise TypeError("User origin is not set. Set it before setting role attribute with Auth.set_user_origin")
		return response

	@staticmethod
	def decode_token(token: str) -> dict:
		if Auth.secret_password is not None:
			decoded_token = decode(token, Auth.secret_password)
			decoded_token = decoded_token.split("/")
			aux_dict: dict = {}

			for key, value in zip(Auth.user_keys, decoded_token):
				aux_dict[key] = value

			if Auth.role_attribute is not None:
				aux_dict[Auth.role_attribute] = decoded_token[-2]
		else:
			raise TypeError("No token has been created. Cannot decode token")
		return aux_dict

	@staticmethod
	def crypt(string: str) -> str:
		return generate_password_hash(string)

	@staticmethod
	def check_crypted(crypted: str, clean: str) -> str:
		return check_password_hash(crypted, clean)
