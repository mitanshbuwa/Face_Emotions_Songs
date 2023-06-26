import cv2
from matplotlib import image
import numpy as np
import mediapipe as mp
from keras.models import load_model
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from tkinter import Tk, Label, Frame, Text, Button
from PIL import Image, ImageTk
import time
import sys
import os
import webbrowser


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS2
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# Spotify credentials
client_id = '8b36e483f7b04c2db9dcd682781f73c4'
client_secret = 'dbffccd760d9456db847c65860b03bc9'
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# Load emotion recognition model and labels
model = load_model(resource_path("model.h5"))
label = np.load(resource_path("labels.npy"))

# MediaPipe and OpenCV initialization
holistic = mp.solutions.holistic
hands = mp.solutions.hands
holis = holistic.Holistic()
drawing = mp.solutions.drawing_utils

# Tkinter window initialization
window = Tk()
window.title("Emotion-based Music Player")
#window.geometry('1000x800')
window.configure(bg="#69C9D0")

# Frames per second (FPS) value
fps = 30

# Create a label to display the detected emotion
emotion_label = Label(window, text="", font=("Arial", 20))

# Create a video frame to display the webcam feed
video_frame = Frame(window, width=640, height=480)

# Create a label within the video frame to display the image
video_label = Label(video_frame)

# Create a text box to display the suggested songs
song_text_box = Text(window, font=("Arial", 12), bg="black", fg="green")
song_text_box.tag_configure("bold", font=("Arial", 12, "bold"))  # Configure the "bold" tag with a bold font
song_text_box.insert("end", "Disclaimer\n\n"
                              "The software created by EEAI follows the law of privacy under ACT 1988."
                              "Any individual to source any code of the created software will be held guilty under privacy act.\n"
                              "Further any client to share the software code without legal consent of 'Mitansh Buwa' will be held guilty under information sharing and privacy act 1988.\n"
                              "It is a request for clients and users to not use software code or share software code without consent of Mitansh Buwa, otherwise consequence of law will take place.", "bold")  # Insert the text "Bold Text" with the "bold" tag

# Create a start button
start_button = Button(window, text="Start", font=("Arial", 16), bg="black", fg="green", command=lambda: start_program())

# Create a restart button
restart_button = Button(window, text="Restart", font=("Arial", 16), bg="black", fg="green", command=lambda: restart_program())

# Configure the grid layout
# Configure the grid layout
window.grid_columnconfigure(0, weight=1)
window.grid_columnconfigure(1, weight=1)
window.grid_rowconfigure(0, weight=1) #This third grid is added to centre the buttons of start and restart
video_frame.grid(row=0, column=0, columnspan=2)
emotion_label.grid(row=1, column=0, pady=10, columnspan=2)
song_text_box.grid(row=0, column=2, rowspan=2, padx=10, pady=10, sticky="nsew")
start_button.grid(row=2, column=0, pady=10, padx=10, sticky="we", columnspan=2)
restart_button.grid(row=3, column=0, pady=10, padx=10, sticky="we", columnspan=2)

# Initialize the video capture
cap = cv2.VideoCapture(0)

# Global variable for start time
start_time = 0

# Function to start the program
def start_program():
    global start_time  # Declare start_time as a global variable
    # Update the start time
    start_time = time.time()
    # Enable the song_text_box
    song_text_box.config(state="normal")
    # Start processing the frames
    process_frame()

# Function to restart the program
def restart_program():
    global start_time  # Declare start_time as a global variable
    # Reset the start time
    start_time = time.time()
    # Clear the text box
    song_text_box.delete(1.0, "end")
    # Reset the emotion label
    emotion_label.configure(text="")
    # Start processing the frames
    process_frame()

# Function to open Spotify track URL
def open_spotify_track(url):
    webbrowser.open(url)

# Function to process each frame and update the emotion label and suggested songs
def process_frame():
    # Check if one minute has passed
    if time.time() - start_time >= 60:
        cap.release()  # Release the video capture
        return

    _, frm = cap.read()
    frm = cv2.flip(frm, 1)

    res = holis.process(cv2.cvtColor(frm, cv2.COLOR_BGR2RGB))

    if res.face_landmarks:
        lst = []

        for i in res.face_landmarks.landmark:
            lst.append(i.x - res.face_landmarks.landmark[1].x)
            lst.append(i.y - res.face_landmarks.landmark[1].y)

        if res.left_hand_landmarks:
            for i in res.left_hand_landmarks.landmark:
                lst.append(i.x - res.left_hand_landmarks.landmark[8].x)
                lst.append(i.y - res.left_hand_landmarks.landmark[8].y)
        else:
            for _ in range(42):
                lst.append(0.0)

        if res.right_hand_landmarks:
            for i in res.right_hand_landmarks.landmark:
                lst.append(i.x - res.right_hand_landmarks.landmark[8].x)
                lst.append(i.y - res.right_hand_landmarks.landmark[8].y)
        else:
            for _ in range(42):
                lst.append(0.0)

        lst = np.array(lst)
        lst = np.expand_dims(lst, axis=0)

        pred = label[np.argmax(model.predict(lst))]
        emotion_label.configure(text=pred)

        # Get song recommendations based on the recognized emotion
        try:
            recognized_moods = [pred]  # Use the recognized emotion as the mood
            mood_genre_mapping = {
                "Happy": ["pop", "dance"],
                "Sad": ["sad", "acoustic", "instrumental"],
                "Angry": ["rock", "metal"],
                "Surprised": ["electronic", "party"],
                "Neutral": ["pop", "rock"],
            }
            seed_genres = mood_genre_mapping.get(pred, ["pop"])  # Default to "pop" if mood not found in mapping

            recommendations = sp.recommendations(seed_genres=seed_genres, limit=10)
            song_text_box.delete(1.0, "end")  # Clear previous suggestions
            for i, track in enumerate(recommendations['tracks']):
                track_name = f"{track['name']} - {track['artists'][0]['name']}"
                track_url = track['external_urls']['spotify']
                song_text_box.insert("end", f"{track_name}\n", f"hyperlink_{i}")  # Insert song suggestion with hyperlink tag
                song_text_box.tag_configure(f"hyperlink_{i}", foreground="green", underline=True)  # Configure hyperlink tag
                song_text_box.tag_bind(f"hyperlink_{i}", "<Button-1>", lambda event, url=track_url: open_spotify_track(url))  # Bind hyperlink tag to open Spotify track URL
        except spotipy.exceptions.SpotifyException as e:
            print("Error:", str(e))

    frm = cv2.cvtColor(frm, cv2.COLOR_BGR2RGB).astype(np.uint8)
    frm = Image.fromarray(frm)
    frm = ImageTk.PhotoImage(image=frm)

    video_label.configure(image=frm)
    video_label.image = frm

    window.after(int(1000 / fps), process_frame)


video_label.pack()

# Run the Tkinter event loop
window.mainloop()
