# ohrenbaer-podcast
Script which helps to load all available podcast audio files from [OHRENBÄREN-Podcast][lnk_podcast] via parsing the site-content for downloadlinks

## Getting Started
Get a fork of the repo or download code

### Requirements
I used Python 3.6.3 and the additional packages listed in requirements.txt. Use the file to get all necessary packages.

```
pip install -r requirements.txt
```

### Quick start
Just run script to start loading available files.
```
python main.py'
```

### Optional arguments
Show help message
```
-h, --help
```

Show program's version number
```
--version, -v
```

Specify output dir (default: %userprofile%/Desktop/ohrenbaer_podcast)
```
--output-dir <PATH>, -o <PATH>
```

Specify URL to podcast site with download links (default: [link][lnk_podcast])
```
--podcast-url <URL>, -u <URL>
```

## Contribution

Feel free to send pull requests.

[lnk_podcast]: https://www.ohrenbaer.de/podcast/podcast.html
