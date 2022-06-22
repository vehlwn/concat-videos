# concat-videos

Concatenate and group small videos from [motion](https://github.com/Motion-Project/motion) by cam_id, date and hour.

Requires ffmpeg binary.

## Help

```bash
$ python main.py -h
usage: main.py [-h] --target-dir TARGET_DIR [--remove-input-files {0,1}]

Concatenate and group small videos by cam_id, date and hour

optional arguments:
  -h, --help            show this help message and exit
  --target-dir TARGET_DIR
                        path to a directory where small files need to be
                        concatenated (default: None)
  --remove-input-files {0,1}
                        deletes input files after concatenation (default: 1)
```
