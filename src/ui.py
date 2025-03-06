import customtkinter as ctk
import whisper
import tempfile
import sounddevice as sd
import soundfile as sf
import numpy as np
import time
import threading
import os
from contextlib import contextmanager

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
        
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header doesn't expand
        self.grid_rowconfigure(1, weight=1)  # Text area expands
        self.grid_rowconfigure(2, weight=0)  # Status doesn't expand
        self.grid_rowconfigure(3, weight=0)  # Buttons don't expand
        
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
        self.button_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Create buttons
        self.record_button = ctk.CTkButton(self.button_frame, text="Record (5s)", command=self.record_audio)
        self.record_button.grid(row=0, column=0, padx=10, pady=10)
        
        self.record_custom_button = ctk.CTkButton(self.button_frame, text="Record Custom", command=self.record_custom)
        self.record_custom_button.grid(row=0, column=1, padx=10, pady=10)
        
        self.browse_button = ctk.CTkButton(self.button_frame, text="Open Audio File", command=self.browse_file)
        self.browse_button.grid(row=0, column=2, padx=10, pady=10)
        
        # Duration slider for custom recording
        self.duration_frame = ctk.CTkFrame(self)
        self.duration_frame.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        self.duration_label = ctk.CTkLabel(self.duration_frame, text="Recording Duration (seconds):")
        self.duration_label.pack(side="left", padx=(10, 0))
        
        self.duration_slider = ctk.CTkSlider(self.duration_frame, from_=1, to=60, number_of_steps=59)
        self.duration_slider.pack(side="left", fill="x", expand=True, padx=10)
        self.duration_slider.set(5)
        
        self.duration_value = ctk.CTkLabel(self.duration_frame, text="5")
        self.duration_value.pack(side="left", padx=(0, 10))
        
        # Bind slider to update the value label
        self.duration_slider.configure(command=self.update_duration_value)
        
        # Initialize whisper model
        self.model = None

    def update_duration_value(self, value):
        self.duration_value.configure(text=f"{int(value)}")

    def record_audio(self):
        self.transcribe_audio(record_duration=5)
        
    def record_custom(self):
        duration = int(self.duration_slider.get())
        self.transcribe_audio(record_duration=duration)
        
    def browse_file(self):
        file_path = ctk.filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=(("Audio Files", "*.mp3 *.wav *.m4a *.flac"), ("All Files", "*.*"))
        )
        if file_path:
            self.transcribe_audio(file_path=file_path)

    def update_status(self, text):
        self.status_label.configure(text=text)
        self.update_idletasks()
        
    def transcribe_audio(self, file_path=None, record_duration=None):
        """Transcribe audio either from file or recording"""
        # Clear previous result
        self.result_text.delete("0.0", "end")
        
        # Run transcription in a separate thread to avoid UI freezing
        threading.Thread(target=self._transcribe_thread, args=(file_path, record_duration), daemon=True).start()
    
    def _transcribe_thread(self, file_path=None, record_duration=None):
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                temp_filename = temp_wav.name
                
                input_file = None
                
                if file_path:
                    input_file = file_path
                    self.update_status(f"📂 Using input file: {os.path.basename(file_path)}")
                else:
                    self.update_status(f"🎤 Recording for {record_duration} seconds...")
                    self.record_button.configure(state="disabled")
                    self.record_custom_button.configure(state="disabled")
                    self.browse_button.configure(state="disabled")
                    
                    # Record audio
                    samplerate = 44100
                    recording = sd.rec(
                        int(record_duration * samplerate),
                        samplerate=samplerate,
                        channels=1,
                        dtype=np.float32
                    )
                    sd.wait()
                    sf.write(temp_filename, recording, samplerate)
                    
                    input_file = temp_filename
                    self.update_status("✅ Recording finished")
                
                # Load the model if not already loaded
                if self.model is None:
                    self.update_status("Loading Whisper model...")
                    self.model = whisper.load_model("tiny.en")
                
                # Transcribe
                self.update_status("🔍 Transcribing...")
                result = self.model.transcribe(input_file)
                
                # Display result
                self.result_text.insert("0.0", result["text"])
                
                # Get file duration
                duration = sf.info(input_file).duration
                
                # Update status with complete info
                self.update_status(f"✅ Transcription complete (Audio duration: {duration:.2f}s)")
                
            # Clean up temporary file if we created one
            if file_path is None and os.path.exists(temp_filename):
                os.unlink(temp_filename)
                
        except Exception as e:
            self.update_status(f"❌ Error: {str(e)}")
            self.result_text.insert("0.0", f"Error: {str(e)}")
        finally:
            # Re-enable buttons
            self.record_button.configure(state="normal")
            self.record_custom_button.configure(state="normal")
            self.browse_button.configure(state="normal")

if __name__ == "__main__":
    app = WhisperApp()
    app.mainloop()