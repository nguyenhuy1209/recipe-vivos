import argparse
import librosa
import pyrubberband as pyrb
import os
import soundfile as sf
import threading
import time

NUM_THREADS = 4

if __name__ == '__main__':
    """
    audio_folder_path  (str)    : path to original audio folder
    output_folder_path (str)    : path to shifted audio folder
    rate               (int)    : stretch factor
    """
    parser = argparse.ArgumentParser(description="VIVOS Dataset speed perturbation.")
    parser.add_argument(
        "--audio_folder_path",
        help="path to original audio folder",
        type=str
    )
    parser.add_argument(
        "--output_folder_path",
        help="path to shifted audio folder",
        type=str,
    )
    parser.add_argument(
        "--rate",
        help="stretch factor",
        default=0.9,
        type=float,
    )

    args = parser.parse_args()

    audio_folder_path = args.audio_folder_path
    output_folder_path = args.output_folder_path
    rate = args.rate

    # Create directory
    os.makedirs(output_folder_path, exist_ok=True)

    spk_list = os.listdir(os.path.join(audio_folder_path, 'waves'))
    spk_per_thread = int(len(spk_list) / NUM_THREADS)

    def speed_perturabate_job(thread_index):
        if thread_index == NUM_THREADS - 1:
            thread_spk_list = spk_list[thread_index*spk_per_thread:]
        else:
            thread_spk_list = spk_list[thread_index*spk_per_thread: \
                                            thread_index*spk_per_thread+spk_per_thread]

        for spk in thread_spk_list:
            apath = os.path.join(audio_folder_path, 'waves', spk)
            opath = os.path.join(output_folder_path, 'waves', spk)
            os.makedirs(opath, exist_ok=True)

            for f in os.listdir(apath):
                audio_path = os.path.join(apath, f)
                output_path = os.path.join(opath, f)

                # Read audio file
                audio, sr = librosa.load(audio_path, sr=16000)

                # Perturbating sound
                # audio_perb = librosa.effects.time_stretch(audio, rate)
                audio_perb = pyrb.time_stretch(audio, sr, rate)

                # Export perturbated audio file
                sf.write(output_path, audio_perb, 16000, 'PCM_16')
    
    thread_list = list()
    start_time = time.time()
    for i in range(NUM_THREADS):
        thread = threading.Thread(target=speed_perturabate_job, args=(i,))
        thread_list.append(thread)
        thread.start()
    for thread in thread_list:
        thread.join()
    print(f"Finished, time: {time.time() - start_time}")