import customtkinter as ctk
import whisper
import tempfile
import sounddevice as sd
import soundfile as sf
import numpy as np
import time
import threading
import queue
import os
from contextlib import contextmanager
import pyperclip

# Set appearance mode and default color theme
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

@contextmanager
def timer(description, result_label=None):
    """Context manager to time operations and optionally update a UI label"""
    start = time.time()
    yield
    elapsed = time.time() - start
    message = f"⏲ [{description}] {elapsed:.2f}s"
    print(message)
    if result_label:
        result_label.configure(text=result_label.cget("text") + f"\n{message}")

class WhisperApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Whisper Transcription")
        self.geometry("700x500")
        
        # Recording state variables
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        self.recording_stream = None
        
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header doesn't expand
        self.grid_rowconfigure(1, weight=1)  # Text area expands
        self.grid_rowconfigure(2, weight=0)  # Status doesn't expand
        self.grid_rowconfigure(3, weight=0)  # Button doesn't expand
        
        # Create header
        self.header = ctk.CTkLabel(self, text="Whisper Audio Transcription", font=ctk.CTkFont(size=20, weight="bold"))
        self.header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        # Create text box for transcription results
        self.result_text = ctk.CTkTextbox(self, width=650, height=300, font=ctk.CTkFont(size=14))
        self.result_text.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        # Create status label
        self.status_label = ctk.CTkLabel(self, text="Ready", font=ctk.CTkFont(size=12))
        self.status_label.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        
        # Create button frame
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=3, column=0, padx=20, pady=(5, 20), sticky="ew")
        self.button_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Create record button
        self.record_button = ctk.CTkButton(
            self.button_frame, 
            text="Record", 
            command=self.toggle_recording,
            fg_color="#28a745",  # Green color for record button
            hover_color="#218838"
        )
        self.record_button.grid(row=0, column=0, padx=10, pady=10)
        
        # Create copy button
        self.copy_button = ctk.CTkButton(
            self.button_frame, 
            text="Copy to Clipboard", 
            command=self.copy_to_clipboard,
            fg_color="#007bff",  # Blue color for copy button
            hover_color="#0069d9"
        )
        self.copy_button.grid(row=0, column=1, padx=10, pady=10)
        
        # Initialize whisper model
        self.model = None
        
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        self.is_recording = True
        self.record_button.configure(
            text="Stop Recording", 
            fg_color="#dc3545",  # Red color for stop button
            hover_color="#c82333"
        )
        
        # Clear previous results
        self.result_text.delete("0.0", "end")
        self.update_status("🎤 Recording... (click Stop when finished)")
        
        # Start recording in a separate thread
        self.audio_queue = queue.Queue()
        self.recording_thread = threading.Thread(target=self._record_audio_thread, daemon=True)
        self.recording_thread.start()
    
    def _record_audio_thread(self):
        """Record audio in a separate thread"""
        samplerate = 44100
        channels = 1
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Status: {status}")
            self.audio_queue.put(indata.copy())
        
        with sd.InputStream(samplerate=samplerate, channels=channels, callback=audio_callback):
            while self.is_recording:
                time.sleep(0.1)
    
    def stop_recording(self):
        if not self.is_recording:
            return
            
        self.is_recording = False
        self.record_button.configure(
            text="Record", 
            fg_color="#28a745",  # Green color for record button
            hover_color="#218838"
        )
        
        self.update_status("Processing recording...")
        
        # Wait for recording thread to finish
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=1.0)
            
        # Process the recorded audio
        threading.Thread(target=self._process_recording, daemon=True).start()
    
    def _process_recording(self):
        try:
            # Get all audio data from queue
            audio_data = []
            while not self.audio_queue.empty():
                audio_data.append(self.audio_queue.get())
                
            if not audio_data:
                self.update_status("❌ No audio recorded")
                return
                
            # Concatenate all audio chunks
            audio_array = np.concatenate(audio_data, axis=0)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                temp_filename = temp_wav.name
                
            samplerate = 44100
            sf.write(temp_filename, audio_array, samplerate)
            
            # Transcribe the audio
            self._transcribe_file(temp_filename, is_temp_file=True)
            
        except Exception as e:
            self.update_status(f"❌ Error: {str(e)}")
            self.result_text.insert("0.0", f"Error: {str(e)}")
    
    def update_status(self, text):
        self.status_label.configure(text=text)
        self.update_idletasks()
    
    def _transcribe_file(self, file_path, is_temp_file=False):
        """Transcribe an audio file"""
        # Clear previous result
        self.result_text.delete("0.0", "end")
        
        # Disable button during transcription
        self.record_button.configure(state="disabled")
        
        # Run transcription in a separate thread
        threading.Thread(
            target=self._transcribe_thread, 
            args=(file_path, is_temp_file), 
            daemon=True
        ).start()
    
    def _transcribe_thread(self, file_path, is_temp_file=False):
        try:
            self.update_status("📂 Processing audio file...")
            
            # Load the model if not already loaded
            if self.model is None:
                self.update_status("Loading Whisper model...")
                self.model = whisper.load_model("tiny.en")
            
            # Transcribe
            self.update_status("🔍 Transcribing...")
            result = self.model.transcribe(file_path)
            
            # Display result
            self.result_text.insert("0.0", result["text"])
            
            # Get file duration
            duration = sf.info(file_path).duration
            
            # Update status with complete info
            self.update_status(f"✅ Transcription complete (Audio duration: {duration:.2f}s)")
            
            # Clean up temporary file
            if is_temp_file and os.path.exists(file_path):
                os.unlink(file_path)
                
        except Exception as e:
            self.update_status(f"❌ Error: {str(e)}")
            self.result_text.insert("0.0", f"Error: {str(e)}")
        finally:
            # Re-enable button
            self.record_button.configure(state="normal")
    
    def copy_to_clipboard(self):
        """Copy the transcription text to clipboard"""
        text = self.result_text.get("0.0", "end").strip()
        if text:
            pyperclip.copy(text)
            self.update_status("✅ Text copied to clipboard")
        else:
            self.update_status("❌ No text to copy")

if __name__ == "__main__":
    app = WhisperApp()
    app.mainloop()