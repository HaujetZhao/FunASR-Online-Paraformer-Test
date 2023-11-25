import soundfile
from funasr_onnx.paraformer_online_bin import Paraformer
from pathlib import Path
import subprocess
import wave
import numpy as np
import time

# 先用 ffmpeg 转格式
file_path = 'audio/out.wav'
wav_path = 'audio/temp.wav'
command = ['ffmpeg', '-y', '-i', file_path, '-ar', '16000', '-ac', '1', wav_path]
subprocess.run(command, capture_output=True)

# 载入模型
model_dir = 'model'
chunk_size = [20, 40, 20] # 左回看，片段，右回看，单位 60ms
model = Paraformer(model_dir, batch_size=1, quantize=True, chunk_size=chunk_size, intra_op_num_threads=4) # only support batch_size = 1

##online asr
print('开始识别了')
print(f'chunk_size: {chunk_size}')
speech, sample_rate = soundfile.read(wav_path)
speech_length = speech.shape[0]
sample_offset = 0
step = chunk_size[1] * 960
param_dict = {'cache': dict()}
final_result = ""
for sample_offset in range(0, speech_length, min(step, speech_length - sample_offset)):
    if sample_offset + step >= speech_length - 1:
        step = speech_length - sample_offset
        is_final = True
    else:
        is_final = False
    param_dict['is_final'] = is_final
    data = speech[sample_offset: sample_offset + step]
    data = data.astype(np.float32)
    rec_result = model(audio_in=data, param_dict=param_dict)
    if len(rec_result) > 0:
       final_result += rec_result[0]["preds"][0]
    if rec_result:
        print(rec_result[0]['preds'][0], end='', flush=True)
print('')
