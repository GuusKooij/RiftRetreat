# 🎮 RiftRetreat

**RiftRetreat** is a comprehensive League of Legends companion desktop application that provides in-depth analytics, performance insights, champion recommendations, challenge tracking, and performance monitoring for your ranked journey.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

### 📊 Performance Dashboard
- **Overall Stats**: Win rate, KDA, CS/min, vision score, damage, gold
- **Per Champion**: Detailed stats for each champion you play
- **Per Role**: Performance breakdown by role (Top, Jungle, Mid, Bot, Support)
- **Trends**: Rolling 10-game averages and performance over time

### 🔮 Rank Predictor (Context-Aware)
- **Smart Predictions**: Compares your stats to your current rank's averages
- **Role-Specific Analysis**: Tailored predictions for each role
- **Insights**: Identifies your strengths and areas to improve
- Example: *"You're Emerald and performing at Diamond level - keep climbing!"*

### 🏆 Champion Pool Analyzer
- **Champion Recommender**: Suggests which champions to prioritize or drop
- **Performance Flags**: Highlights strong picks (>55% WR) and weak picks (<45% WR)
- **Mastery Tracking**: Track progress toward mastery milestones

### 🎯 Challenge Tracker
- **Progress Tracking**: Monitor your progress on 300+ League challenges
- **Smart Recommendations**: Suggests which champion to play next to progress multiple challenges
- **In-Game Tips**: Actionable reminders for challenges like Soul Sweep, Invincible, Baron Power Play

### 📈 Win Condition Analysis
- **Stat Correlations**: Compare stats in wins vs losses
- **Performance Gaps**: Identifies which stats correlate most with your wins
- Example: *"Your wins correlate with: High KP (72% vs 48%), Low deaths (3.1 vs 6.8)"*

### 🎲 Tilt Detection
- **Losing Streaks**: Detects 3+ consecutive losses
- **Session Analysis**: Groups games into sessions and tracks performance
- **Time-of-Day**: Shows win rate by hour to find your best playing times

### 🖼️ Shareable Stat Cards
- **Social Media Ready**: Generate 1080x1080 PNG stat cards
- 6 card types: Overall Stats, Best Champion, Win Rate, Nuzlocke, Personal Records, Custom
- **RiftRetreat Branding**: Professional © watermark

### 🎮 Live Game Tools
- **Champion Select Detection**: Real-time detection when you're in champion select
- **Pre-Game Scouting**: Look up teammates and enemies
- **Game Plan Panel**: Shows relevant challenge tips for your selected champion

### 📉 Ranked Climb Tracker
- **LP History**: Track LP over time with visual graph
- **Session Tracking**: Auto-detect sessions and track net LP gains/losses
- **Tilt Detection**: Flags sessions with declining performance

---

## 🚀 Quick Start

### Prerequisites
- **Windows 10/11** (64-bit)
- Active League of Legends account

### Installation

1. **Download** the latest release from the [Releases page](https://github.com/GuusKooij/RiftRetreat/releases)
2. **Extract** the ZIP file to a folder of your choice
3. **Run** `RiftRetreat.exe`

### First-Time Setup

1. Launch RiftRetreat
2. Enter your **Riot ID** (e.g., `Retreat#EUW`)
3. Select your **region** (EUW, NA, KR, etc.)
4. Click **"Fetch Data"** to download your match history

> **Note:** The initial data fetch may take 2-5 minutes depending on your match history size.

---

## 🛠️ Usage

### Dashboard
View your overall performance stats, win conditions, role breakdown, duo partners, recent form, tilt analysis, and climb history.

### Champions
Analyze your champion pool, see recommendations for which champions to play or avoid, and track mastery progress.

### Challenges
Track challenge progress across 300+ League challenges and get smart recommendations for which champion to play next to progress multiple challenges simultaneously.

### Match History
Browse all your ranked matches with detailed stats, sortable columns, and filters by queue type, role, or champion.

### Settings
Update your Riot API key, refresh data to fetch new matches, view account info, and export match data to CSV.

---

## 📁 Installation Structure

After extracting the ZIP, you'll have:

```
RiftRetreat/
├── RiftRetreat.exe          # Main application (double-click to run)
├── _internal/               # Application dependencies (don't modify)
├── cache/                   # Champion/item icons (bundled)
└── data/                    # Your match data (created on first run)
```

All your personal data (matches, stats, settings) will be saved in the `data/` folder.

---

## 🔒 Privacy & Data

- **All data stays on your computer** - RiftRetreat does not upload your data anywhere
- **No account required** - Only uses your Riot API key for data fetching
- **Local storage** - All match data is saved in the `data/` folder on your computer
- **Open source** - You can review all code in this repository
- **No telemetry** - RiftRetreat doesn't track or collect any usage data

---

## 🛠️ Built With

- **Python 3.13**
- **PyQt6** - GUI framework
- **Riot Games API** - Match data and statistics
- **Data Dragon** - Champion/item assets

## 🐛 Known Issues

- **API Key Expiry**: Free development API keys expire every 24 hours and must be regenerated
- **Rate Limiting**: Large match history fetches may take several minutes due to API rate limits
- **Windows Only**: Currently only available for Windows (Mac/Linux support planned)

---

## 🤝 Contributing

Contributions are welcome! If you'd like to add features or fix bugs:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Running from Source

If you want to contribute or run from Python source:

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python app.py`

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

RiftRetreat is not endorsed by Riot Games and does not reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games and all associated properties are trademarks or registered trademarks of Riot Games, Inc.

## 💬 Support

If you encounter issues or have questions:
- Open an [Issue](https://github.com/GuusKooij/RiftRetreat/issues)
- Check existing issues for solutions

---

## 🙏 Acknowledgments

- Riot Games for providing the API
- Data Dragon for champion/item assets
- PyQt6 team for the excellent GUI framework

---

**Made with ❤️ for the League of Legends community**
