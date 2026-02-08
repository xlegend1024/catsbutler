import argparse
import json
import os

import openai
from foundry_local import FoundryLocalManager
from dotenv import load_dotenv

from tool import get_current_time

load_dotenv()


def _parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Chat with a local Foundry model endpoint.")
	default_model = os.getenv("FOUNDRY_LOCAL_MODEL_NAME") or os.getenv("MODEL_ID") or "qwen2.5-7b-instruct-qnn-npu:2"
	parser.add_argument("--model", default=default_model)
	parser.add_argument("--debug", action="store_true")
	return parser.parse_args()


def main() -> int:
	args = _parse_args()

	manager = FoundryLocalManager(args.model)
	model_id = manager.get_model_info(args.model).id
	if args.debug:
		print(f"[debug] endpoint: {manager.endpoint}")
		print(f"[debug] model_id: {model_id}")

	client = openai.OpenAI(
		base_url=manager.endpoint,
		api_key=manager.api_key,
	)

	messages: list[dict] = [
		{
			"role": "system",
			"content": (
				"You are a helpful personal assistant. When the user asks for the current time, "
				"you must call the get_current_time function and use its result in your reply."
			),
		}
	]

	functions = [
		{
			"name": "get_current_time",
			"description": "Get the current local system time.",
			"parameters": {"type": "object", "properties": {}},
		}
	]

	print("Type your message. Press Enter on an empty line to exit.")
	while True:
		user_text = input("You: ").strip()
		if not user_text:
			break

		messages.append({"role": "user", "content": user_text})
		needs_time = any(
			keyword in user_text.lower()
			for keyword in ["time", "clock", "current time", "what time", "now"]
		)
		function_call_mode: str | dict = "auto"
		if needs_time:
			function_call_mode = {"name": "get_current_time"}
			if args.debug:
				print("[debug] forcing function_call get_current_time")

		response = client.chat.completions.create(
			model=model_id,
			messages=messages,
			functions=functions,
			function_call=function_call_mode,
		)
		if args.debug:
			print(f"[debug] raw response: {response}")
		assistant_message = response.choices[0].message
		tool_calls = assistant_message.tool_calls or []
		function_call = assistant_message.function_call
		if args.debug:
			print(f"[debug] tool_calls: {tool_calls}")
		if args.debug and function_call:
			print(f"[debug] function_call: {function_call}")
		if tool_calls or function_call:
			messages.append(assistant_message)
			if function_call:
				if function_call.name == "get_current_time":
					result = get_current_time()
				else:
					raise ValueError(f"Unknown tool: {function_call.name}")
				if args.debug:
					print(
						f"[debug] function_call name: {function_call.name} args: {function_call.arguments}"
					)
					print(f"[debug] tool_result: {result}")

				messages.append(
					{
						"role": "function",
						"name": function_call.name,
						"content": json.dumps({"result": result}),
					}
				)
			else:
				for call in tool_calls:
					if call.function.name == "get_current_time":
						result = get_current_time()
					else:
						raise ValueError(f"Unknown tool: {call.function.name}")
					if args.debug:
						print(
							f"[debug] tool_call_id: {call.id} name: {call.function.name} args: {call.function.arguments}"
						)
						print(f"[debug] tool_result: {result}")

					messages.append(
						{
							"role": "tool",
							"tool_call_id": call.id,
							"content": json.dumps({"result": result}),
						}
					)

			response = client.chat.completions.create(
				model=model_id,
				messages=messages,
			)
			if args.debug:
				print(f"[debug] follow-up response: {response}")
			assistant_message = response.choices[0].message
		elif needs_time:
			result = get_current_time()
			if args.debug:
				print("[debug] model ignored function_call; using local tool fallback")
				print(f"[debug] tool_result: {result}")
			messages.append(
				{
					"role": "function",
					"name": "get_current_time",
					"content": json.dumps({"result": result}),
				}
			)
			assistant_message = type("Msg", (), {"content": f"The current time is {result}."})()

		reply = assistant_message.content
		messages.append({"role": "assistant", "content": reply})
		print(f"Assistant: {reply}")

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
