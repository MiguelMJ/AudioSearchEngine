import argparse
import asyncio
import json
import os
import re
import requests
import sys

try:
    import telethon
except:
    telethon = None
#
# Output functions
#
log_level = 2
red = "\033[38;5;9m"
green = "\033[38;5;10m"
yellow = "\033[38;5;11m"
bold = "\033[1m"
reset = "\033[0m"

def no_color():
    global red
    global green
    global yellow
    global bold
    global reset
    red = ""
    green = ""
    yellow = ""
    bold = ""
    reset = ""

def log_info(msg, **kargs):
    if log_level >= 2:
        print(msg, file=sys.stderr, **kargs)
        sys.stderr.flush()


def log_important(msg, **kargs):
    if log_level >= 2:
        print(f"{bold}> {msg}{reset}", file=sys.stderr, **kargs)
        sys.stderr.flush()


def log_success(msg, **kargs):
    if log_level >= 2:
        print(f"{green}\u2714 {msg}{reset}", file=sys.stderr, **kargs)
        sys.stderr.flush()


def log_warning(msg, **kargs):
    if log_level >= 1:
        print(f"{yellow}\u26A0 {msg}{reset}", file=sys.stderr, **kargs)
        sys.stderr.flush()


def log_error(msg, **kargs):
    if log_level >= 0:
        print(f"{red}\u2716 {msg}{reset}", file=sys.stderr, **kargs)
        sys.stderr.flush()


def set_log_level(level):
    global log_level
    if level < -1 or level > 2:
        raise "Invalid log level"
    log_level = level


def abort(code, msg, **kargs):
    log_error(msg, **kargs)
    exit(code)


#
# Cache management
#

## Get the path to a cached response associated to an input file
def get_cache_path(infile):
    ofile = re.sub(r'^\.+', '', infile.replace('/', '_'))
    return f"{cache_dir}/{ofile}"


## Call Deepgram API to get the transcription of an audio
def get_transcription(audio_file, api_token, url_params, **kargs):
    cache_file = get_cache_path(audio_file + ".json")
    log_important(f"Getting transcription [{audio_file}]")
    if kargs.get("ignore_cache"):
        log_info("Ignore cache")
    elif os.path.exists(cache_file):
        log_info("Cache hit")
        with open(cache_file) as f:
            obj = json.load(f)
        transcript = obj["results"]["channels"][0]["alternatives"][0]["transcript"]
        if len(transcript) == 0:
            log_warning(f"Empty transcription")
        else:
            log_success("Transcription returned successfully")
        return obj
    else:
        log_info("Cache fail")
    url_params_str = "&".join(f"{k}={url_params[k]}" for k in url_params)
    url = f"https://api.deepgram.com/v1/listen?{url_params_str}"
    headers = {"Authorization": f"Token {api_token}"}
    with open(audio_file, "rb") as fh:
        response = requests.post(url, headers=headers, data=fh)
        obj = json.loads(response.text)
        obj["source_file"] = audio_file
        if response:
            transcript = obj["results"]["channels"][0]["alternatives"][0]["transcript"]
            if len(transcript) == 0:
                log_warning(f"Empty transcription")
            else:
                log_success("Transcription returned successfully")
            log_info("Saving in cache...")
            with open(cache_file, "w") as f:
                json.dump(obj, f)
            return obj
        else:

            abort(
                response.status_code,
                f"Status {response.status_code}: {obj['error']} - {obj['reason']}",
            )


## Call Telegram API to get the last audios of a chat
async def get_audios(api_id, api_hash, who, limit, audio_dir, cache_file):
    log_important(f"Getting messages [{who}, {limit}]")
    try:
        with open(cache_file) as f:
            cache = json.load(f)
    except IOError:
        cache = {}
    async with await telethon.TelegramClient(
        "anon", api_id, api_hash
    ).start() as client:
        me = await client.get_me()
        audios = []
        msgi = 0
        for message in await client.get_messages(who, limit=limit):
            msgi += 1
            log_info(f"\r\033[JMessage {msgi}/{limit}", end="")
            if message.voice:
                if str(message.id) in cache:
                    dest = cache[str(message.id)]
                    log_info("\r\033[JAudio found (cache): "+dest)
                else:
                    path = await message.download_media()
                    dest = f"{audio_dir}/{path}"
                    os.rename(path, dest)
                    cache[message.id] = dest
                    log_info(f"\r\033[JAudio found: "+dest)
                audios.append(dest)
        log_info("\r\033[J", end="")
        if len(audios) == 0:
            log_warning(f"No audios found in chat with {who}")
        else:
            log_success(f"Audios returned: {len(audios)} from the last {msgi} messages")
            with open(cache_file, "w") as f:
                json.dump(cache, f)
        return audios


