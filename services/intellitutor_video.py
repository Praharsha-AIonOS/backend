# Video composition utilities for IntelliTutor (Feature 4)
import os
import subprocess


def compose_video(slide_images, avatar_video, duration, output_video):
    per_slide = duration / len(slide_images)
    slide_videos = []

    for i, img in enumerate(slide_images):
        out = output_video.replace(".mp4", f"_slide_{i}.mp4")
        subprocess.run(
            ["ffmpeg", "-y", "-loop", "1", "-i", img, "-t", str(per_slide),
             "-vf", "scale=1280:720", "-c:v", "libx264", "-pix_fmt", "yuv420p", out],
            check=True,
        )
        slide_videos.append(out)

    # FFmpeg concat expects paths relative to the concat file location.
    concat = output_video.replace(".mp4", "_concat.txt")
    concat_dir = os.path.dirname(concat)
    with open(concat, "w") as f:
        for v in slide_videos:
            # Write only the basename so ffmpeg, which is given the concat file path,
            # can resolve files relative to storage/outputs/...
            f.write(f"file '{os.path.basename(v)}'\n")

    bg = output_video.replace(".mp4", "_bg.mp4")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat,
            "-c",
            "copy",
            bg,
        ],
        check=True,
    )

    subprocess.run(
        ["ffmpeg", "-y", "-i", bg, "-i", avatar_video,
         "-filter_complex", "[1:v]scale=300:-1[av];[0:v][av]overlay=W-w-20:H-h-20",
         "-map", "0:v", "-map", "1:a?", "-shortest", output_video],
        check=True,
    )
    return output_video

