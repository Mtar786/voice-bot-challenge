import os
import json
import time
from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = OpenAI()

# In-memory storage for call logs (In production, use a DB)
# Structure: { call_sid: [ {"role": "system", ...}, {"role": "user", ...} ] }
call_histories = {}
call_scenarios = {}

SYSTEM_PROMPT_TEMPLATE = """
You are a patient calling a medical clinic.
Your specific scenario is: {scenario}

- Act natural. Use occasional "ums" or "ahs".
- Keep your responses concise (1-2 sentences).
- Do not announce that you are an AI.
- If the other agent makes a mistake, act confused.
- If the conversation is done, say "Goodbye" to end it.
"""

@app.route("/voice", methods=['POST'])
def voice():
    """Initial webhook called when the call connects."""
    call_sid = request.values.get('CallSid')

    # Check if we have a scenario preset for this call (passed via query param in caller.py)
    # If not, default to a standard refill.
    scenario = request.args.get('scenario', "You need to refill your Lisinopril prescription.")

    # Initialize history
    call_histories[call_sid] = [
        {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE.format(scenario=scenario)}
    ]
    call_scenarios[call_sid] = scenario

    resp = VoiceResponse()
    # Pause briefly to let the line connect fully
    resp.pause(length=1)

    # We wait for the OTHER AI to speak first (usually "Hello, thanks for calling...").
    # gathering input triggers the 'gather' route.
    gather = Gather(input='speech', action='/gather', speechTimeout='auto')
    resp.append(gather)

    # If they don't say anything, redirect back to listen again
    resp.redirect('/voice')

    return str(resp)

@app.route("/gather", methods=['POST'])
def gather():
    """Handles the speech input from the other AI."""
    call_sid = request.values.get('CallSid')
    speech_result = request.values.get('SpeechResult') # This is what the other AI said

    if not speech_result:
        # If we heard nothing, listen again
        resp = VoiceResponse()
        resp.redirect('/voice')
        return str(resp)

    # 1. Record what they said
    history = call_histories.get(call_sid, [])
    history.append({"role": "user", "content": speech_result}) # "User" is the other AI here

    # 2. Generate our response
    completion = client.chat.completions.create(
        model="gpt-4o", # Or gpt-3.5-turbo for speed/cost
        messages=history,
        temperature=0.7,
        max_tokens=150
    )

    bot_reply = completion.choices[0].message.content
    history.append({"role": "assistant", "content": bot_reply})

    # Update global state
    call_histories[call_sid] = history

    # 3. Build TwiML response
    resp = VoiceResponse()

    # Detect if we should hang up
    if "goodbye" in bot_reply.lower() or "bye" in bot_reply.lower():
        resp.say(bot_reply, voice='Polly.Matthew') # Use a realistic voice
        resp.hangup()
        # Trigger save of transcript
        save_transcript(call_sid)
    else:
        resp.say(bot_reply, voice='Polly.Matthew')
        # Listen for their next reply
        gather = Gather(input='speech', action='/gather', speechTimeout='auto')
        resp.append(gather)

    return str(resp)

def save_transcript(call_sid):
    """Saves the conversation to a JSON file."""
    if call_sid in call_histories:
        filename = f"transcripts/call_{call_sid}.json"
        os.makedirs("transcripts", exist_ok=True)
        with open(filename, "w") as f:
            data = {
                "scenario": call_scenarios.get(call_sid),
                "history": call_histories[call_sid],
                "timestamp": time.time()
            }
            json.dump(data, f, indent=2)
        print(f"Transcript saved to {filename}")

if __name__ == "__main__":
    app.run(debug=True, port=5000)