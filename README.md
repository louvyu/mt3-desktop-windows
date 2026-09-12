# MT3 Windows Desktop APP

This is a local desktop conversion tool based on MT3 (Multi-Task Multitrack Music Transcription). It features a sleek, modern glassmorphism UI and supports one-click audio-to-MIDI conversion using local CPU or GPU environments.

## Acknowledgements

This project is built upon and inspired by the following open-source works:

* **Core PyTorch Model Implementation**: [gudgud1014/MR-MT3](https://huggingface.co/gudgud1014/MR-MT3) (MIT License).
* **Desktop Application Reference**: [qauzy/mt3](https://github.com/qauzy/mt3).
* **Original MT3 Algorithm**:
  > Gardner, Josh and Simon, Ian and Manilow, Ethan and Hawthorne, Curtis and Engel, Jesse. "MT3: Multi-Task Multitrack Music Transcription." arXiv preprint arXiv:2111.03017 (2021).

## Disclaimer and Usage Notes

Due to repository size limitations, this source code repository does not contain the required `pretrained` model weights, FFmpeg binaries, or CUDA DLLs necessary for local execution. 

To run or build this application locally:
1. Download the complete `pretrained` resource folder from the Releases page.
2. Extract and place the `pretrained` folder in the same directory as the main executable or the root directory of the source code.

## License

This project is open-sourced under the [GPLv3 License](LICENSE).
