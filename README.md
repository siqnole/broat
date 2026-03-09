# Bronx — Stoat.chat Bot

A feature-rich chat bot for [Stoat.chat](https://stoat.chat) built with [stoat.py](https://pypi.org/project/stoat.py/).

## Features

- 🎨 **Rich Embeds** — Beautiful formatted messages with colors, titles, and descriptions
- 🎮 **Fun Commands** — Games and entertainment (coinflip, dice, 8ball, etc.)
- 🛠️ **Moderation** — Kick, ban, and message management tools
- ℹ️ **Info Commands** — User and server information lookups
- 🔧 **Extensible** — Built with Gears (cogs) for easy command organization

## Setup

1. **Create a virtual environment & install dependencies:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -U stoat.py  # or: pip install -U git+https://github.com/MCausc78/stoat.py@master
   ```

2. **Configure your bot token:**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and replace `your-bot-token-here` with your actual Stoat bot token.

3. **Run the bot:**

   ```bash
   python main.py
   ```

## Commands

### General
| Command      | Description                  |
|-------------|------------------------------|
| `!help`     | Show all commands or get help for a specific command |
| `!ping`     | Measure bot latency (response time, WebSocket, internet) |
| `!uptime`   | Show bot uptime              |
| `!about`    | Bot info & credits           |
| `!echo`     | Repeat your message back     |
| `!say`      | Make the bot say something   |
| `!embedtest`| Demo of rich embed formatting |

### Fun
| Command             | Description                             |
|--------------------|-----------------------------------------|
| `!coinflip`        | Flip a coin                             |
| `!roll [sides]`    | Roll a die (default: d6)                |
| `!8ball <question>` | Ask the magic 8-ball                   |
| `!choose a, b, c`  | Pick from comma-separated options       |
| `!reverse <text>`  | Reverse a string                        |
| `!shout <text>`    | SHOUT YOUR TEXT                         |

### Info
| Command               | Description                        |
|------------------------|------------------------------------|
| `!userinfo [member]`  | Show info about a user             |
| `!serverinfo`         | Show info about the current server |
| `!avatar [member]`    | Get a user's avatar URL            |

### Moderation
| Command                     | Description                            |
|----------------------------|----------------------------------------|
| `!kick <member> [reason]`  | Kick a member                          |
| `!ban <member> [reason]`   | Ban a member                           |
| `!purge [count]`           | Delete last N messages (default 10)    |

## Project Structure

```
bronx/
├── main.py              # Entry point
├── .env.example         # Environment variable template
├── .gitignore
├── README.md            # This file
├── STYLE_GUIDE.md       # Visual styling guidelines
└── bot/
    ├── __init__.py
    ├── core.py          # Bot class, error handling, gear loading
    ├── style.py         # Color & emoji constants
    └── gears/
        ├── __init__.py
        ├── general.py   # help, ping, uptime, about, echo, say, embedtest
        ├── fun.py       # coinflip, roll, 8ball, choose, reverse, shout
        ├── info.py      # userinfo, serverinfo, avatar
        └── moderation.py# kick, ban, purge
```

## Contributing

When adding new commands or features, please follow the [Style Guide](STYLE_GUIDE.md) to maintain visual consistency.

## License

MIT
