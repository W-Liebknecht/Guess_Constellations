
<h1 align="center">
    	<a href="https://github.com/W-Liebknecht/Guess_Constellations/">
            <img src="https://github.com/W-Liebknecht/Guess_Constellations/stimuli_images/Cyg.png" alt="Cyg"/>
  	    </a>
			<br/> A Constellations Guessing Game
</h1>

# Constellations Guessing Game

A small desktop quiz: it shows a constellation star map and you type its
Chinese name. All 88 constellations are included.

## Requirements

- Python 3.8+ with `tkinter` — bundled with the python.org installers on
  Windows and macOS; on Debian/Ubuntu run `sudo apt install python3-tk`.
- Install the Python packages:

  ```bash
  python -m pip install -r requirements.txt
  ```

## Usage

```bash
python main.py          # normal quiz: 3 questions
python main.py -i       # infinite mode
python main.py -d 1.0   # ask for a harder set of 3 questions
python main.py -t       # check that all 88 images load, then exit
```

| Option | Description |
| --- | --- |
| `-t`, `--test` | Open and verify every image in `stimuli_images/`, report any that fail, then exit. Handy after editing the images or the CSV. |
| `-d`, `--difficulty` | Target *sum* of the difficulties of the 3 questions (default `0.6`). Each constellation is rated `0.1`–`0.4`, so the sum ranges from `0.3` to `1.2` — higher is harder. |
| `-i`, `--infty` | Infinite mode; see below. |

## How to play

Type the Chinese name of the constellation shown and press Enter (or click
提交). The answer is compared exactly against the name in
`stimuli_config.csv`, ignoring surrounding spaces only — there is no partial
credit. Names are 3 or 4 characters.

**Normal mode** picks 3 constellations whose difficulties add up to roughly the
target. When you finish, a summary shows your score, accuracy, elapsed time and
each answer, and the program closes itself after 3 seconds.

**Infinite mode** (`-i`) never ends: every question is a fresh random
constellation out of all 88, with no difficulty target and no summary. Close
the window to stop. Each answer is also printed to the console, which makes it
useful for long practice runs or for sanity-checking the data:

```
[无限模式] 已加载 88 个星座，每题随机出现；输入中文名后回车提交，关闭窗口即可退出。
[1] Boo 答案=牧夫座 输入=牧夫座 -> CORRECT (得分 1/1)
[2] Sct 答案=盾牌座 输入=错误答案 -> WRONG (得分 1/2)
```

> Note: the packaged `main.exe` is built with `console=False`, so on Windows
> this output is only visible when running from source.

## Files

| Path | Purpose |
| --- | --- |
| `main.py` | The whole program (GUI, quiz logic, command-line options). |
| `stimuli_config.csv` | The 88 constellations: index, Chinese name, Latin abbreviation, difficulty. |
| `stimuli_images/` | One PNG per constellation, named after its Latin abbreviation (e.g. `Ori.png`). 800×800 or larger. |
| `main.spec` | PyInstaller recipe for the standalone build. |
| `requirements.txt` | Python dependencies. |

## Building a standalone executable

```bash
python -m pip install pyinstaller
python -m PyInstaller main.spec --clean --noconfirm
```

Build on the platform you are targeting — PyInstaller cannot cross-compile, so
a Windows `.exe` has to be built on Windows. Always build from `main.spec`
rather than `main.py`, since the spec is what bundles the CSV and the images.
