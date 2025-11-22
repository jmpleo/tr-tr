from setuptools import setup, find_packages
import subprocess
import sys
import os

def build_windows_exe():
    import PyInstaller.__main__

    repo_exists = os.path.exists('repo')
    if not repo_exists:
        print("Warning: 'repo' directory not found. Model files won't be included.")

    build_args = [
        'main.py',
        '--name=TrTr',
        '--onedir',
        '--clean',
        '--icon=icon.ico' if os.path.exists('icon.ico') else '',
        # PyQt6 hidden imports
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtNetwork',
        # Your existing hidden imports
        '--hidden-import=faster_whisper',
        '--hidden-import=transformers',
        '--hidden-import=torch',
        '--hidden-import=torch._C',
        '--hidden-import=ctranslate2',
        '--hidden-import=huggingface_hub',
        '--hidden-import=transformers.models.auto',
        '--hidden-import=transformers.models.opus_mt',
        # Add these critical imports
        '--collect-all=faster_whisper',
        '--collect-all=ctranslate2',
        '--collect-all=torch',
    ]

    if repo_exists:
        build_args.append('--add-data=repo:repo')

    PyInstaller.__main__.run(build_args)

if __name__ == "__main__":
    build_windows_exe()