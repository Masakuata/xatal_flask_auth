from xf_auth.Auth import Auth


class StatefulSession:
	session: list = []

	@staticmethod
	def new_session(data: dict, token: str = None) -> str:
		if token is None:
			token: str = StatefulSession.__new_token(data)
		StatefulSession.session.append({
			"token": token,
			"data": data
		})
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
	def get_data(token: str) -> dict or None:
		data: dict or None = None
		for session in StatefulSession.session:
			if session["token"] == token:
				data = session["data"]
				break
		if data is None:
			data = Auth.decode_token(token)
		return data
