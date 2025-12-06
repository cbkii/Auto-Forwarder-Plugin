# Message Forwarder Plugin Fork

[![Version](https://img.shields.io/badge/version-1.9.9.9-blue.svg)](https://github.com/cbkii/Auto-Forwarder-Plugin/releases)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Telegram](https://img.shields.io/badge/author-%40T3SL4-blue.svg)](https://t.me/T3SL4)

An advanced plugin for exteraGram clients (11.9.1+) to automatically forward or copy messages from any chat to another, with powerful filters and customization.

> **Original Author:** [@T3SL4](https://t.me/T3SL4)  
> This fork maintains and extends the original functionality with additional features.

> **🔐 ⚠️ DISCLAIMER – READ BEFORE USING ⚠️**
> This plugin automates actions on your personal Telegram account, a practice often called "self-botting." This is provided for educational, testing, and personal automation purposes only.
>
> The author does not encourage or support any form of abuse or activity that violates [Telegram’s Terms of Service](https://telegram.org/tos).
> - Misuse of this plugin to automate actions in a way that mimics bot activity can result in account limitations or permanent bans. You are solely responsible for how you use this tool.
> - By using this plugin, you agree to use it responsibly, ethically, and entirely at your own risk. The author assumes no liability for any actions taken with or consequences arising from its use.

---

## 📸 Preview

![Plugin Preview](https://github.com/cbkii/Auto-Forwarder-Plugin/raw/refs/heads/main/auto_forwarder_preview.gif)


## ✨ Features

### Core Functionality
* **Two Forwarding Modes:**
    * **Copy Mode:** Sends a brand new message, making it look like you sent it yourself. Perfectly preserves all text formatting.
    * **Forward Mode:** Performs a standard Telegram forward with the "Forwarded from" header.
* **Forward from Anywhere:** Create rules for any chat, including private messages, groups, and channels.
* **Advanced Content Filtering:** For each rule, you can select exactly which types of content to forward (Text, Photos, Videos, Documents, Stickers, GIFs, Voice Messages, Video Messages, Audio Files).
* **Full Formatting Preservation:** In Copy Mode, all rich text formatting is kept intact, including **bold**, *italic*, `monospace`, ~~strikethrough~~, __underline__, ||spoilers||, and [hyperlinks](https://telegram.org).

### Intelligent Message Processing
* **Album Handling:** Automatically waits to collect all photos/videos in an album before sending them together.
* **Media Deferral:** Includes a safety net for large or slow-to-download media, ensuring files are forwarded reliably.
* **Reply Quotes:** Option to include quoted text from replied-to messages in your forwarded messages.
* **Sequential Processing:** Messages are processed in order with configurable delays to prevent rate limiting.
* **Deduplication:** Prevents duplicate message forwards within a configurable time window.

### Advanced Filtering & Customization
* **Author Filtering:** Specify exactly which users (by ID or @username) can trigger forwarding in each rule. Choose to forward messages from:
    * Regular users
    * Bots
    * Your own outgoing messages
* **Text-Based Filtering:**
    * **Global Blacklist:** Block messages containing specific words across all rules.
    * **Global Keyword Preset:** Set a regex pattern that messages must match (can be enabled per-rule).
    * **Per-Rule Regex Filter:** Add custom regex patterns for each individual rule.
    * **Text Replacement:** Transform message text using regex substitution (e.g., `s/old/new/`).
* **Message Length Limits:** Set minimum and maximum character counts for text messages.

### Batch Processing Tools
* **Process All Unread:** Retroactively forward all unread messages from all configured chats.
* **Process Historical Messages:** Forward messages from the last N days for all configured chats.
* **Batch Ignore Option:** Exclude specific rules from batch processing operations.
* **Queue Management:** Clear pending message queue when needed.

### Anti-Spam & Rate Limiting
* **Anti-Spam Firewall:** Built-in rate-limiter prevents a single user from flooding your destination chat with configurable delay.
* **Sequential Processing Delay:** Control the time between processing each message to avoid triggering Telegram's rate limits.

### User Experience
* **In-Chat Configuration:** Set up and manage rules directly from any chat's menu.
* **Destination Flexibility:** Set destinations by ID, @username, or by replying to a message in the target chat.
* **Visual Settings Page:** Comprehensive settings UI showing all active rules and global configurations.


## ⚙️ Installation

**Requirements:**
- exteraGram version **11.9.1** or higher
- Python 3.11+ support via Chaquopy

**Steps:**
1.  Go to the [**Releases**](https://github.com/cbkii/Auto-Forwarder-Plugin/releases) page and download the latest `.py` file.
2.  Using your device's file manager, **rename the file extension** from `.py` to `.plugin`.
3.  Send the `.plugin` file to yourself in Telegram (e.g., in your "Saved Messages").
4.  Tap on the file you just sent. The client will show a confirmation dialog.
5.  Tap **INSTALL PLUGIN** to finish.

## 🚀 How to Use

This plugin is configured entirely through the Telegram user interface.

### Creating a Rule

1.  Go into the chat you want to forward messages **from**.
2.  Tap the three-dots menu (⋮) in the top-right corner.
3.  Select **Auto Forward...** from the menu.
4.  A dialog will appear with comprehensive options:
    * **Destination:** Enter the chat ID, @username, or use "Set Destination by Replying" to reply to any message in your target chat with "set"
    * **Remove Original Author:** Check to enable Copy Mode (unchecked = Forward Mode)
    * **Quote Replies:** Include quoted text from replied-to messages
    * **Forward messages from:** Choose which message types to forward (Users, Bots, Outgoing Messages)
    * **Content to forward:** Select which media types to forward (Text, Photos, Videos, Documents, Audio, Voice, Video Messages, Stickers, GIFs)
    * **Advanced Filtering:**
        * **Author Filter:** Comma-separated list of user IDs or @usernames to filter by
        * **Text Replacement:** Regex substitution pattern (e.g., `s/pattern/replacement/`)
        * **Use Global Keyword Preset:** Enable global regex filtering for this rule
        * **Exclude from Global Batch Tools:** Prevent this rule from being processed during batch operations
5.  Tap **Set** to save the rule.

### Editing or Deleting a Rule

1.  Go into a chat that already has an active forwarding rule.
2.  Open the **Auto Forward...** menu item again.
3.  A management dialog will appear, allowing you to **Modify** or **Delete** the rule for that chat.

You can also see and manage all your active rules from the main plugin settings page.

## 🔧 Configuration

All global settings and active rules can be managed from:  
`Settings > exteraGram Settings > Plugins > Auto Forwarder`

### General Settings
* **Minimum Message Length:** Filter text messages by minimum character count (default: 1)
* **Maximum Message Length:** Filter text messages by maximum character count (default: 4096)
* **Media Deferral Timeout:** Time to wait for media files to download before forwarding (default: 5000ms). Increase if large files fail to forward.
* **Album Buffering Timeout:** Time to wait for all media in an album before sending together (default: 800ms)
* **Deduplication Window:** Time window to ignore duplicate message events (default: 10 seconds)
* **Anti-Spam Delay:** Minimum time between forwards from the same user (default: 1 second). Set to 0 to disable.
* **Sequential Processing Delay:** Delay between processing each message in the queue (default: 1.5 seconds)

### Global Presets
* **Global Keyword Preset:** A regex pattern that messages must match when this option is enabled in individual rules. Useful for setting up keyword-based filtering across multiple rules.
* **Global Blacklist Words:** Comma-separated list of words or phrases. Any message containing these will be blocked from forwarding across all rules.

### Queue Control
* **Clear Pending Queue:** Remove all messages waiting to be processed
* **Process All Unread:** Retroactively process all unread messages from all configured chats (excluding rules with "Batch Ignore" enabled)
* **Process All History:** Process messages from the last N days for all configured chats (you'll be prompted for the number of days)

### Active Forwarding Rules
View, edit, or delete all configured forwarding rules. Each rule shows:
* Source chat name
* Destination chat name
* Mode (Copy or Forward)


## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/cbkii/Auto-Forwarder-Plugin/issues).

## ❤️ Support the Developer

If you find this plugin useful, please consider supporting its development. Thank you!

* **TON:** `UQDx2lC9bQW3A4LAfP4lSqtSftQSnLczt87Kn_CIcmJhLicm`
* **USDT (TRC20):** `TXLJNebRRAhwBRKtELMHJPNMtTZYHeoYBo`


## 📜 License

This project is licensed under the **GNU General Public License v3.0**. See the [LICENSE](https://www.gnu.org/licenses/gpl-3.0.html) file for the full license text.
