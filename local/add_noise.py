import argparse
import numpy as np
import librosa
import os
import soundfile as sf
import random
import threading
import time

NUM_THREADS = 4

def calculate_rms(samples):
    """Given a numpy array of audio samples, return its Root Mean Square (RMS)."""
    return np.sqrt(np.mean(np.square(samples)))

def calculate_desired_noise_rms(clean_rms, snr):
    """
    Given the Root Mean Square (RMS) of a clean sound and a desired signal-to-noise ratio (SNR),
    calculate the desired RMS of a noise sound to be mixed in.
    Based on https://github.com/Sato-Kunihiko/audio-SNR/blob/8d2c933b6c0afe6f1203251f4877e7a1068a6130/create_mixed_audio_file.py#L20
    :param clean_rms: Root Mean Square (RMS) - a value between 0.0 and 1.0
    :param snr: Signal-to-Noise (SNR) Ratio in dB - typically somewhere between -20 and 60
    :return:
    """
    a = float(snr) / 20
    noise_rms = clean_rms / (10 ** a)
    return noise_rms

if __name__ == '__main__':
    """
    audio_path  (str)  : list of paths to original audio files
    noise_path  (str)   : path to noise file
    output_path (str)   : list of paths to export the mixed audio files
    alpha       (float) : parameter to adjust noise strength, larger means more noise strength
    """
    parser = argparse.ArgumentParser(description="VIVOS Dataset noise augumentation.")
    parser.add_argument(
        "--audio_folder_path",
        help="list of paths to original audio files",
        type=str
    )
    parser.add_argument(
        "--noise_path",
        help="path to noise file",
        default='./noises/xe34.wav',
        type=str,
    )
    parser.add_argument(
        "--output_folder_path",
        help="list of paths to export the mixed audio filess",
        type=str,
    )
    parser.add_argument(
        "--min_snr_in_db",
        help="Minimum signal-to-noise ratio in dB",
        default=5,
        type=float,
    )
    parser.add_argument(
        "--max_snr_in_db",
        help="Maximum signal-to-noise ratio in dB",
        default=30,
        type=float,
    )

    args = parser.parse_args()

    audio_folder_path = args.audio_folder_path
    noise_path = args.noise_path
    output_folder_path = args.output_folder_path
    min_snr_in_db = args.min_snr_in_db
    max_snr_in_db = args.max_snr_in_db

    # Read background file
    bg, bg_sr = librosa.load(noise_path, sr=None)

    # Resample noise
    bg = librosa.resample(bg, bg_sr, 16000)
    bg_length = bg.shape[0]

    # Sample-to-noise ratio sampler
    snr_in_db = random.uniform(
        min_snr_in_db, max_snr_in_db
    )

    # Check backgound noise strength
    bg_rms = calculate_rms(bg)
    if bg_rms < 1e-9:
        warnings.warn(
            "The file {} is too silent to be added as noise. Returning the input"
            " unchanged.".format(self.parameters["noise_file_path"])
        )

    # Create directory
    os.makedirs(output_folder_path, exist_ok=True)
    
    spk_list = os.listdir(os.path.join(audio_folder_path, 'waves'))
    spk_per_thread = int(len(spk_list) / NUM_THREADS)

    def add_noise_job(thread_index):
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
                clean_rms = calculate_rms(audio)
                audio_length = audio.shape[0]

                # Check compatibility
                if bg_length < audio_length:
                    raise Exception("Background duration cannot be smaller than audio duration!")

                min_bg_offset = 0
                max_bg_offset = max(0, bg_length - audio_length - 1)
                bg_start_index = random.randint(min_bg_offset, max_bg_offset)
                bg_end_index = bg_start_index + audio_length
                bg_trim = bg[
                    bg_start_index : bg_end_index
                ]

                # Add noise to audio
                desired_noise_rms = calculate_desired_noise_rms(
                    clean_rms, snr_in_db
                )

                # Adjust the noise to match the desired noise RMS
                bg_trim = bg_trim * (desired_noise_rms / bg_rms)
                audio_with_bg = audio + bg_trim
                # start_ = np.random.randint(bg.shape[0] - audio_length)
                # bg_slice = bg[start_ : start_ + audio_length]
                # audio_with_bg = audio + bg_slice * alpha

                # Export noised audio file
                sf.write(output_path, audio_with_bg, 16000, 'PCM_16')
    
    thread_list = list()
    start_time = time.time()
    for i in range(NUM_THREADS):
        thread = threading.Thread(target=add_noise_job, args=(i,))
        thread_list.append(thread)
        thread.start()
    for thread in thread_list:
        thread.join()
    print(f"Finished, time: {time.time() - start_time}")
