import os
import csv
import random
import requests
import asyncio
from tqdm import tqdm
from pydub import AudioSegment

not_in_db = ["saajna", "juice_wrld"]

def merge_audios(audios):
    merged_audio = AudioSegment.empty()
    start_points = {}
    start_point = 0
    for file_name, segment in audios.items():
        merged_audio =  merged_audio.append(segment, crossfade = 0)
        start_points[start_point] = file_name
        start_point += len(segment)
    return merged_audio, start_points

def get_random_start(merged_audio, duration = 2000):
    random_start = random.randint(0, len(merged_audio) - duration)
    return random_start

def select_clip(merged_audio, ad_start, start_points, duration = 2000, overlap = 500):
    clip = merged_audio[ad_start: ad_start + duration]
    for i, (start_point, file_name) in enumerate(start_points.items()):
        try:
            if (start_point <= ad_start + overlap < list(start_points.keys())[i+1]):
                clip.export(file_name, format = "mp3")
                return file_name
        except:
            clip.export(file_name, format = "mp3")
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
    recorded_merged = AudioSegment.from_mp3("mergedrecordedclean1.mp3")

    with open('test_clean_act.csv', 'w', newline='') as csvfile:
        fieldnames = ['iter', 'random_start', 'ad_start','actual_ad','in_db', 'detected_ad', 'input_confidence', 'result',]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        total_iterations = 10 * 3
        with tqdm(total=total_iterations) as pbar:
            for i in range(10):
                random_start = get_random_start(merged_audio)
                for j in range(3):
                    duration = 2000
                    ad_start = random_start + j * duration
                    clip_name = select_clip(recorded_merged, ad_start, start_points)
                    data = await recognize_audio(clip_name, "mp3")
                    try:
                        max_confidence_ad = max(data, key = lambda x: x['input_confidence'])
                    except:
                        continue
                    detected_ad = max_confidence_ad['song_name']
                    actual_ad = clip_name.split(".mp3")[0]
                    iteration = j
                    in_db = actual_ad in not_in_db
                    input_confidence = max_confidence_ad['input_confidence']
                    result = (detected_ad == actual_ad) or (detected_ad != actual_ad and (actual_ad in not_in_db))
                    writer.writerow({'iter': iteration, 'random_start': random_start, 'ad_start': ad_start, 'actual_ad': actual_ad,'in_db': in_db, 'detected_ad': detected_ad, 'input_confidence': input_confidence, 'result': result})
                    pbar.update(1)
        print("csv done")
if __name__ == "__main__":
    asyncio.run(main())