## Search for a word in a transcription array and return info about the hits
def perform_search(transcriptions, term, **kargs):
    log_important(f"Searching in audios transcriptions [{term}]")
    search = term.lower()
    audiosNum = len(transcriptions)
    ctxt_size = kargs["context"]
    hits = []
    a_i = 0
    for audio_i in transcriptions:
        a_i += 1
        audio = transcriptions[audio_i]
        possible_hit = {
            "source_file": audio["source_file"],
            "duration": audio["metadata"]["duration"],
            "hits": [],
        }
        words = audio["results"]["channels"][0]["alternatives"][0]["words"]
        wordsNum = len(words)
        for word_i, word in enumerate(words):
            log_info(f"\r\033[J{word['word']}", end="")
            if word["word"] == search:
                possible_hit["hits"].append(
                    {
                        "position": word_i,
                        "start": word["start"],
                        "end": word["end"],
                        "context": " ".join(
                            words[c_i]["punctuated_word"]
                            for c_i in range(
                                max(0, word_i - ctxt_size),
                                min(wordsNum, word_i + ctxt_size + 1),
                            )
                        ),
                    }
                )
        if len(possible_hit["hits"]) > 0:
            hits.append(possible_hit)
    log_info(f"\r\033[J", end="")
    if len(hits) > 0:
        log_success(f"Audios with matches: {len(hits)}")
    else:
        log_warning(f"No audio with matches")
    return hits


## Function to assure that a file is read
def read_folder(path):
    try:
        with open(path) as f:
            text = f.read()
        log_info(f"Successfully read {path}")
        return text
    except IOError as e:
        abort(-1, f"Error encountered reading {path}: {e.what()}")


## Function to assure that a folder exists
def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)


def parse_arguments():
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTIONS] TERM FILES...",
        description=f"Search engine for audios with support for several audio sources. Powered by Deepgram.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Source code: https://github.com/MiguelMJ/AudioSearchEngine",
    )
    parser.add_argument("search", help="Word to search", metavar="TERM")
    parser.add_argument("files", help="Files to perform the search", metavar="FILES", nargs="*")
    parser.add_argument("--no-ansi", help="Don't display color in the output", action="store_true")
    parser.add_argument(
        "-L",
        "--log-level",
        help="log level. -1=quiet, 0=errors, 1=warnings, 2=info (default=2)",
        type=int,
        default=2,
        metavar="NUM",
    )
    parser.add_argument(
        "-C",
        "--context",
        help="number of words to surround the search hits in the output (default=2)",
        type=int,
        default=2,
        metavar="NUM",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        help="file to store the results of the search in a JSON format",
        metavar="FILE"
    )
    group = parser.add_argument_group("Deepgram options")
    group.add_argument(
        "--deepgram-api-key",
        help="Deepgram API key. By default, get it from a file named deepgramApiKey",
        metavar="X",
    )
    group.add_argument(
        "-P",
        "--param",
        help="parameter for the Deepgram URL",
        action="append",
        metavar="X=Y"
    )
    group.add_argument(
        "-F",
        "--ignore-cache",
        help="ignore cached transcriptions and force an API call",
        action="store_true"
    )
    group = parser.add_argument_group("Telegram options")
    group.add_argument(
        "--telegram-api-id",
        help="Telegram API key. By default, get it from a file named telegramApiId",
        metavar="X",
    )
    group.add_argument(
        "--telegram-api-hash",
        help="Telegram API hash. By default, get it from a file named telegramApiHash",
        metavar="X",
    )
    group.add_argument(
        "-T",
        "--telegram-chat",
        help="chat from Telegram to retreive messages from",
        action="append",
        default=[],
        metavar="X"
    )
    group.add_argument(
        "-M",
        "--messages",
        help="number of messages to retreive while looking for audios in each Telegram chat(default=100)",
        type=int,
        default=100,
        metavar="NUM"
    )
    args = parser.parse_args()
    return args


#
# Main
#
if __name__ == "__main__":
    # Initialize folders
    audio_dir = "./_audio"
    cache_dir = "./_cache"
    create_folder(audio_dir)
    create_folder(cache_dir)

    # Parse CLI args
    args = parse_arguments()
    if args.no_ansi:
        no_color()
    set_log_level(args.log_level)
    print(args)
    # Deepgram related info
    deepgram_api_key = args.deepgram_api_key or read_folder("deepgramApiKey")
    deepgram_params = {
        "language": "es",
        "model": "general",
        "punctuate": "true",
        "diarize": "false",
        "utterances": "true",
        "alternatives": "1",    
    }
    if args.param:
        for param in args.param:
            [k,v] = param.split("=")
            deepgram_params[k] = v
    log_info("Deepgram URL params:\n"+"\n".join(f"{k:15}{deepgram_params[k]}" for k in deepgram_params))
    audios = args.files 
    # Telegram search
    if len(args.telegram_chat) > 0:
        if telethon == None:
            abort(-1, "Search in Telegram requires the telethon package installed")
        telegram_api_id = args.telegram_api_id or read_folder("telegramApiId")
        telegram_api_hash = args.telegram_api_hash or read_folder("telegramApiHash")
        for chat in args.telegram_chat:
            audios += asyncio.run(get_audios(
                telegram_api_id,
                telegram_api_hash,
                chat,
                args.messages,
                audio_dir,
                f"{cache_dir}/tg_audio_cache"
            ))
    if len(audios) == 0:
        log_warning("No audios provided")
    else:
        # Get transcriptions
        transcriptions = {
            audio: get_transcription(audio, deepgram_api_key, deepgram_params, ignore_cache=args.ignore_cache)
            for audio in audios
        }
        # Do the search
        hits = perform_search(transcriptions, args.search, context=args.context)
        if args.output_file:
            with open(args.output_file, "w") as out:
                json.dump(hits, ensure_ascii=False, file=out)
        elif len(hits) > 0:
            print(json.dumps(hits, indent=2, ensure_ascii=False))
