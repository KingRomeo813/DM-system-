import json
import os
from channels.generic.websocket import AsyncWebsocketConsumer
import google.generativeai as genai
import base64
from contextlib import suppress
import logging
import asyncio
# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# Load API key from environment - Should use environment variable or settings
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)
# Supported MIME types and their max sizes
SUPPORTED_MIME_TYPES = {
    "audio/pcm": 10 * 1024 * 1024,  # 10MB max for audio
    "image/jpeg": 5 * 1024 * 1024,   # 5MB max for images
    "image/png": 5 * 1024 * 1024,    # 5MB max for images
    "text/plain": 1024 * 1024        # 1MB max for text
}
class GeminiConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Establish WebSocket connection."""
        await self.accept()
        self.gemini_session = None
        logger.info("WebSocket connected")
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.cleanup_session()
        logger.info(f"WebSocket disconnected with code: {close_code}")
    async def cleanup_session(self):
        """Cleanup active Gemini session."""
        if self.gemini_session:
            with suppress(Exception):
                # No need to call __aenter__ or close() as we're using the new API
                self.gemini_session = None
                logger.info("Gemini session cleaned up")
    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            logger.debug(f"Received data: {data}")
            if self.gemini_session is None and "setup" not in data:
                default_config = {
                    "temperature": 0.7,
                    "candidate_count": 1,
                    "max_output_tokens": 2048,
                }
                await self.handle_setup({"setup": default_config})
            if "setup" in data:
                await self.handle_setup(data)
            elif "realtime_input" in data:
                await self.handle_realtime_input(data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error in receive: {e}", exc_info=True)
            await self.send_error(f"An error occurred: {str(e)}")
    async def handle_setup(self, data):
        """Setup the Gemini session."""
        try:
            await self.cleanup_session()
            config = data.get("setup", {})
            logger.info(f"Setup request received with config: {config}")
            # Initialize Gemini model
            self.gemini_session = genai.GenerativeModel(
                model_name='gemini-pro',
                generation_config=config
            )
            logger.info("Gemini session initialized successfully")
            await self.send(json.dumps({
                "status": "setup_complete",
                "supported_mime_types": list(SUPPORTED_MIME_TYPES.keys())
            }))
        except Exception as e:
            logger.error(f"Error during setup: {e}", exc_info=True)
            await self.send_error(f"Setup failed: {str(e)}")
    async def handle_realtime_input(self, data):
        """Process real-time input from the client."""
        user_id = data.get("user_id", "unknown_user")
        logger.info(f"Processing realtime input for user_id: {user_id}")
        try:
            if not self.gemini_session:
                raise ValueError("No active Gemini session")
            media_chunks = data["realtime_input"].get("media_chunks", [])
            if not media_chunks:
                raise ValueError("No media chunks provided")
            # Process chunks and generate response
            contents = []
            for chunk in media_chunks:
                processed_chunk = await self.process_media_chunk(chunk, user_id)
                if processed_chunk:
                    contents.append(processed_chunk)
            # Generate response using the Gemini model
            response = await asyncio.to_thread(
                self.gemini_session.generate_content,
                contents
            )
            # Send response back to client
            await self.process_model_response(response, user_id)
        except Exception as e:
            logger.error(f"Error in handle_realtime_input: {e}", exc_info=True)
            await self.send_error(f"Processing failed: {str(e)}")
    async def process_media_chunk(self, chunk, user_id):
        """Process each media chunk received."""
        try:
            mime_type = chunk.get("mime_type")
            encoded_data = chunk.get("data")
            if not mime_type or not encoded_data:
                raise ValueError("Missing mime_type or data in chunk")
            if mime_type not in SUPPORTED_MIME_TYPES:
                raise ValueError(f"Unsupported mime_type: {mime_type}")
            # Add padding if necessary
            padding_needed = len(encoded_data) % 4
            if padding_needed:
                encoded_data += '=' * (4 - padding_needed)
            decoded_data = base64.b64decode(encoded_data)
            # Check size limit
            if len(decoded_data) > SUPPORTED_MIME_TYPES[mime_type]:
                raise ValueError(f"File size exceeds limit for {mime_type}")
            await self.send(json.dumps({
                "user_id": user_id,
                "status": "chunk_processed",
                "mime_type": mime_type,
                "size": len(decoded_data)
            }))
            logger.debug(f"Successfully processed chunk: {mime_type}, size: {len(decoded_data)}")
            # Return processed content for Gemini
            if mime_type.startswith('text/'):
                return decoded_data.decode('utf-8')
            else:
                return {
                    "mime_type": mime_type,
                    "data": decoded_data
                }
        except base64.binascii.Error as e:
            logger.error(f"Invalid base64 encoding: {str(e)}")
            raise ValueError(f"Invalid base64 encoding: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to process chunk: {str(e)}", exc_info=True)
            raise
    async def process_model_response(self, response, user_id):
        """Process and send the model's response to the client."""
        try:
            if response and response.text:
                await self.send(json.dumps({
                    "user_id": user_id,
                    "type": "text",
                    "content": response.text
                }))
            await self.send(json.dumps({
                "user_id": user_id,
                "status": "turn_complete"
            }))
        except Exception as e:
            logger.error(f"Error processing model response: {e}", exc_info=True)
            await self.send_error(f"Error processing model response: {str(e)}")
    async def send_error(self, message):
        """Send an error message to the client."""
        error_response = {
            "error": message,
            "status": "error"
        }
        await self.send(json.dumps(error_response))
        logger.error(f"Error sent to client: {message}")