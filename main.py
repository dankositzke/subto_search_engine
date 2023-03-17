import os, time
from pymongo import MongoClient
import certifi
from functions import mp4_to_mp3, start_transcription, transcription_status
from functions import extract_video_name, get_transcript_paragraphs_with_timestamps
from pprint import pprint

file_to_transcribe = r"c:\\Users\\Danie\\Subto_Videos\\raising_private_capital\\TEST2_Wanted a Brochure - Melvin - 5-28-20.mp4"
video_name = extract_video_name(file_to_transcribe)
file_to_transcribe = mp4_to_mp3(file_to_transcribe)
polling_endpoint, transcript_id = start_transcription(file_to_transcribe)

status = transcription_status(polling_endpoint)

while status != "completed":
    # print(status)
    time.sleep(15)
    status = transcription_status(polling_endpoint)

# Set up MongoDB
ca = certifi.where()
MONGODB_PW = os.getenv("MONGODB_PW")

cluster = f"mongodb+srv://dankositzke:{MONGODB_PW}@cluster0.vqape.mongodb.net/real_estate?retryWrites=true&w=majority"
client = MongoClient(cluster, tlsCAFile=ca)

pprint("MongoDB connection established.")

collection = client.real_estate.videos

result = collection.insert_many(
    get_transcript_paragraphs_with_timestamps(
        transcript_id,
        video_name,
    )
)

pprint(result)
