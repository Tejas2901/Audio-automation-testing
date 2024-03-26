import os
from pydub import AudioSegment

def merge_audios(audios):
    merged_audio = AudioSegment.empty()
    start_points = {}
    start_point = 0
    for file_name, segment in audios.items():
        merged_audio =  merged_audio.append(segment, crossfade = 0)
        start_points[start_point] = file_name
        start_point += len(segment)
    return merged_audio, start_points

if __name__ == "__main__":
    directory = "audio_files"
    audio_files  = [file for file in os.listdir(directory) if file.endswith(".mp3")]
    audios = {file: AudioSegment.from_mp3(os.path.join(directory, file)) for file in audio_files}
    merged_audio, start_points = merge_audios(audios)
    merged_audio.export("merged_audio_file.mp3", format = "mp3")
    print("Start Points", start_points)


