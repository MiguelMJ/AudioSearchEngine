<h1 align="center">Audio Search Engine</h1>

<h3 align="center">Search inside audio files</h3>

<p align="center">
    <a href="https://core.telegram.org/"><img src="https://img.shields.io/badge/-Telegram-black?style=for-the-badge&logo=telegram"></a>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/-Python_3-black?style=for-the-badge&logo=python"></a>
    <a href="https://deepgram.com"><img src="https://img.shields.io/badge/-Deepgram-black?style=for-the-badge"></a>
    <a href="LICENSE"><img " src="https://img.shields.io/badge/License-MIT-black?style=for-the-badge"></a>
</p>

Search for words inside audio files or Telegram voicemails. Powered by Deepgram. Requires API keys from Deepgram and optionally Telegram. Submission for Deepgram+DEV hackathon, 2022.

## Get the API keys
- Deepgram (required): Create an account in deepgram.com and get an API key.
- Telegram (optional): Create an account in Telegram and follow the steps here: [Obtaining api_id](https://core.telegram.org/api/obtaining_api_id)
   
Store them in files named `deepgramApiKey`, `telegramApiId` and `telegramApiHash` in the root folder or pass them directly in the CLI using the `--deepgram-api-key`, `--telegram-api-id` and `--telegram-api-hash` arguments.

## Features
- **Tune the voice recognition process** with the Deepgram [query parameters for transcriptions pre-recorded audio](https://developers.deepgram.com/api-reference/#transcription-prerecorded) with `-P|--param KEY=VALUE` arguments.
- Search directly in **local files** passing them as arguments after the search term.
- Automatically **download audios from chats in Telegram** with one or more `-T|--telegram-chat CHAT_ID` arguments.
- Downloads and results are **cached to reduce redundant traffic**, but you can force it using the `-F|--force` flag or directly removing the `_cache` and `_audio` folders.
- Search for **partial matches or for whole words** using the `-W|--whole-word` flag.
- Include a bit of the context in which the word was said for each hit.
- All log information outputs through stderr and the search output through stdout (or a file, with the `-o|--output-file FILE` argument). This makes it easy to redirect and **pipe different information safely**.
- Output in the following JSON format:
    ```
    [                        // list of audio files with matches
      {
        "source_file":str,   // path to the audio file
        "duration":num,      // duration of the file
        "hits": [            // list of hits in the file
          {
            "position":num,  // position of the word in the transcript
            "start":num,     // start time in the audio
            "end":num,       // end time in the audio
            "context":str,   // text in the transcript surrounding the match
          },
          ...        
        ]
      },
      ...
    ]
    ```
     
## Quick start
- Install all dependencies (`telethon` too):
    ```bash
    pip install -r requirements.txt
    ```
- Search for a term in local files:
    ```bash
    python main.py TERM FILES...
    ```
- Search for a term in audios from chats in Telegram:
    ```bash
    python main.py TERM -T CHAT1 -T CHAT2 ...
    ```
- Print all available options:
    ```
    python main.py -h
    ```

## Contributing
- See the [CONTRIBUTING](CONTRIBUTING) file to make a PR.
- :star: Star this repository [![](https://img.shields.io/github/stars/MiguelMJ/AudioSearchEngine?style=social)](https://github.com/MiguelMJ/AudioSearchEngine/stargazers)
- Raise an issue  [![](https://img.shields.io/github/issues/MiguelMJ/AudioSearchEngine?style=social&logo=github)](https://github.com/MiguelMJ/AudioSearchEngine/issues).

## Contributors
Empty section, for now ;)

## Ideas for the future

- Add more remote audio sources, apart from Telegram chats (maybe Discord?).
- Make the search process more flexible using an edit-distance based match, instead of only exact matches.
- Allowing more complex queries: multiple words, regular expresions, etc.
- If you can think of another one, feel free to make a PR!

        
## License
This code is licensed under the MIT license, a copy of which is available in the repository.
