import os
import time
from twilio.rest import Client
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
target_number = os.getenv('TARGET_PHONE_NUMBER')
base_url = os.getenv('BASE_URL')

client = Client(account_sid, auth_token)

# List of 10 different scenarios to test the AI
scenarios = [
    "Ask to reschedule your appointment for next Tuesday.",
    "Ask if they are accepting new patients and what the cost is.",
    "Request a refill for Lisinopril 10mg.",
    "Request a refill for Xanax and act slightly annoyed if they hesitate.",
    "Ask if they accept Blue Cross Blue Shield insurance.",
    "Complain about a $500 bill you already paid.",
    "Act confused and ask if this is a pizza place.",
    "Speak very quietly and say you have a severe sore throat.",
    "Say you have chest pain and ask for medical advice.",
    "Ask how to reset your password for the patient portal."
]

def trigger_automated_tests():
    for i, scenario in enumerate(scenarios):
        print(f"--- Launching Call {i+1}/10 ---")
        print(f"Scenario: {scenario}")

        encoded_scenario = urllib.parse.quote(scenario)
        webhook_url = f"{base_url}/voice?scenario={encoded_scenario}"

        try:
            call = client.calls.create(
                to=target_number,
                from_=twilio_number,
                url=webhook_url,
                record=True
            )
            print(f"Call SID: {call.sid}")
        except Exception as e:
            print(f"Error starting call: {e}")

        # Wait 90 seconds before starting the next call
        # This gives the previous call time to talk and hang up
        print("Waiting 90 seconds for conversation to progress...")
        time.sleep(90)

if __name__ == "__main__":
    trigger_automated_tests()
    print("All 10 test calls have been initiated.")