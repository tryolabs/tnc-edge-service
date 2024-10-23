#!/bin/bash

# see these documentation websites for each filter:
# https://gstreamer.freedesktop.org/documentation/avi/avidemux.html
#  https://gstreamer.freedesktop.org/documentation/nvcodec/nvjpegdec.html

gst-launch-1.0 nvarguscamerasrc num-buffers=$((30*290)) ! 'video/x-raw(memory:NVMM), width=(int)1920, height=(int)1080, format=(string)NV12, framerate=(fraction)30/1' ! nvvidconv  left=240 right=1680 top=0 bottom=1080 ! 'video/x-raw(memory:NVMM), width=(int)1024, height=(int)768, pixel-aspect-ratio=1/1' ! nvjpegenc quality=70 ! videorate drop-only=true ! 'image/jpeg, framerate=(fraction)16/1' ! avimux ! filesink location=/thalos/edge6/videos/picam/27-07-2023/21/27-07-2023-21-50.avi ; mv /thalos/edge6/videos/picam/27-07-2023/21/27-07-2023-21-50.avi{,.done}


gst-launch-1.0 filesrc location="./some_mjpeg.avi" ! avidemux ! nvjpegdec ! nvv4l2h264enc ! avimux ! filesink location=tmp5.avi

# mjpeg to h264
gst-launch-1.0 filesrc location="/thalos/saintpatrick/videos/cam1/06-07-2023/20/06-07-2023-20-10.avi.done" ! avidemux ! nvjpegdec ! nvv4l2h264enc ! avimux ! filesink location=/videos/tmp5.avi

#macos mp4 to images

VF=''
AIF='/Users/ericfultz/Documents/pops/TNC/tnc-edge-service/brancol_jan_aifishoutput/20240122T121500Z_cam1.json'
if [ -d 'frames/' ] ; then
  rm frames/*
  gst-launch-1.0 filesrc location="$VF" ! decodebin ! jpegenc ! multifilesink index=1 location=frames/%d.jpg
  python3 - "$AIF"  <<'EOF' | parallel --colsep "\t" convert "frames/{1}.jpg" -fill none -stroke red -strokewidth 2 -pointsize 24 -draw " {2} " "frames/{1}.jpg"
import sys
import json
from collections import defaultdict
with open(sys.argv[1]) as f:
  ds = [ json.loads(l.strip()) for l in f.readlines()]
  g_by_f = defaultdict(list)
  for d in ds:
    g_by_f[d['frame']].append(f"rectangle {d['xmin']},{d['ymin']} {d['xmax']},{d['ymax']}")
    if d['object_confidence']:
      g_by_f[d['frame']].append(f'text {d["xmin"]},{d["ymin"] + 22} "{d["class_name"]} %{d["object_confidence"]*100:.1f}"')
    else:
      g_by_f[d['frame']].append(f'text {d["xmin"]},{d["ymin"] + 22} "{d["class_name"]}"')
  for k, v in g_by_f.items():
    print(str(k) + "\t" + " ".join(v))
EOF
  ffmpeg -framerate 15 -i 'frames/%d.jpg' -c:v libx264 -crf 30 out.mp4
fi


# thalos's low quality h264 to images
rm /videos/frames/*
gst-launch-1.0 filesrc location="/thalos/saintpatrick/videos/cam1/26-07-2023/14/26-07-2023-14-00.mp4.done" ! qtdemux ! h265parse ! nvv4l2decoder ! nvjpegenc ! multifilesink index=1 location=/videos/frames/%d.jpg


# thalos's high quality to h265
gst-launch-1.0 filesrc location="/thalos/saintpatrick/videos/cam1/26-07-2023/14/26-07-2023-14-00.mp4.done" ! qtdemux ! nvv4l2decoder mjpeg=true ! nvv4l2h265enc bitrate=2000000 ! h265parse ! matroskamux ! filesink location="/videos/"

rm /videos/frames/*
gst-launch-1.0 filesrc location="/videos/20240112T224000Z_cam1.avi" ! avidemux ! multifilesink index=1 location=/videos/frames/%d.jpg



rm /videos/frames/*
gst-launch-1.0 filesrc location="/videos/20240308T124000Z_cam1_reenc.mkv" ! matroskademux ! h265parse ! nvv4l2decoder ! nvjpegenc ! multifilesink index=1 location=/videos/frames/%d.jpg

20230912T133500Z_cam2_ondeck

mkdir ./frames || rm ./frames/*
gst-launch-1.0 filesrc location="$V" ! avidemux ! multifilesink index=1 location=./frames/%d.jpg


F= ; convert $F -fill none -stroke red -strokewidth 1 -draw 'rectangle 426,271 588,625' $F


F=2045.jpg
scp edge1:/videos/frames/$F .
cp $F $F.origg
tr "\n" "\0" <<EOF | xargs -0 -I % convert $F -fill none -stroke red -strokewidth 2 -draw "rectangle %" $F
838,234 928,427
2,2 50,50
EOF
echo "http://192.168.15.82:8000/$F"
python3 -m http.server


{
  "frameNum": 2045,
  "timestamp": "2023-09-12T22:41:49.848852+00:00",
  "bbox": [
    [
      838.4176025390625,
      234.28652954101562,
      928.3148193359375,
      427.3348693847656
    ]
  ],
  "confidence": [
    0.6209518909454346
  ],
  "class": [
    0
  ],



F=1300.jpg
scp edge1:/videos/frames/$F .
cp $F $F.origg
tr "\n" "\0" <<EOF | xargs -0 -I % convert $F -fill none -stroke red -strokewidth 2 -draw "rectangle %" $F
838,234 928,427
EOF
echo "http://192.168.15.82:8000/$F"
python3 -m http.server






for i in 12-09-2023-15-05.avi.done 12-09-2023-15-10.avi.done 12-09-2023-15-15.avi.done 12-09-2023-15-20.avi.done 12-09-2023-15-25.avi.done 12-09-2023-15-30.avi.done 12-09-2023-15-35.avi.done 12-09-2023-15-40.avi.done 12-09-2023-15-55.avi.done ; do
rm /videos/frames/*
gst-launch-1.0 filesrc location="/thalos/brancol/videos/cam2/12-09-2023/15/$i" ! avidemux ! multifilesink index=1 location=/videos/frames/%d.jpg
tar czf ~/$i.tar.gz -C /videos/frames {1,480,960,1440,1920,2400,2880,3360,3840,4320}.jpg
done
