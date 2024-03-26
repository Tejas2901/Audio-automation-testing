import os
import random
import requests
import asyncio
from pydub import AudioSegment

def merge_audios(audios):
    merged_audio = AudioSegment.empty()
    start_points = {}
    start_point = 0
    print(audios.items)
    for file_name, segment in audios.items():
        merged_audio =  merged_audio.append(segment, crossfade = 0)
        start_points[start_point] = file_name
        start_point += len(segment)
    return merged_audio, start_points

def select_random_clip(merged_audio, start_points, duration = 10000, overlap = 5000):
    random_start = random.randint(0, len(merged_audio) - duration)
    print("random start ", random_start)
    clip = merged_audio[random_start: random_start + duration]
    for i, (start_point, file_name) in enumerate(start_points.items()):
        try:
            if (start_point <=random_start + overlap < list(start_points.keys())[i+1]):
                clip.export(file_name, format = "mp3")
                print("file name", file_name)
                return file_name
        except:
            clip.export(file_name, format = "mp3")
            print("last_file",file_name)
            return file_name

async def recognize_audio(file_path: str, file_format: str):
    try:
        with open(file_path, 'rb') as file:
            files = {'file': (os.path.basename(file_path), file, file_format)}
            headers = {'Accept': 'application/json'}
            response = requests.post('http://localhost:8000/api/v2/decode', files=files, headers=headers)

            if response.status_code == 200:
                os.unlink(file_path)  # Delete the file after successful recognition
                return response.json()
            else:
                print(f"Failed to recognize audio. Status code: {response.status_code}")
                return None
    except Exception as error:
        print('Error decoding audio:', error)
        return None

async def main():
    directory = "audio_files"
    audio_files = [file for file in os.listdir(directory) if file.endswith(".mp3")]
    audios = {file: AudioSegment.from_mp3(os.path.join(directory, file)) for file in audio_files}
    merged_audio, start_points = merge_audios(audios)
    merged_audio.export("merged_audio_file.mp3", format="mp3")
    recorded_merged = AudioSegment.from_mp3("admerged.mp3")
    random_clip = select_random_clip(recorded_merged, start_points)

    data = await recognize_audio(random_clip, "mp3")
    print("Start Points", start_points)
    print("\nI am data", data)

if __name__ == "__main__":
    asyncio.run(main())
