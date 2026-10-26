# Downloading and transcribing chat audio (Evolution API v2.3.7)

Use this only when the user asks to transcribe or read audio from a chat. Nothing here sends a message; it is read-only.

## Procedure
1. Select the audio messages first: `POST /chat/findMessages/{instance}` (paginate newest-first), keep records with `messageType == "audioMessage"` inside the requested window, and dedupe by `key.id`. Save each record's `key` object, since the download call needs it.
2. Download each audio: `POST /chat/getBase64FromMediaMessage/{instance}` with body `{"message":{"key":KEY},"convertToMp4":false}`. The response is `201` with `base64` (the `buffer` field is `None`) and `mimetype` such as `audio/ogg; codecs=opus`. Decode `base64` and write to a file in the scratch directory, named by `key.id` with `.ogg` extension.
3. Confirm each file is non-empty before transcribing.
4. Transcribe with the local CLI: `transcribe-whisper text <file> <out.txt> -l pt` (output path is the 2nd positional arg; it also prints the text). Run it from a shell with the Python env stripped: `env -u VIRTUAL_ENV -u PYTHONPATH -u PYTHONHOME -u CONDA_PREFIX transcribe-whisper ...` via the terminal tool. Calling it from `subprocess` inside the execute_code kernel inherits the kernel's Python env and fails with a NumPy import error (`numpy._core._multiarray_umath`).
5. Speaker attribution: in groups, map `key.participantAlt` (phone JID) to a person with `bmoca-app people resolve --phone <digits> --json` (unregistered = `Falante não identificado (…1234)`); the `pushName` can be a raw numeric ID or the account owner's label (`fromMe`), so fall back to the phone number rather than guessing. Names heard inside transcripts are often mis-transcribed; use only names that are clear.

## Pitfalls
- Check the presence of `base64` in the body, not the status code; the endpoint returns 201.
- macOS does not ship `timeout`. Do not wrap the CLI in `timeout`; run it directly, or run the loop as a tracked background process with completion notification.
- Transcribing many clips is slow. Run the loop in the background with one output file per clip, then read the files when the completion notice arrives, instead of blocking on the whole batch.
- Transcripts are not summaries. Report what each speaker said, and mark any unclear passage as unclear rather than filling the gap.
- Voice notes from group members are personal content; attribute each transcript to its `pushName` and keep only what is needed for the request.
