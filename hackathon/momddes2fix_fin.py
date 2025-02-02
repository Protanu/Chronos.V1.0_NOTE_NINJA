import sys
import speech_recognition as sr
import os
import datetime
import pyaudio
import wave
import google.generativeai as genai
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QFileDialog, QTextEdit, QMessageBox, QHBoxLayout
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon


genai.configure(api_key="AIzaSyDkXR3W6SobrZd5rdT2ZwEFBT5hjmo8RYE")

def apply_lavender_theme(self):
    self.setStyleSheet("""
        QWidget {
            background-color: #E6E6FA;
            color: black;
        }
        QTextEdit {
            background: #F8F8FF;
            color: black;
            border-radius: 10px;
            padding: 8px;
        }
        QPushButton {
            background-color: #D8BFD8;
            border-radius: 15px;
            color: black;
            padding: 10px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #DDA0DD;
        }
        QLabel {
            color: #4B0082;
            font-size: 14px;
        }
    """)




def apply_gemini_ai_theme(widget):
    widget.setStyleSheet("""
        QWidget {
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #5E81F4, stop:1 #8E54E9);
            color: white;
        }
        QTextEdit {
            background: #ffffff;
            color: black;
            border: 1px solid #ccc;
            border-radius: 10px;
            padding: 8px;
        }
        QPushButton {
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #5E81F4, stop:1 #8E54E9);
            border: none;
            border-radius: 15px;
            color: white;
            font-size: 14px;
            font-weight: bold;
            padding: 10px;
        }
        QPushButton:hover {
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #7A97F5, stop:1 #A078EF);
        }
        QPushButton:pressed {
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #4A6FE5, stop:1 #7744E1);
        }
        QLabel {
            color: white;
            font-size: 16px;
        }
    """)


def apply_gemini_ai_button_style(button):
    button.setStyleSheet("""
        QPushButton {
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #5E81F4, stop:1 #8E54E9);
            border: none;
            border-radius: 20px;
            padding: 10px;
            color: white;
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #7A97F5, stop:1 #A078EF);
        }
        QPushButton:pressed {
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #4A6FE5, stop:1 #7744E1);
        }
    """)


class AudioRecorder(QThread):
    recording_complete = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.timestamp = datetime.datetime.now()
        self.output_file = f"recorded_audio_{self.timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.wav"
        self.chunk = 1024
        self.sample_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.frames = []

    def run(self):
        p = pyaudio.PyAudio()
        self.stream = p.open(format=self.sample_format, channels=self.channels, rate=self.rate, input=True, frames_per_buffer=self.chunk)
        self.is_recording = True

        while self.is_recording:
            data = self.stream.read(self.chunk)
            self.frames.append(data)

        self.stream.stop_stream()
        self.stream.close()
        p.terminate()

        wf = wave.open(self.output_file, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(p.get_sample_size(self.sample_format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(self.frames))
        wf.close()

        self.recording_complete.emit(self.output_file)

    def stop(self):
        self.is_recording = False

class AudioTranscriber(QWidget):
    def save_transcript(self):
        transcript = self.text_area.toPlainText()
        if not transcript.strip():
            QMessageBox.warning(self, "Save Error", "There is no transcript to save.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Transcript", "", "Text Files (*.txt)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(transcript)
            QMessageBox.information(self, "Success", "Transcript saved successfully!")

    def __init__(self):
        super().__init__()
        self.initUI()
        self.recognizer = sr.Recognizer()
        self.audio_file_path = ""
        self.timestamp = None
        self.recorder = AudioRecorder()
        self.recorder.recording_complete.connect(self.handle_recording_complete)
        


    def initUI(self):
        self.setWindowTitle("Note Ninja")
        self.setWindowIcon(QIcon("icon.png"))
        self.setGeometry(100, 100, 800, 600)
        apply_lavender_theme(self)
        

        self.layout = QVBoxLayout()

        self.label = QLabel("Select or Record an Audio File to Transcribe")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)

        self.record_btn = QPushButton("Start Recording")
        self.record_btn.clicked.connect(self.start_recording)
        self.layout.addWidget(self.record_btn)
        apply_gemini_ai_button_style(self.record_btn)

        self.stop_record_btn = QPushButton("Stop Recording")
        self.stop_record_btn.setEnabled(False)
        self.stop_record_btn.clicked.connect(self.stop_recording)
        self.layout.addWidget(self.stop_record_btn)
        apply_gemini_ai_button_style(self.stop_record_btn)


        self.transcribe_btn = QPushButton("Select Audio File")
        self.transcribe_btn.clicked.connect(self.load_audio)
        self.layout.addWidget(self.transcribe_btn)
        apply_gemini_ai_button_style(self.transcribe_btn)


        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.layout.addWidget(self.text_area)

        button_layout = QHBoxLayout()

        self.summarize_btn = QPushButton("Generate Meeting Minutes")
        self.summarize_btn.clicked.connect(self.summarize_text)
        button_layout.addWidget(self.summarize_btn)
        apply_gemini_ai_button_style(self.summarize_btn)
        


        self.brief_summarize_btn = QPushButton("Summarize Paragraph")
        self.brief_summarize_btn.clicked.connect(self.summarize_paragraph)
        button_layout.addWidget(self.brief_summarize_btn)
        apply_gemini_ai_button_style(self.brief_summarize_btn)
        

        self.layout.addLayout(button_layout)

        self.save_btn = QPushButton("Save Transcript")
        self.save_btn.clicked.connect(self.save_transcript)
        self.layout.addWidget(self.save_btn)
        apply_gemini_ai_button_style(self.save_btn)


        self.setLayout(self.layout)

    def start_recording(self):
        self.record_btn.setEnabled(False)
        self.stop_record_btn.setEnabled(True)
        self.recorder.start()

    def stop_recording(self):
        self.recorder.stop()
        self.stop_record_btn.setEnabled(False)
        self.record_btn.setEnabled(True)

    def handle_recording_complete(self, file_path):
        self.audio_file_path = file_path
        self.transcribe_audio()

    def load_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Audio File", "", "Audio Files (*.wav *.mp3)")
        if file_path:
            self.audio_file_path = file_path
            self.transcribe_audio()

    def transcribe_audio(self):
        if not self.audio_file_path:
            return
        with sr.AudioFile(self.audio_file_path) as source:
            audio = self.recognizer.record(source)
        try:
            transcript = self.recognizer.recognize_google(audio)
            self.text_area.setText(transcript)
        except sr.UnknownValueError:
            self.text_area.setText("Could not understand the audio.")
        except sr.RequestError:
            self.text_area.setText("Could not request results, check your internet connection.")

    def summarize_text(self):
        transcript = self.text_area.toPlainText()
        if not transcript:
            return
        try:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(f"Generate meeting minutes from this transcript:\n{transcript}")
            self.text_area.setText(f"Meeting Minutes:\n{response.text}\n\nFull Transcript:\n{transcript}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def summarize_paragraph(self):
        paragraph = self.text_area.toPlainText()
        if not paragraph:
            return
        try:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(f"Summarize this paragraph briefly:\n{paragraph}")
            self.text_area.setText(f"Brief Summary:\n{response.text}\n\nOriginal Text:\n{paragraph}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AudioTranscriber()
    window.show()
    sys.exit(app.exec())
