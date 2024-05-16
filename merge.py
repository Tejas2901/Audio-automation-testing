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

def get_random_start(merged_audio, duration = 10000):
    random_start = random.randint(0, len(merged_audio) - duration)
    return random_start

def select_clip(merged_audio, ad_start, start_points, duration = 10000):
    overlap = 0.5 * duration
    clip = merged_audio[ad_start: ad_start + duration]
    for i, (start_point, file_name) in enumerate(start_points.items()):
        try:
            if (start_point <= ad_start + overlap < list(start_points.keys())[i+1]):
                clip.export(file_name, format = "mp3")
                return file_name
        except:
            clip.export(file_name, format = "mp3")
            return file_name

def recognize_audio(file_path: str, file_format: str):
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


def consective_random(merged_audio, recorded_merged, start_points, no_of_test_cases, result_csv_name):
    with open(result_csv_name, 'w', newline='') as csvfile:
        fieldnames = ['iter', 'random_start', 'ad_start','actual_ad','in_db', 'detected_ad', 'input_confidence', 'result',]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        total_random_starts = int(no_of_test_cases // 3 )
        with tqdm(total= no_of_test_cases) as pbar:
            for i in range(total_random_starts):
                random_start = get_random_start(merged_audio)
                for j in range(3):
                    duration = 10000
                    ad_start = random_start + j * duration
                    clip_name = select_clip(recorded_merged, ad_start, start_points)
                    data = recognize_audio(clip_name, "mp3")
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

def contiguous_random(merged_audio, recorded_merged, start_points, no_of_test_cases, result_csv_name):
    duration = 10000
    with open(result_csv_name, 'w', newline='') as csvfile:
        fieldnames = ['iter', 'random_start', 'ad_start','actual_ad','in_db', 'detected_ad', 'input_confidence', 'result',]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        total_random_starts = int(no_of_test_cases // 6)
        with tqdm(total=no_of_test_cases) as pbar:
            for i in range(100):
                random_start = get_random_start(merged_audio)
                ad_starts = get_contiguous_list(random_start, duration, recorded_merged)

                for key,value in ad_starts.items():
                    clip_name = select_clip(recorded_merged, value[0], start_points, duration = value[1])
                    ad_start = value[0]
                    actual_ad = clip_name.split(".mp3")[0]
                    slice_name = key
                    data = recognize_audio(clip_name, "mp3") 
                    try:
                        max_confidence_ad = max(data, key = lambda x: x['input_confidence'])
                    except:
                        continue
                    detected_ad = max_confidence_ad['song_name']
                    in_db = actual_ad in not_in_db
                    input_confidence = max_confidence_ad['input_confidence']
                    result = (detected_ad == actual_ad) or (detected_ad != actual_ad and (actual_ad in not_in_db))
                    writer.writerow({'iter': slice_name, 'random_start': random_start, 'ad_start': ad_start, 'actual_ad': actual_ad,'in_db': in_db, 'detected_ad': detected_ad, 'input_confidence': input_confidence, 'result': result})
                    pbar.update(1)
        print("csv done")
                      
def get_contiguous_list(random_start, duration, recorded_merged):
    ad_starts = {}
    first_10_slice = (random_start, duration)
    second_10_slice = (random_start + duration, duration)
    third_10_slice = (random_start + 2 * duration, duration)
    first_20_slice = (random_start, 2 * duration)
    second_20_slice = (random_start + duration, 2 * duration)
    thirty_second = (random_start, 3 * duration)

    ad_starts['first_10_slice'] = first_10_slice
    ad_starts['second_10_slice'] = second_10_slice
    ad_starts['third_10_slice'] = third_10_slice
    ad_starts['first_20_slice'] = first_20_slice
    ad_starts['second_20_slice'] = second_20_slice
    ad_starts['thirty_second'] = thirty_second

    return ad_starts 
    
def main():
    audio_files_dir = "audio_files"
    input_recorded_file = "mergedrecordedclean1.mp3"
    result_csv_name = "clean_settings_nb-7.csv"
    no_of_test_cases = 600

    audio_files = [file for file in os.listdir(audio_files_dir) if file.endswith(".mp3")]
    audios = {file: AudioSegment.from_mp3(os.path.join(audio_files_dir, file)) for file in audio_files}

    merged_audio, start_points = merge_audios(audios)
    merged_audio.export("merged_audio_file.mp3", format="mp3")
    recorded_merged = AudioSegment.from_mp3(input_recorded_file)
    consective_random(merged_audio, recorded_merged, start_points, no_of_test_cases,result_csv_name)
    #contiguous_random(merged_audio, recorded_merged, start_points, no_of_test_case, result_csv_name)

if __name__ == "__main__":
    main()
