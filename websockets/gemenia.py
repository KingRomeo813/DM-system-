from channels.generic.websocket import AsyncWebsocketConsumer
import json
import gc
import asyncio
import base64

class GeminiConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print("Gemini WebSocket connected")

    async def disconnect(self, close_code):
        print(f"Gemini WebSocket disconnected with code {close_code}")
        gc.collect()

    async def receive(self, text_data):
        """Receives messages from the WebSocket client and processes Gemini responses."""
        try:
            print("Receiving from Gemini...")

            async for response in session.receive():  # Assuming session is defined
                print(f"Response: {response}")

                if response.server_content is None:
                    continue  # No content to process

                model_turn = response.server_content.model_turn
                if model_turn:
                    for part in model_turn.parts:
                        if hasattr(part, 'text') and part.text:
                            await self.send(json.dumps({"text": part.text}))
                        elif hasattr(part, 'inline_data') and part.inline_data:
                            base64_audio = base64.b64encode(part.inline_data.data).decode('utf-8')
                            await self.send(json.dumps({"audio": base64_audio}))

                if response.server_content.turn_complete:
                    print("\n<Turn complete>")

                gc.collect()

        except Exception as e:
            print(f"Error receiving from Gemini: {e}")

