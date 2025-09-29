from customtkinter import *
from tkinter import filedialog
import pygame
import os
import pyaudio
import wave
import time
import threading

# --- Ініціалізація та 
pygame.mixer.init()
audio = pyaudio.PyAudio()

# Задаємо основні конфігурації для зручності
BG_COLOR = "#212121"
CHAT_BG_COLOR = "#2c2c2c"
WIDGET_COLOR = "#3c3c3c"
HOVER_COLOR = "#4a4a4a"
TEXT_COLOR = "#ffffff"
CYAN_COLOR = "#00bcd4"  # для голосових повідомлень
ENTRY_COLOR = "#424242"

# --- Глобальні змінні ---
current_file = None
is_playing_music = False
is_recording = False
frames = []
stream = None
start_time = None
record_count = 0


# --- Допоміжна функція ---
def add_message_to_chat(text, color=TEXT_COLOR):
    """Додає текст у chatbox як повідомлення"""
    label = CTkLabel(chatbox, text=text, text_color=color, anchor="w", justify="left")
    label.pack(anchor="w", pady=2, padx=5)
    chatbox._parent_canvas.yview_moveto(1)  # прокрутка вниз


# --- Функції для музики ---
def add_music_file():
    global current_file
    file_path = filedialog.askopenfilename(
        title="Виберіть музичний файл",
        filetypes=[("Музичні файли", "*.mp3 *.wav *.ogg"), ("Усі файли", "*.*")]
    )
    if file_path:
        current_file = file_path
        filename = os.path.basename(file_path)
        add_message_to_chat(f"🎵 Додано файл: {filename}")


def play_music():
    global is_playing_music, current_file
    if current_file:
        if not is_playing_music:
            try:
                pygame.mixer.music.load(current_file)
                pygame.mixer.music.play()
                add_message_to_chat(f"▶️ Відтворення: {os.path.basename(current_file)}")
                is_playing_music = True
            except pygame.error as e:
                add_message_to_chat(f"Помилка відтворення: {e}")
        else:
            pygame.mixer.music.stop()
            add_message_to_chat("⏹️ Музику зупинено")
            is_playing_music = False


# --- Функції для голосових ---
def start_recording():
    global is_recording, frames, stream, start_time
    if not is_recording:
        is_recording = True
        frames = []
        start_time = time.time()

        # Параметри для запису з мікрофона
        stream = audio.open(format=pyaudio.paInt16, channels=1,
                            rate=44100, input=True, frames_per_buffer=1024)

        threading.Thread(target=record_audio, daemon=True).start()
        add_message_to_chat("🎤 Запис почався...")


def record_audio():
    global frames, is_recording
    while is_recording:
        try:
            data = stream.read(1024, exception_on_overflow=False)
            frames.append(data)
        except IOError as e:
            print(f"Помилка запису: {e}")
            is_recording = False


def stop_recording():
    global is_recording, stream, record_count, start_time
    if is_recording:
        is_recording = False
        stream.stop_stream()
        stream.close()

        record_count += 1
        filename = f"voice_{record_count}.wav"

        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(frames))
        wf.close()

        duration = int(time.time() - start_time)
        if duration < 60:
            duration_text = f"{duration} c"
        else:
            minutes = duration // 60
            seconds = duration % 60
            duration_text = f"{minutes} хв {seconds:02d} c"

        # Додаємо голосове повідомлення як фрейм у чат
        message_frame = CTkFrame(chatbox, fg_color="transparent")
        message_frame.pack(anchor="w", pady=2, padx=5)

        label = CTkLabel(message_frame, text=f"👤 Ви: ", text_color=TEXT_COLOR)
        label.pack(side="left")

        voice_button_in_chat = CTkButton(
            message_frame, text=f"🎤 Голосове ({duration_text})",
            fg_color=CYAN_COLOR, hover_color=HOVER_COLOR,
            command=lambda file=filename: threading.Thread(
                target=play_voice, args=(file,), daemon=True).start()
        )
        voice_button_in_chat.pack(side="left")

        chatbox._parent_canvas.yview_moveto(1)  # прокрутка вниз


def toggle_recording():
    if not is_recording:
        voice_button.configure(fg_color="red")
        start_recording()
    else:
        voice_button.configure(fg_color="green")
        stop_recording()


def play_voice(filename):
    try:
        wf = wave.open(filename, 'rb')
        play_stream = audio.open(format=audio.get_format_from_width(wf.getsampwidth()),
                                 channels=wf.getnchannels(),
                                 rate=wf.getframerate(),
                                 output=True)
        data = wf.readframes(1024)
        while data:
            play_stream.write(data)
            data = wf.readframes(1024)

        play_stream.stop_stream()
        play_stream.close()
        wf.close()
    except Exception as e:
        add_message_to_chat(f"Помилка відтворення: {e}")


# --- Чат ---
def send_message():
    message = entry.get()
    if message.strip() != "":
        label = CTkLabel(chatbox, text=f"👤 Ви: {message}", text_color=TEXT_COLOR, anchor="w", justify="left")
        label.pack(anchor="w", pady=2, padx=5)
        entry.delete(0, "end")
        chatbox._parent_canvas.yview_moveto(1)


# --- Інтерфейс ---
set_appearance_mode("dark")
window = CTk()
window.geometry("420x520")
window.title("Mini Telegram з голосовими")
window.configure(fg_color=BG_COLOR)

chat_frame_container = CTkFrame(window, fg_color=CHAT_BG_COLOR, corner_radius=10)
chat_frame_container.pack(fill="both", expand=True, padx=10, pady=(10, 5))

chatbox = CTkScrollableFrame(chat_frame_container, fg_color="transparent")
chatbox.pack(fill="both", expand=True, padx=5, pady=5)

bottom_frame = CTkFrame(window, fg_color=BG_COLOR)
bottom_frame.pack(fill="x", pady=5, padx=10)

entry = CTkEntry(bottom_frame, width=200, placeholder_text="Напишіть повідомлення...",
                 fg_color=ENTRY_COLOR, text_color=TEXT_COLOR, border_width=0, corner_radius=20)
entry.pack(side="left", padx=(5, 0), pady=5, fill="x", expand=True)
entry.bind("<Return>", lambda event: send_message())

send_button = CTkButton(bottom_frame, text="➤", width=40, height=30, command=send_message,
                        fg_color=CYAN_COLOR, hover_color=HOVER_COLOR, corner_radius=20, text_color="white")
send_button.pack(side="left", padx=5)

file_button = CTkButton(bottom_frame, text="📎", width=40, height=30, command=add_music_file,
                        fg_color=WIDGET_COLOR, hover_color=HOVER_COLOR, corner_radius=20)
file_button.pack(side="left", padx=(0, 5))

play_button = CTkButton(bottom_frame, text="🎵", width=40, height=30, command=play_music,
                        fg_color=WIDGET_COLOR, hover_color=HOVER_COLOR, corner_radius=20)
play_button.pack(side="left", padx=(0, 5))

voice_button = CTkButton(bottom_frame, text="🎤", width=40, height=30, fg_color="green",
                         hover_color="red", command=toggle_recording, corner_radius=20)
voice_button.pack(side="left", padx=(0, 5))

window.mainloop()
