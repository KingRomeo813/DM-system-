import gc
async def receive_from_gemini():
    """Receives responses from the Gemini API and forwards them to the client, looping until turn is complete."""
    try:
        while True:
            try:
                print("receiving from gemini")
                import time
                start_time = time.time() 
                async for response in session.receive():
                    end_time = time.time()
                    print(f"Time to receive response: {end_time - start_time} seconds")
                    print(":::::::::::::::::::::::::::::::::0000000000000")
                    print(">>>>>>>>>>>>>>>>>>>>>",response.server_content)
                    print(f"response: {response}")
                    if response.server_content is None:
                        # if response.tool_call is not None:
                        #       #handle the tool call
                        #        print(f"Tool call received: {response.tool_call}")

                        #        function_calls = response.tool_call.function_calls
                        #        function_responses = []

                        #        for function_call in function_calls:
                        #              name = function_call.name
                        #              args = function_call.args
                        #              # Extract the numeric part from Gemini's function call ID
                        #              call_id = function_call.id

                        #              # Validate function name
                        #              if name == "set_light_values":
                        #                   try:
                        #                       result = set_light_values(int(args["brightness"]), args["color_temp"])
                        #                       function_responses.append(
                        #                          {
                        #                              "name": name,
                        #                              #"response": {"result": "The light is broken."},
                        #                              "response": {"result": result},
                        #                              "id": call_id  
                        #                          }
                        #                       ) 
                        #                       await client_websocket.send(json.dumps({"text": json.dumps(function_responses)}))
                        #                       print("Function executed")
                        #                   except Exception as e:
                        #                       print(f"Error executing function: {e}")
                        #                       continue


                        #        # Send function response back to Gemini
                        #        print(f"function_responses: {function_responses}")
                        #        await session.send(function_responses)
                        #        continue

                        #print(f'Unhandled server message! - {response}')
                        continue

                    model_turn = response.server_content.model_turn
                    if model_turn:
                        for part in model_turn.parts:
                            #print(f"part: {part}")
                            if hasattr(part, 'text') and part.text is not None:
                                #print(f"text: {part.text}")
                                await client_websocket.send(json.dumps({"text": part.text}))
                            elif hasattr(part, 'inline_data') and part.inline_data is not None:
                                # if first_response:
                                #print("audio mime_type:", part.inline_data.mime_type)
                                    #first_response = False
                                base64_audio = base64.b64encode(part.inline_data.data).decode('utf-8')
                                await client_websocket.send(json.dumps({
                                    "audio": base64_audio,
                                }))
                                print("audio received")
                                del base64_audio
                            del part
                    if response.server_content.turn_complete:
                        print('\n<Turn complete>')
                    gc.collect()
            except websockets.exceptions.ConnectionClosedOK:
                print("Client connection closed normally (receive)")
                break  # Exit the loop if the connection is closed
            except Exception as e:
                print(f"Error receiving from Gemini: {e}")
                break # exit the lo

    except Exception as e:
            print(f"Error receiving from Gemini: {e}")
    finally:
            await client_websocket.close() 
            gc.collect()
            print("Gemini connection closed (receive)")
