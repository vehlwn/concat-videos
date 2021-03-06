import itertools
import os
import re
import subprocess
import sys
import tempfile
import argparse
import os.path


def _existing_dir(s: str):
    if os.path.isdir(s):
        return s
    raise argparse.ArgumentTypeError(f"'{s}' is not an existing directory")


parser = argparse.ArgumentParser(
    description="Concatenate and group small videos by cam_id, date and hour",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    "--target-dir",
    type=_existing_dir,
    required=True,
    help="path to a directory where small files need to be concatenated",
)
args = parser.parse_args()

VIDEO_EXT = ".mkv"
AUDIO_EXT = ".wav"
VIDEO_FNAME_REGEX = re.compile(
    R"(\d\d\d\d-\d\d-\d\d)_((\d\d).\d\d.\d\d)_(\d+)" + VIDEO_EXT
)


class VideoFile:
    def __init__(
        self,
        video_path: str,
        date: str,
        time: str,
        hour: str,
        cam_id: str,
        audio_path: str,
    ):
        self.video_path = video_path
        self.date = date
        self.time = time
        self.hour = hour
        self.cam_id = cam_id
        self.audio_path = audio_path

    def add_audio(self):
        tmp_fname = self.video_path + ".old"
        print(f"rename {self.video_path=}, {tmp_fname=}")
        os.rename(self.video_path, tmp_fname)
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-i",
                tmp_fname,
                "-i",
                self.audio_path,
                "-map",
                "0:v",
                "-map",
                "1:a",
                "-c:v",
                "copy",
                "-shortest",
                self.video_path,
            ],
            check=True,
        )
        print(f"remove {tmp_fname}")
        os.remove(tmp_fname)
        print(f"remove {self.audio_path}")
        os.remove(self.audio_path)


entries = []
for f in os.scandir(args.target_dir):
    if f.is_file():
        m = VIDEO_FNAME_REGEX.match(f.name)
        audio_path = os.path.splitext(f.path)[0] + AUDIO_EXT
        if m and os.path.isfile(audio_path):
            entries.append(
                VideoFile(
                    f.path,
                    m.group(1),
                    m.group(2),
                    m.group(3),
                    m.group(4),
                    audio_path,
                )
            )

if not entries:
    print("No files found. Exitting.")
    sys.exit()

entries.sort(key=lambda x: x.time)
entries.sort(key=lambda x: x.date)
entries.sort(key=lambda x: x.cam_id)
for x in entries:
    print(x.video_path, x.date, x.time, x.hour)
print(f"{len(entries)=}")

print("====Mixing audio...")
for x in entries:
    x.add_audio()

for cam_id, cam_group in itertools.groupby(entries, lambda x: x.cam_id):
    cam_dir = os.path.join(args.target_dir, "camera_" + cam_id)
    os.makedirs(cam_dir, exist_ok=True)
    for date, date_group in itertools.groupby(cam_group, lambda x: x.date):
        date_dir = os.path.join(cam_dir, date)
        os.makedirs(date_dir, exist_ok=True)
        for hour, hour_group in itertools.groupby(date_group, lambda x: x.hour):
            output_fname = os.path.join(date_dir, f"{date}_{hour}.00.00.mkv")
            with tempfile.NamedTemporaryFile(delete=False) as file_files:
                input_small_files = []
                tmp_files_fname = file_files.name
                if os.path.exists(output_fname):
                    old_output_fname = output_fname + ".old"
                    print(f"Output fname exists, renaming to '{old_output_fname}'")
                    os.rename(output_fname, old_output_fname)
                    input_small_files.append(old_output_fname)
                    file_files.write(
                        "file '{}'\n".format(old_output_fname).encode("utf-8")
                    )
                for x in hour_group:
                    s = x.video_path
                    input_small_files.append(s)
                    file_files.write("file '{}'\n".format(s).encode("utf-8"))
            print(f"===={output_fname=}")
            print(f"{input_small_files=}")
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    tmp_files_fname,
                    "-c",
                    "copy",
                    output_fname,
                ],
                check=True,
            )
            os.remove(tmp_files_fname)
            for y in input_small_files:
                os.remove(y)
