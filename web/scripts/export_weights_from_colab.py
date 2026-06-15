"""
Run this cell in Google Colab AFTER training to download your trained weights.

Your notebook saves to:
  /content/drive/MyDrive/AD_PD_Project/final_model.pth
  /content/drive/MyDrive/AD_PD_Project/best_model.pth

Then copy the downloaded file to:
  neurofusenet_web/weights/final_model.pth
"""

# ── Paste in Colab ──────────────────────────────────────────────────────────
# from google.colab import files
# import shutil, os
#
# SAVE_DIR = '/content/drive/MyDrive/AD_PD_Project'
# src = f'{SAVE_DIR}/final_model.pth'
# if not os.path.exists(src):
#     src = f'{SAVE_DIR}/best_model.pth'
#
# if os.path.exists(src):
#     print(f'Downloading {src} ({os.path.getsize(src)/1e6:.1f} MB)...')
#     files.download(src)
# else:
#     print('No weights found! Run training cells first.')
