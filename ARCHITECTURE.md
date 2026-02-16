# Architecture & Design Decisions

## System Overview
The system is built on a **synchronous webhook architecture** using Python (Flask), Twilio Programmable Voice, and OpenAI's GPT-4o.

### Data Flow
1.  **Initiation:** `caller.py` triggers an outbound call via the Twilio REST API. Crucially, it embeds a specific "scenario" (e.g., "Refill Lisinopril") as a query parameter in the webhook URL. This ensures the bot knows *who* it is supposed to be for that specific call.
2.  **Connection:** When the call connects, Twilio requests TwiML instructions from `app.py`.
3.  **Conversation Loop:**
    * **Input:** Twilio's `<Gather>` verb captures the target AI's speech and converts it to text (STT).
    * **Processing:** `app.py` receives the text, appends it to the in-memory conversation history, and sends the full context to OpenAI.
    * **Output:** OpenAI generates a persona-based response. `app.py` returns TwiML with `<Say>` to speak the response back to the target using a neural TTS voice.
4.  **Analysis:** Upon hang-up (triggered by the bot saying "Goodbye"), the full conversation log is serialized to a JSON file. `analyzer.py` then uses a separate LLM pass to review these logs specifically for hallucinations, latency, or logic errors.

## Key Design Choices

### 1. Twilio `<Gather>` vs. Media Streams (WebSockets)
I chose **Twilio `<Gather>`** (synchronous HTTP) over Media Streams (asynchronous WebSockets) for this implementation.
* **Reasoning:** While WebSockets offer lower latency (real-time interruption capabilities), the challenge emphasized "shipping working code" and "reasoning through ambiguous problems." The turn-based nature of a medical intake call fits the Request/Response model perfectly. `<Gather>` is statistically more robust for a rapid prototype, avoiding the complexity of handling raw audio buffers, silence detection, and thread management, which introduces significant stability risks in a short timeframe.

### 2. Scenario Injection via URL Parameters
Instead of a generic bot, the system injects specific user personas via URL parameters at the moment of call initiation.
* **Reasoning:** This allows for deterministic testing. We can programmatically iterate through edge cases (e.g., insurance questions, angry patients, quiet talkers) without changing the core server code or restarting the application.

### 3. Automated QA Pipeline (`analyzer.py`)
Rather than manually listening to 10 calls, I built a secondary pipeline to analyze the transcripts.
* **Reasoning:** Scalability. In a real-world engineering scenario, we would want to run hundreds of regression tests. An automated "Judge" model that reads transcripts and flags anomalies is the only scalable way to monitor quality over time.