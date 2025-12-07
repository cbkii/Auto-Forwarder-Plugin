# Auto Fwd Plugin Fork

[![Version](https://img.shields.io/badge/version-1.9.9.9-blue.svg)](https://github.com/cbkii/Auto-Forwarder-Plugin/releases)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Original Author](https://img.shields.io/badge/original%20author-%40T3SL4-blue.svg)](https://t.me/T3SL4)
[![Fork Maintainer](https://img.shields.io/badge/fork%20by-%40cbkii-green.svg)](https://github.com/cbkii)

An advanced plugin for **exteraGram** that gives you total control over message forwarding. Automatically copy or forward messages from any chat to another with powerful filters, an integrated auto-updater, and a robust engine for reliable, ordered delivery.

> **This is a fork** of the [original Auto Forwarder Plugin](https://github.com/0x11DFE/Auto-Forwarder-Plugin) by @T3SL4. Version 1.9.9.9 builds upon the stable 1.9.0 release with additional features for batch processing and enhanced filtering capabilities.

> [!WARNING]
> ### 🔐 Disclaimer – Read Before Using
> > This plugin automates actions on your personal Telegram account, a practice often called "self-botting." It is provided for educational, testing, and personal automation purposes only. The author does not encourage any activity that violates Telegram’s Terms of Service.
> > - **Misuse can lead to account limitations or bans.** You are solely responsible for how you use this tool.
> > - By using this plugin, you agree to use it responsibly, ethically, and **entirely at your own risk.** The author assumes no liability for any consequences arising from its use.

---

### 📚 Table of Contents
* [What's New in v1.9.9.9](#-whats-new-in-v1999-fork)
* [Features](#-features)
* [Installation](#%EF%B8%8F-installation)
* [How to Use](#-how-to-use)
* [Configuration](#%EF%B8%8F-configuration)
* [Contributing](#-contributing)
* [Support the Developer](#%EF%B8%8F-support-the-developer)
* [License](#-license)

---

## 🆕 What's New in v1.9.9.9 (Fork)

This fork extends the original v1.9.0 release with powerful batch processing capabilities and enhanced filtering options:

> **📌 Note:** This is version **1.9.9.9** of the fork. The built-in auto-updater still points to the original repository and may show "v1.9.0" as the latest version. To stay updated with fork-specific features, bookmark this repository and check the [Releases](https://github.com/cbkii/Auto-Forwarder-Plugin/releases) page.

### New Features Added in This Fork:

* **📬 Batch Processing - Unread Messages:**
  * **Process Unread Messages:** Forward all unread messages from any chat with a single click via the chat menu.
  * **Global Batch Unread:** Process unread messages for ALL configured rules at once from the settings page.
  * **Smart Boundary Tracking:** Intelligently tracks both Telegram's read status AND the plugin's last processed message to avoid reprocessing.

* **📅 Batch Processing - Historical Messages:**
  * **Process Messages from Date:** Forward messages from the last X days (1-30) for any chat via the chat menu.
  * **Global Batch Historical:** Process historical messages for ALL configured rules at once from the settings page.
  * **Flexible Time Range:** Choose how far back to scan (minimum 1 day, maximum 30 days).

* **🌐 Global Keyword/Regex Filter:**
  * Set a **global keyword/regex pattern** in the main settings that can be applied across multiple rules.
  * Each rule can optionally enable "**use global regex**" to apply this global filter in addition to its local filter.
  * Perfect for maintaining consistent filtering criteria across multiple forwarding rules.

* **💾 Persistent Last-Seen Tracking:**
  * The plugin now tracks the last processed message ID for each chat to prevent reprocessing messages.
  * This ensures that when processing unread or historical messages, you won't get duplicates of messages that were already forwarded.

### Base Features from v1.9.0:
All features from the upstream v1.9.0 release are included, such as:
- Sequential Processing Engine for guaranteed message order
- "Set by Replying" for effortless destination setup
- Auto-updater with changelog display
- Advanced filtering (keywords, regex, author whitelisting)
- Album handling and anti-spam firewall

---

## 📸 Preview

![Plugin Preview](https://github.com/0x11DFE/Auto-Forwarder-Plugin/raw/refs/heads/main/auto_forwarder_preview.gif)


## ✨ Features

* **🚀 Reliable, Ordered Forwarding:**
    * **Sequential Processing Engine:** A completely new architecture that processes messages one-by-one in a dedicated queue. This resolves race conditions and **guarantees that messages are forwarded in the exact order they are received.**
    * **Configurable Speed vs. Order:** The new `Sequential Delay (Seconds)` setting gives you direct control over the trade-off. A small delay ensures order for large batches of files, while setting it to `0` restores high-speed parallel processing (which may result in messages being forwarded out of order).

* **Effortless Destination & Topic Setup:**
    * **Set by Replying:** The easiest way to set up a rule. Simply tap "Set by Replying" in the rule dialog, then go to your destination chat and reply to *any* message with the word `set`. The plugin handles the rest.
    * **Full Topic Support:** Automatically forward messages directly into a specific topic in a group or a comment thread in a channel. The "Set by Replying" feature makes this seamless.

* **Seamless Auto-Updater:**
    * Get notified directly in the app when a new version is available on GitHub Releases.
    * View the official changelog in a pop-up dialog before updating.
    * Update with a single click—no manual downloads or installs required.

* **Two Powerful Forwarding Modes:**
    * **Copy Mode:** Sends a brand new message, making it look like you sent it yourself. This mode enables perfect formatting preservation and automatically recreated reply quotes.
    * **Header Mode (Simulated Forward):** Copies the message and prepends a custom, clickable "Forwarded from..." header, linking to the original author and chat.

* **Advanced Filtering Engine:**
    * **Keyword & Regex:** Forward messages, media captions, or **documents with filenames** that contain specific keywords or match a regular expression.
    * **Global Regex Filter:** Set a global keyword/regex pattern in the settings that can be applied to multiple rules. Each rule can optionally enable "use global regex" in addition to its local filter.
    * **Granular Content Control:** The "Text" filter is now split into "Text Messages" and "Media Captions," allowing you to forward media while stripping its caption, and vice-versa.
    * **Author Whitelisting:** Filter messages based on the author type (Users, Bots, Outgoing), or provide a specific, comma-separated list of User IDs or `@usernames` to exclusively forward messages *only* from them.

* **Intelligent & Reliable Processing:**
    * **Ordered Album Handling:** Automatically waits to collect all photos/videos in a gallery before sending them together as a single, correctly ordered album.
    * **Duplicate Notification Prevention:** A thread-safe deduplication system prevents client-side notification glitches from causing the same message to be forwarded multiple times.
    * **Anti-Spam Firewall:** A built-in rate-limiter prevents a single user from flooding your destination chat with rapid messages.
    * **Persistent Last-Seen Tracking:** Tracks the last processed message for each chat to avoid reprocessing messages.

* **🆕 Batch Processing (Fork Feature):**
    * **Process Unread Messages:** Forward all unread messages from a chat with a single click (available in chat menu).
    * **Process Historical Messages:** Forward messages from the last X days (1-30) for any chat (available in chat menu).
    * **Global Batch Actions:** Process unread or historical messages for all configured rules at once from the settings page.
    * **Smart Tracking:** Persistent last-seen tracking prevents reprocessing of already-forwarded messages.

* **🆕 Global Filtering (Fork Feature):**
    * **Global Keyword/Regex Filter:** Set a global filter pattern in settings that can be applied to multiple rules.
    * **Per-Rule Toggle:** Each rule can independently enable "use global regex" to apply the global filter alongside its local filter.


## 🛠️ Installation

1.  Go to the [**Releases**](https://github.com/cbkii/Auto-Forwarder-Plugin/releases) page of this fork and download the latest `.py` file (v1.9.9.9 or newer).
2.  Using your device's file manager, **rename the file extension** from `.py` to `.plugin`. (Your file manager may warn you about changing the extension; accept the change.)
3.  Open Telegram and send the `.plugin` file to yourself (e.g., in your "Saved Messages").
4.  Tap on the file you just sent within the Telegram app.
5.  A confirmation dialog will appear. Tap **INSTALL PLUGIN** to finish.

> **⚠️ Important Note About Updates:** The auto-updater built into this plugin currently points to the original repository by @T3SL4. This means:
> - The "Check for Updates" button will check the original repository, not this fork
> - You may see update notifications for older versions (like v1.9.0) even though you're on v1.9.9.9
> - To get fork-specific updates, you'll need to manually download new versions from this fork's [Releases](https://github.com/cbkii/Auto-Forwarder-Plugin/releases) page
> - Future versions of this fork may redirect the auto-updater to check this fork's releases instead

## 📖 How to Use

This plugin is configured entirely through the Telegram user interface.

### Creating a Rule (The Easy Way)
1.  Go into the chat you want to forward messages **from**.
2.  Tap the three-dots menu (**⋮**) in the top-right corner and select **Auto Fwd...**.
3.  In the rule setup dialog, tap the **"Set by Replying"** button.
4.  A prompt will appear. Click **Proceed**.
5.  Navigate to your desired destination chat. This can be a user, group, channel, or even a specific **topic/comment thread**.
6.  **Reply** to any message in that destination with the exact word: `set`
7.  The plugin will instantly configure the rule and delete your `set` message. You're done!

### Creating a Rule (Manual Method)
1.  Go into the chat you want to forward messages **from**.
2.  Tap the three-dots menu (**⋮**) in the top-right corner and select **Auto Fwd...**.
3.  A dialog will appear. Manually enter the destination chat's ID, @username, or private `t.me/joinchat/...` link.
4.  Configure the other options, such as content filters, keyword matching, and specific author whitelists.
5.  Tap **Set** to save the rule.

### Editing or Deleting a Rule
1.  Go into a chat that already has an active forwarding rule.
2.  Open the **Auto Fwd...** menu item again.
3.  A management dialog will appear, allowing you to **Modify** or **Delete** the rule for that chat.

### 🆕 Processing Unread or Historical Messages (Fork Feature)
These batch processing features are exclusive to this fork (v1.9.9.9):

#### For a Single Chat:
1.  Go into a chat with an active forwarding rule.
2.  Tap the three-dots menu (**⋮**) in the top-right corner.
3.  Select **Process Unread Messages** to forward all unread messages since the last time the plugin processed them.
4.  Or select **Process Messages from Date** and enter a number (1-30) to forward messages from the last X days.

#### For All Configured Rules:
1.  Go to the plugin settings page: `Settings > exteraGram Settings > Plugins > Auto Forwarder`
2.  Use the **"Fwd Unread (All Rules)"** button to process unread messages for ALL configured rules at once.
3.  Or use the **"Fwd Last X Days (All Rules)"** button to process historical messages (you'll be prompted to enter the number of days).

> **Note:** The plugin tracks which messages have been processed to avoid duplicates. When you process unread messages, it will only forward messages that are newer than both Telegram's "read" marker and the plugin's internal tracking.

## ⚙️ Configuration

All global settings and a list of all active rules can be found by going to:
`Settings > exteraGram Settings > Plugins > Auto Forwarder`

### General Settings:
- **Album Buffering Timeout (ms):** How long to wait to collect all media in an album.
- **Sequential Delay (Seconds):** The pause between each message to guarantee order. Set to `0` to restore high-speed parallel mode (order not guaranteed).
- **Deduplication Window (Seconds):** Time window to ignore duplicate notifications from the client.
- **🆕 Global Keyword/Regex Filter (Fork Feature):** An optional filter that can be applied to multiple rules. Enable "use global regex" in each rule to apply this filter in addition to the rule's local filter.

### Global Batch Actions (Fork Features):
- **🆕 Fwd Unread (All Rules):** Processes unread messages for all configured rules at once.
- **🆕 Fwd Last X Days (All Rules):** Processes historical messages (1-30 days) for all configured rules at once.

### Other Actions:
- **Check for Updates:** Checks for new plugin versions on GitHub. ⚠️ **Note:** Currently checks the original repository by @T3SL4, not this fork. To get fork-specific updates (v1.9.9.9+), check the [Releases](https://github.com/cbkii/Auto-Forwarder-Plugin/releases) page manually.

### Per-Rule Settings:
When creating or editing a rule, you can configure:
- Destination chat/channel/topic
- Content type filters (text, photos, videos, documents, etc.)
- Keyword/regex filter (local to this rule)
- **🆕 Use Global Regex (Fork Feature):** Toggle to apply the global keyword filter in addition to the local filter
- Author filtering (users, bots, outgoing messages)
- Author whitelist (specific user IDs or @usernames)


## 🤝 Contributing

Contributions, issues, and feature requests are welcome! 

- For issues related to the **fork-specific features** (batch processing, global filters, last-seen tracking), please open an issue on this fork: [cbkii/Auto-Forwarder-Plugin/issues](https://github.com/cbkii/Auto-Forwarder-Plugin/issues)
- For issues related to the **base functionality**, consider reporting to the original repository: [0x11DFE/Auto-Forwarder-Plugin/issues](https://github.com/0x11DFE/Auto-Forwarder-Plugin/issues)

## ❤️ Support the Developers

If you find this plugin useful, please consider supporting its development:

### Original Author (@T3SL4)
The original plugin was created by @T3SL4. If you'd like to support the original author:
* **TON:** `UQDx2lC9bQW3A4LAfP4lSqtSftQSnLczt87Kn_CIcmJhLicm`
* **USDT (TRC20):** `TXLJNebRRAhwBRKtELMHJPNMtTZYHeoYBo`

### Fork Maintainer (@cbkii)
This fork is maintained by @cbkii. Consider giving a ⭐ on [GitHub](https://github.com/cbkii/Auto-Forwarder-Plugin) if you find the additional features useful!


## 📜 License

This project is licensed under the **GNU General Public License v3.0**. See the [LICENSE](https://www.gnu.org/licenses/gpl-3.0.html) for the full license text.

---

## 📋 Changelog

### v1.9.9.9 (Fork) - Batch Processing & Enhanced Filtering

This fork extends the original v1.9.0 release with the following enhancements:

**🆕 New Features:**
- **Batch Processing for Unread Messages:**
  - Added "Process Unread Messages" menu item for individual chats
  - Added "Fwd Unread (All Rules)" button in settings for global batch processing
  - Intelligent boundary tracking using both Telegram's read status and plugin's internal tracking
  
- **Batch Processing for Historical Messages:**
  - Added "Process Messages from Date" menu item to process messages from last X days (1-30)
  - Added "Fwd Last X Days (All Rules)" button in settings for global historical processing
  - Configurable time range with automatic clamping to valid values

- **Global Keyword/Regex Filter:**
  - New global filter setting that can be applied across multiple rules
  - Per-rule "use global regex" toggle to enable/disable global filter for each rule
  - Works in combination with local rule filters for maximum flexibility

- **Persistent Last-Seen Tracking:**
  - Plugin now tracks the last processed message ID for each chat
  - Prevents reprocessing of already-forwarded messages
  - Survives app restarts and plugin reloads

**🔧 Technical Improvements:**
- Added 28+ new functions to support batch processing and enhanced filtering
- Implemented `_load_last_seen_ids()` and `_save_last_seen_ids()` for persistent storage
- Added `_get_unread_boundary()` to intelligently determine which messages to process
- Implemented `_would_message_pass_filters()` for batch processing filter validation
- Enhanced keyword filtering with `_passes_combined_keyword_filter()` to support both local and global filters
- Added chat menu integration for easy access to batch processing features
- Increased codebase from ~1,816 lines to ~2,366 lines (+550 lines, +30%)

**📝 Metadata Changes:**
- Updated plugin name to "Auto Fwd Fork"
- Updated author to "@T3SL4,@cbkii"
- Updated version to "1.9.9.9"

### Base: v1.9.0 (Upstream) - The Sequential Engine & Stability Overhaul

All features from the original v1.9.0 release are included:
- Sequential Processing Engine for guaranteed message order
- Configurable Sequential Delay setting
- Fixed duplicate message issues
- Fixed album handling
- "Set by Replying" feature for easy destination setup
- Auto-updater with changelog display
- Advanced filtering (keywords, regex, author whitelisting)
- And all features from previous versions (v1.0.0 through v1.8.0)
