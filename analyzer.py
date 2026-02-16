import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

def analyze_transcript(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    history = data['history']
    # Convert history to a readable string
    transcript_text = ""
    for entry in history:
        if entry['role'] == 'user':
            transcript_text += f"Target AI: {entry['content']}\n"
        elif entry['role'] == 'assistant':
            transcript_text += f"Our Bot: {entry['content']}\n"

    prompt = f"""
    Here is a transcript of a call between a patient bot and a medical receptionist AI.
    Please analyze the 'Target AI' responses for bugs.
    Look for:
    1. Hallucinations (making up info).
    2. Repetitiveness.
    3. Failure to understand user intent.
    4. Awkward phrasing or latency issues implied by context.

    Transcript:
    {transcript_text}

    Return a short bulleted list of issues found. If none, say "Pass".
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

def main():
    transcript_dir = "transcripts"
    if not os.path.exists(transcript_dir):
        print("No transcripts found.")
        return

    files = [f for f in os.listdir(transcript_dir) if f.endswith('.json')]

    print(f"Analyzing {len(files)} calls...\n")

    with open("BUG_REPORT.md", "w") as report:
        report.write("# Automated Quality Assurance Report\n\n")

        for file in files:
            path = os.path.join(transcript_dir, file)
            print(f"Processing {file}...")
            analysis = analyze_transcript(path)

            report.write(f"## Call: {file}\n")
            report.write(analysis + "\n\n")
            report.write("---\n")

    print("Done! Check BUG_REPORT.md")

if __name__ == "__main__":
    main()