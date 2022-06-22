import itertools
import os
import re
import subprocess
import sys
import tempfile

target_dir = "/home/vehlwn/projects/python/concat-videos/video"
remove_small_files = True

fname_regex = re.compile(R"(\d\d\d\d-\d\d-\d\d)_(\d\d).\d\d.\d\d_(\d+)-\d+.mkv")


class ParsedEntry:
    def __init__(self, f: os.DirEntry, date: str, hour: str, cam_id: str):
        self.f = f
        self.date = date
        self.hour = hour
        self.cam_id = cam_id


entries = []
for f in os.scandir(target_dir):
    if f.is_file():
        m = fname_regex.match(f.name)
        if m:
            entries.append(ParsedEntry(f, m.group(1), m.group(2), m.group(3)))
entries.sort(key=lambda x: x.f.name)

if not entries:
    print("No files found. Exitting.")
    sys.exit()

for x in entries:
    print(x.f.name, x.date, x.hour)

for cam_id, cam_group in itertools.groupby(entries, lambda x: x.cam_id):
    cam_dir = os.path.join(target_dir, "camera_" + cam_id)
    os.makedirs(cam_dir, exist_ok=True)
    for date, date_group in itertools.groupby(cam_group, lambda x: x.date):
        date_dir = os.path.join(cam_dir, date)
        os.makedirs(date_dir, exist_ok=True)
        for hour, hour_group in itertools.groupby(date_group, lambda x: x.hour):
            with tempfile.NamedTemporaryFile(delete=False) as file_files:
                tmp_files_fname = file_files.name
                input_small_files = []
                for x in hour_group:
                    s = os.path.abspath(x.f.name)
                    input_small_files.append(s)
                    file_files.write("file '{}'\n".format(s).encode("utf-8"))
            output_fname = os.path.join(date_dir, f"{date}_{hour}.00.00.mkv")
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
            if remove_small_files:
                for y in input_small_files:
                    os.remove(y)
