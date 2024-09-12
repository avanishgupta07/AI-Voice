import os
import requests
import json
import wave
from pydub import AudioSegment
from pydub.playback import play
import sounddevice as sd
import time

DEEPGRAM_API_KEY = 'Key'    #Enter your Key
DEEPGRAM_API_URL = 'https://api.deepgram.com/v1/listen'

# OpenAI credentials
OPENAI_API_KEY = 'Key'     #Enter your Key
OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions'

# Neets.ai credentials
NEETS_API_KEY = 'Key'      #Enter your Key
NEETS_API_URL = 'https://api.neets.ai/v1/text-to-speech'

class VoiceChat:
    def __init__(self):
        self.deepgram_headers = {
            'Authorization': f'Token {DEEPGRAM_API_KEY}',
            'Content-Type': 'audio/wav',
        }
        self.openai_headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json',
        }
        self.neets_headers = {
            'Authorization': f'Bearer {NEETS_API_KEY}',
            'Content-Type': 'application/json',
        }
    
    def record_audio(self, duration, filename):
        fs = 44100  # Sample rate
        print("Recording...")
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=2, dtype='int16')
        sd.wait()  # Wait until recording is finished
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(fs)
            wf.writeframes(recording.tobytes())
        print("Recording saved as", filename)

    def transcribe_audio(self, filename):
        try:
            with open(filename, 'rb') as audio_file:
                response = requests.post(DEEPGRAM_API_URL, headers=self.deepgram_headers, data=audio_file)
            print("Deepgram Response Status Code:", response.status_code)
            print("Deepgram Response Text:", response.text)  
            if response.status_code == 200:
                response_data = response.json()
                transcript = response_data.get('results', {}).get('channels', [{}])[0].get('alternatives', [{}])[0].get('transcript', '')
                if not transcript:
                    print("No transcript found in the response.")
                return transcript
            else:
                print("Error in transcription:", response.text)
                return ""
        except Exception as e:
            print(f"Exception occurred during transcription: {e}")
            return ""

    def generate_response(self, text):
        data = {
            'model': 'gpt-3.5-turbo-0125',
            'messages': [{'role': 'user', 'content': text}],
            'max_tokens': 150,
        }
        retry_attempts = 3
        for attempt in range(retry_attempts):
            try:
                response = requests.post(OPENAI_API_URL, headers=self.openai_headers, data=json.dumps(data))
                if response.status_code == 200:
                    response_data = response.json()
                    response_text = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    if not response_text:
                        print("No response text found in the response.")
                    return response_text
                else:
                    error_message = response.json().get('error', {}).get('message', 'Unknown error')
                    if 'quota' in error_message.lower():
                        print("Quota exceeded. Please check your OpenAI usage.")
                        break  # Exit the loop if quota is exceeded
                    else:
                        print("Error in generating response:", error_message)
                    time.sleep(5)  
            except Exception as e:
                print(f"Exception occurred during response generation: {e}")
                time.sleep(5) 
        return ""

    def synthesize_speech(self, text, filename):
        data = {
            'text': text,
            'voice': 'en_us_male',
        }
        response = requests.post(NEETS_API_URL, headers=self.neets_headers, data=json.dumps(data))
        if response.status_code == 200:
            with open(filename, 'wb') as audio_file:
                audio_file.write(response.content)
            print("Speech synthesized and saved as", filename)
        else:
            print("Error in synthesizing speech:", response.text)
         
            with open(filename, 'wb') as audio_file:
                audio_file.write(b'')
            print("Empty file created due to synthesis error.")

    def _playback(self, file):
        try:
            audio = AudioSegment.from_file(file)
            play(audio)
        except Exception as e:
            print(f"Error playing back audio file {file}: {e}")

    def chat(self):
        self.record_audio(duration=5, filename='input.wav')
        transcript = self.transcribe_audio('input.wav')
        print(f"Transcript: {transcript}")

        if transcript.strip():  
            response_text = self.generate_response(transcript)
            print(f"Response: {response_text}")

            if response_text.strip():  
                self.synthesize_speech(response_text, 'response.wav')
                self._playback('response.wav')
            else:
                print("No valid response text generated.")
        else:
            print("No valid transcript obtained.")

if __name__ == "__main__":
    vc = VoiceChat()
    vc.chat()
