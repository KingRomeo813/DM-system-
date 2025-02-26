# import json
# import asyncio
# import base64
# from channels.generic.websocket import AsyncWebsocketConsumer
# from google import genai  # Ensure you have this package installed and configured
# import os

# # Set your API key if not done elsewhere
# os.environ['GOOGLE_API_KEY'] 
# MODEL = "gemini-2.0-flash-exp"  # Replace with your model ID

# client = genai.Client(
#     http_options={'api_version': 'v1alpha'}
# )

# class GeminiConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         await self.accept()
#         self.gemini_session = None
#         print("WebSocket connected.")

#     async def disconnect(self, close_code):
#         if self.gemini_session:
#             # If the session provides a close method, call it here
#             await self.gemini_session.close()
#         print("WebSocket disconnected with code:", close_code)

#     async def receive(self, text_data=None, bytes_data=None):
#         message = text_data or (bytes_data.decode("utf-8") if bytes_data else None)
#         if not message:
#             return

#         data = json.loads(message)
#         # If it's the initial setup message
#         if "setup" in data:
#             config = data.get("setup", {})
#             # Start the Gemini session in a background task
#             asyncio.create_task(self.start_gemini_session(config))
#         elif "realtime_input" in data:
#             if self.gemini_session:
#                 for chunk in data["realtime_input"]["media_chunks"]:
#                     if chunk["mime_type"] == "audio/pcm":
#                         await self.gemini_session.send({
#                             "mime_type": "audio/pcm", 
#                             "data": chunk["data"]
#                         })
#                     elif chunk["mime_type"] == "image/jpeg":
#                         await self.gemini_session.send({
#                             "mime_type": "image/jpeg", 
#                             "data": chunk["data"]
#                         })
#         else:
#             print("Unrecognized message:", data)

#     async def start_gemini_session(self, config):
#         try:
#             async with client.aio.live.connect(model=MODEL, config=config) as session:
#                 self.gemini_session = session
#                 print("Connected to Gemini API")
#                 async for response in session.receive():
#                     if response.server_content is None:
#                         print("Unhandled server message:", response)
#                         continue

#                     model_turn = response.server_content.model_turn
#                     if model_turn:
#                         for part in model_turn.parts:
#                             if hasattr(part, "text") and part.text is not None:
#                                 await self.send(json.dumps({"text": part.text}))
#                             elif hasattr(part, "inline_data") and part.inline_data is not None:
#                                 base64_audio = base64.b64encode(part.inline_data.data).decode("utf-8")
#                                 await self.send(json.dumps({"audio": base64_audio}))
#                     if response.server_content.turn_complete:
#                         print("Turn complete")
#         except Exception as e:
#             print("Error in Gemini session:", e)
#         finally:
#             print("Gemini session closed")

import json
import asyncio
import base64
from channels.generic.websocket import AsyncWebsocketConsumer
from google import genai  # Ensure you have this package installed and configured
import os

# ✅ Load API Key Securely
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("❌ Google API Key not set! Set GOOGLE_API_KEY in environment variables.")

MODEL = "gemini-2.0-flash-exp"

# ✅ Initialize Gemini Client
client = genai.Client(
    http_options={'api_version': 'v1alpha'},
    api_key=GOOGLE_API_KEY
)


class GeminiConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Accept WebSocket Connection and Keep It Alive."""
        await self.accept()
        print("✅ WebSocket connected.")

        self.gemini_session = None
        self.keep_alive = True  # ✅ Keep the session alive

    async def disconnect(self, close_code):
        """Handles WebSocket Disconnection."""
        print(f"🔌 WebSocket disconnected (Code: {close_code})")
        
        self.keep_alive = False  # ✅ Stop receiving from Gemini
        
        if self.gemini_session:
            await self.gemini_session.__aexit__(None, None, None)  # ✅ Properly close Gemini session

    async def receive(self, text_data=None, bytes_data=None):
        """Handles Incoming Messages from WebSocket Client."""
        message = text_data or (bytes_data.decode("utf-8") if bytes_data else None)
        if not message:
            return

        data = json.loads(message)

        if "setup" in data:
            config = data.get("setup", {})
            asyncio.create_task(self.start_gemini_session(config))  # ✅ Start Gemini session in background

        elif "realtime_input" in data:
            if self.gemini_session:
                for chunk in data["realtime_input"]["media_chunks"]:
                    if chunk["mime_type"] in ["audio/pcm", "image/jpeg"]:
                        await self.gemini_session.send({"mime_type": chunk["mime_type"], "data": chunk["data"]})
        
        else:
            print("Unrecognized message:", data)

    async def start_gemini_session(self, config):
        """Maintains Connection with Gemini API Until WebSocket Disconnects."""
        try:
            async with client.aio.live.connect(model=MODEL, config=config) as session:
                self.gemini_session = session
                print("✅ Connected to Gemini API")

                while self.keep_alive:  # ✅ Keep receiving responses
                    async for response in session.receive():
                        if response.server_content is None:
                            print("Unhandled server message:", response)
                            continue

                        model_turn = response.server_content.model_turn
                        if model_turn:
                            for part in model_turn.parts:
                                if hasattr(part, "text") and part.text is not None:
                                    await self.send(json.dumps({"text": part.text}))
                                elif hasattr(part, "inline_data") and part.inline_data is not None:
                                    base64_audio = base64.b64encode(part.inline_data.data).decode("utf-8")
                                    await self.send(json.dumps({"audio": base64_audio}))

                        if response.server_content.turn_complete:
                            print("✅ Turn complete")

        except Exception as e:
            print("❌ Error in Gemini session:", e)
        finally:
            print("🔄 Gemini session closed")
