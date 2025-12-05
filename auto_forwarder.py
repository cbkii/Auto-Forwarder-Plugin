# ----------------------------------------------------------------------------------
# Message Forwarder Plugin for exteraGram
# Copyright (C) 2025 @T3SL4
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# ----------------------------------------------------------------------------------
#
# DISCLAIMER:
# This plugin automates actions on a user's personal Telegram account ("self-botting").
# It is intended for educational and personal automation purposes only. Misuse may
# violate Telegram's Terms of Service and can lead to account limitations or bans.
# The author assumes no liability for any consequences arising from its use.
# USE ENTIRELY AT YOUR OWN RISK.
#
# ----------------------------------------------------------------------------------
#
# EXTERAGRAM PLUGIN COMPLIANCE NOTES:
# This plugin follows exteraGram best practices (https://plugins.exteragram.app/):
# - Uses run_on_queue() from client_utils for one-off background tasks (batch operations)
# - Uses daemon thread for persistent queue processor (worker loop)
# - Separates UI updates via run_on_ui_thread()
# - Validates context and handles errors gracefully
# - Compatible with exteraGram 11.9.1+ and Python 3.11 via Chaquopy
#
# ----------------------------------------------------------------------------------

# --- Standard Library Imports ---
import json
import traceback
import random
import collections
import time
import re
import queue
import threading
import unicodedata
import datetime

# --- Chaquopy Import for Java Interoperability ---
from java.chaquopy import dynamic_proxy

# --- Base Plugin and UI Imports ---
from base_plugin import BasePlugin, MenuItemData, MenuItemType
from ui.settings import Header, Text, Divider, Input
from ui.alert import AlertDialogBuilder
from ui.bulletin import BulletinHelper

# --- Android & Chaquopy Imports ---
from android_utils import log, run_on_ui_thread
from android.widget import EditText, FrameLayout, CheckBox, LinearLayout, TextView, Toast, ScrollView
from android.text import InputType, Html
from android.text.method import LinkMovementMethod
from android.util import TypedValue
from android.view import View, ViewGroup
from java.util import ArrayList, HashSet
from android.content.res import ColorStateList
from android.content import ClipData, ClipboardManager, Context
from android.os import Handler, Looper
from java.lang import Runnable, String as JavaString
from android.content import Intent
from android.net import Uri
from android.graphics import Typeface

# --- Telegram & Client Utilities ---
from org.telegram.messenger import NotificationCenter, MessageObject
from org.telegram.tgnet import TLRPC
from org.telegram.ui.ActionBar import Theme
from com.exteragram.messenger.plugins.ui import PluginSettingsActivity
from client_utils import (
    get_messages_controller,
    get_last_fragment,
    get_account_instance,
    send_request,
    RequestCallback,
    get_user_config,
    run_on_queue
)

# --- Plugin Metadata ---
__id__ = "auto_forwarder_fork"
__name__ = "Auto Fwd Fork"
__description__ = "Sets up forwarding rules for any chat, including users, groups, and channels."
__author__ = "@T3SL4"
__version__ = "1.6.6.6"
__min_version__ = "11.9.1"
__icon__ = "Putin_1337/14"

# --- Constants & Default Settings ---
FORWARDING_RULES_KEY = "forwarding_rules_v1337"
DEFAULT_SETTINGS = {
    "deferral_timeout_ms": 5000,
    "min_msg_length": 1,
    "max_msg_length": 4096,
    "deduplication_window_seconds": 10.0,
    "album_timeout_ms": 800,
    "antispam_delay_seconds": 1.0,
    "sequential_delay_seconds": 1.5
}
FILTER_TYPES = {
    "text": "Text Messages",
    "photos": "Photos",
    "videos": "Videos",
    "documents": "Files / Documents",
    "audio": "Audio Files",
    "voice": "Voice Messages",
    "video_messages": "Video Messages (Roundies)",
    "stickers": "Stickers",
    "gifs": "GIFs & Animations"
}
FAQ_TEXT = """
--- **Disclaimer and Responsible Usage** ---
Please be aware that using a plugin like this automates actions on your personal Telegram account. This practice is often referred to as 'self-botting'.
This kind of automation may be considered a violation of [Telegram's Terms of Service](https://telegram.org/tos), which can prohibit bot-like activity from user accounts.
Using this plugin carries potential risks, including account limitations or bans. You accept full responsibility for your actions. The author is not responsible for any consequences from your use or misuse of this tool.
**Use at your own risk.**
--- **FAQ** ---
**🚀 Core Functionality**
* **How do I create a rule?**
Go into any chat you want to forward messages *from*. Tap the three-dots menu (⋮) in the top right and select "Auto Forward...". A dialog will then ask for the destination chat.
* **How do I edit or delete a rule?**
Go to a chat where a rule is active and open the "Auto Forward..." menu item again. A "Manage Rule" dialog will appear, allowing you to modify or delete it. You can also manage all rules from the main plugin settings page.
* **What's the difference between "Copy" and "Forward" mode?**
When setting up a rule, you have a checkbox for "Remove Original Author".
- **Checked (Copy Mode):** Sends a brand new message to the destination. It looks like you sent it yourself. All text formatting is preserved.
- **Unchecked (Forward Mode):** Performs a standard Telegram forward, including the "Forwarded from..." header, preserving the original author's context.
* **Can I control which messages get forwarded?**
Yes. When creating or modifying a rule, you can choose to forward messages from regular users, bots, and your own outgoing messages independently.
--- **✨ Advanced Features & Formatting** ---
* **How does the Anti-Spam Firewall work?**
It's a rate-limiter that prevents a single user from flooding your destination chat. It works by enforcing a minimum time delay between forwards *from the same person*. You can configure this delay in the General Settings.
* **How do the content filters work?**
When creating or modifying a rule, you'll see checkboxes for different message types (Text, Photos, Videos, etc.). Simply uncheck any content type you *don't* want to be forwarded for that specific rule. For example, you can set up a rule to forward only photos and videos from a channel, ignoring all text messages.
* **Does the plugin support text formatting (Markdown)?**
Yes, completely. In 'Copy' mode, the plugin perfectly preserves all text formatting from the original message. This includes:
- **Bold** and *italic* text
- `Monospace code`
- ~~Strikethrough~~ and __underline__
- ||Spoilers||
- [Custom Hyperlinks](https://telegram.org)
- Mentions and #hashtags
--- **⚙️ Technical Settings & Troubleshooting** ---
* **What do the General Settings mean?**
- **Min/Max Message Length:** Filters *text messages* based on their character count.
- **Media Deferral Timeout:** A safety net for media files. When a file arrives, your app might need a moment to get the data required for forwarding. This is how long the plugin waits. Increase this value if large files you receive sometimes fail to forward.
- **Album Buffering Timeout:** When a gallery of photos/videos is sent, the plugin waits a brief moment to collect all the images before forwarding them together as a single album. This controls that waiting period.
- **Deduplication Window:** Prevents double-forwards. If Telegram sends a duplicate notification for the same message within this time window (in seconds), the plugin will ignore it.
- **Anti-Spam Delay:** The core setting for the firewall, as explained above. Set to `0` to disable it.
* **Why do large files I send myself sometimes fail to forward?**
This is a known limitation. If your file takes longer to upload than the "Media Deferral Timeout", the plugin may not be able to forward it. The feature is most reliable for forwarding messages you receive or for your own small files that upload instantly.
"""

class DeferredTask(dynamic_proxy(Runnable)):
    """A robust Runnable class to handle the timeout for deferred messages."""
    def __init__(self, plugin, event_key):
        super().__init__()
        self.plugin = plugin
        self.event_key = event_key

    def run(self):
        """This method is called by the Android Handler after the timeout to re-process a message."""
        self.plugin._process_timed_out_message(self.event_key)


class AlbumTask(dynamic_proxy(Runnable)):
    """A Runnable class to handle the timeout for album processing."""
    def __init__(self, plugin, grouped_id):
        super().__init__()
        self.plugin = plugin
        self.grouped_id = grouped_id

    def run(self):
        """This method is called by the Android Handler after the album timeout to process the buffered album."""
        self.plugin._process_album(self.grouped_id)


class AutoForwarderPlugin(dynamic_proxy(NotificationCenter.NotificationCenterDelegate), BasePlugin):
    """
    The main class for the Auto Forwarder plugin. It handles forwarding rules,
    listens for new messages, and manages the complex logic for forwarding
    different types of content correctly.
    """
    TON_ADDRESS = "UQDx2lC9bQW3A4LAfP4lSqtSftQSnLczt87Kn_CIcmJhLicm"
    USDT_ADDRESS = "TXLJNebRRAhwBRKtELMHJPNMtTZYHeoYBo"
    USER_TIMESTAMP_CACHE_SIZE = 500

    def __init__(self):
        super().__init__()
        self.id = __id__
        self.forwarding_rules = {}
        self.error_message = None
        self.deferred_messages = {}
        self.album_buffer = {}
        self.processed_keys = collections.deque(maxlen=200)
        self.handler = Handler(Looper.getMainLooper())
        self.user_last_message_time = collections.OrderedDict()
        self.processing_queue = queue.Queue()
        self.stop_worker_thread = threading.Event()
        self.is_listening_for_reply = False
        self.reply_context = {}
        self._load_configurable_settings()

    def on_plugin_load(self):
        """Called when the plugin is loaded. Registers the new message observer."""
        log(f"[{self.id}] Loading version {__version__}...")
        self._load_configurable_settings()
        self._load_forwarding_rules()
        self._add_chat_menu_item()
        account_instance = get_account_instance()
        if account_instance:
            account_instance.getNotificationCenter().addObserver(self, NotificationCenter.didReceiveNewMessages)
        
        # Start persistent worker thread for sequential message processing
        # Note: Using a dedicated daemon thread here instead of run_on_queue because
        # we need a long-lived, persistent queue processor that runs continuously
        # throughout the plugin's lifecycle. This aligns with exteraGram best practices
        # for daemon threads handling supporting background operations.
        worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        worker_thread.start()
        log(f"[{self.id}] Worker thread started.")

    def on_plugin_unload(self):
        """Called when the plugin is unloaded. Removes the observer and cancels any pending tasks."""
        account_instance = get_account_instance()
        if account_instance:
            account_instance.getNotificationCenter().removeObserver(self, NotificationCenter.didReceiveNewMessages)
        self.handler.removeCallbacksAndMessages(None)
        self.stop_worker_thread.set()
        log(f"[{self.id}] Worker thread stop signal sent.")

    def _load_configurable_settings(self):
        """Loads all configurable settings from storage into instance attributes."""
        log(f"[{self.id}] Reloading configurable settings into memory.")
        self.min_msg_length = int(self.get_setting("min_msg_length", str(DEFAULT_SETTINGS["min_msg_length"])))
        self.max_msg_length = int(self.get_setting("max_msg_length", str(DEFAULT_SETTINGS["max_msg_length"])))
        self.deferral_timeout_ms = int(self.get_setting("deferral_timeout_ms", str(DEFAULT_SETTINGS["deferral_timeout_ms"])))
        self.album_timeout_ms = int(self.get_setting("album_timeout_ms", str(DEFAULT_SETTINGS["album_timeout_ms"])))
        self.deduplication_window_seconds = float(self.get_setting("deduplication_window_seconds", str(DEFAULT_SETTINGS["deduplication_window_seconds"])))
        self.antispam_delay_seconds = float(self.get_setting("antispam_delay_seconds", str(DEFAULT_SETTINGS["antispam_delay_seconds"])))
        self.sequential_delay_seconds = float(self.get_setting("sequential_delay_seconds", str(DEFAULT_SETTINGS["sequential_delay_seconds"])))
        self.global_keyword_preset = self.get_setting("global_keyword_preset", "")
        self.global_blacklist_words = self.get_setting("global_blacklist_words", "")

    def _worker_loop(self):
        """Worker thread loop that processes items from the queue sequentially."""
        log(f"[{self.id}] Worker loop started.")
        try:
            while not self.stop_worker_thread.is_set():
                try:
                    item = self.processing_queue.get(timeout=1.0)
                    
                    if isinstance(item, tuple) and len(item) == 2 and item[0] == "album":
                        grouped_id = item[1]
                        log(f"[{self.id}] Worker processing album: {grouped_id}")
                        self._process_album(grouped_id)
                    else:
                        # It's a message object
                        log(f"[{self.id}] Worker processing message.")
                        self.super_handle_message_event(item)
                    
                    # Sleep after processing to enforce sequential delay
                    time.sleep(self.sequential_delay_seconds)
                    
                except queue.Empty:
                    continue
                except (OSError, ValueError) as e:
                    log(f"[{self.id}] Queue operation error in worker loop: {e}")
                    continue
                except Exception as e:
                    log(f"[{self.id}] ERROR processing item in worker loop: {traceback.format_exc()}")
                    # Continue processing despite errors
                    continue
        finally:
            log(f"[{self.id}] Worker loop stopped.")

    def _create_message_object_safely(self, message):
        """Safely creates a MessageObject from a TLRPC message."""
        try:
            # Try standard constructor with full layout generation and media existence check
            return MessageObject(get_user_config().getCurrentAccount(), message, True, True)
        except (TypeError, AttributeError):
            # Fallback if upstream signature changes: skip layout generation and media check
            try:
                return MessageObject(get_user_config().getCurrentAccount(), message, False, False)
            except (TypeError, AttributeError):
                return None

    def _is_media_complete(self, message):
        """Checks if a media message has a file_reference, which is needed for forwarding."""
        if not message or not hasattr(message, 'media') or not message.media:
            return True
        if hasattr(message.media, 'photo') and getattr(message.media.photo, 'file_reference', None):
            return True
        if hasattr(message.media, 'document') and getattr(message.media.document, 'file_reference', None):
            return True
        return False

    def didReceivedNotification(self, id, account, args):
        """The main entry point, called by Telegram for every new message event."""
        if id != NotificationCenter.didReceiveNewMessages:
            return
        try:
            if not self.forwarding_rules:
                return
            messages_list = args[1]
            for i in range(messages_list.size()):
                message_object = messages_list.get(i)
                if not (hasattr(message_object, 'messageOwner') and message_object.messageOwner):
                    continue
                self.handle_message_event(message_object)
        except Exception:
            log(f"[{self.id}] ERROR in notification handler: {traceback.format_exc()}")

    def _get_author_type(self, message):
        """Determines if the message is from a user, a bot, or is outgoing."""
        if message.out:
            return "outgoing"
        
        author_entity = self._get_chat_entity(self._get_id_from_peer(message.from_id))
        if author_entity and getattr(author_entity, 'bot', False):
            return "bot"
        
        return "user"

    def handle_message_event(self, message_object):
        """Event triage - checks if rule exists and queues messages for processing."""
        message = message_object.messageOwner
        source_chat_id = self._get_id_from_peer(message.peer_id)
        
        # Check if listening for reply to set destination
        if self.is_listening_for_reply:
            message_text = (message.message or "").strip().lower()
            if message_text == "set":
                dest_chat_id = source_chat_id
                context = self.reply_context
                if context and 'source_id' in context:
                    log(f"[{self.id}] Setting destination by reply: {dest_chat_id}")
                    self.is_listening_for_reply = False
                    dest_name = self._get_chat_name(dest_chat_id)
                    
                    # Update the input field if available
                    if 'input_field' in context and context['input_field']:
                        try:
                            input_field = context['input_field']
                            run_on_ui_thread(lambda: input_field.setText(str(dest_chat_id)))
                        except Exception as e:
                            log(f"[{self.id}] Error updating input field: {e}")
                    
                    run_on_ui_thread(lambda: BulletinHelper.show_success(f"Destination set to {dest_name}"))
                return
        
        rule = self.forwarding_rules.get(source_chat_id)
        if not rule or not rule.get("enabled", False):
            return

        grouped_id = getattr(message, 'grouped_id', 0)
        if grouped_id != 0:
            # Buffer album messages
            if grouped_id not in self.album_buffer:
                log(f"[{self.id}] Detected start of new album: {grouped_id}")
                album_task = AlbumTask(self, grouped_id)
                self.album_buffer[grouped_id] = {'messages': [], 'task': album_task}
                self.handler.postDelayed(album_task, self.album_timeout_ms)
            self.album_buffer[grouped_id]['messages'].append(message_object)
            return
        
        # Queue single message for processing
        self.processing_queue.put(message_object)

    def super_handle_message_event(self, message_object):
        """Main processing pipeline for each incoming message (called by worker)."""
        message = message_object.messageOwner
        source_chat_id = self._get_id_from_peer(message.peer_id)
        rule = self.forwarding_rules.get(source_chat_id)
        if not rule or not rule.get("enabled", False):
            return

        # Check author filter if present
        author_filter = rule.get("author_filter", "")
        if author_filter:
            author_id = self._get_id_from_peer(message.from_id)
            author_entity = self._get_chat_entity(author_id)
            author_username = getattr(author_entity, 'username', '') if author_entity else ''
            
            allowed_authors = [a.strip() for a in author_filter.split(',') if a.strip()]
            author_match = False
            for allowed in allowed_authors:
                if allowed.startswith('@'):
                    if author_username and author_username.lower() == allowed[1:].lower():
                        author_match = True
                        break
                else:
                    try:
                        if int(allowed) == author_id:
                            author_match = True
                            break
                    except ValueError:
                        pass
            
            if not author_match:
                log(f"[{self.id}] Message filtered out by author filter.")
                return

        author_type = self._get_author_type(message)
        if author_type == "outgoing" and not rule.get("forward_outgoing", True):
            return
        if author_type == "user" and not rule.get("forward_users", True):
            return
        if author_type == "bot" and not rule.get("forward_bots", True):
            return

        if self.antispam_delay_seconds > 0:
            author_id = get_user_config().getClientUserId() if message.out else self._get_id_from_peer(message.from_id)
            if author_id:
                current_time = time.time()
                last_time = self.user_last_message_time.get(author_id)
                if last_time and (current_time - last_time) < self.antispam_delay_seconds:
                    log(f"[{self.id}] Dropping message from user {author_id} due to anti-spam rate limit.")
                    return
                self.user_last_message_time[author_id] = current_time
                if len(self.user_last_message_time) > self.USER_TIMESTAMP_CACHE_SIZE:
                    self.user_last_message_time.popitem(last=False)

        event_key = None
        if message.out:
            event_key = ("outgoing", message.dialog_id, message.date, message.message or "")
        else:
            author_id = self._get_id_from_peer(message.from_id)
            event_key = ("incoming", author_id, source_chat_id, message.id)

        if any(key == event_key for key, ts in self.processed_keys):
            return

        is_media = hasattr(message, 'media') and message.media and not isinstance(message.media, TLRPC.TL_messageMediaEmpty)
        is_incomplete_media = is_media and not self._is_media_complete(message)
        is_reply = hasattr(message, 'reply_to') and message.reply_to is not None
        is_reply_object_missing = is_reply and not (hasattr(message_object, 'replyMessageObject') and message_object.replyMessageObject)
        if is_incomplete_media or is_reply_object_missing:
            if event_key not in self.deferred_messages:
                reason = "incomplete media" if is_incomplete_media else "missing reply object"
                log(f"[{self.id}] Deferring message due to {reason}. Key: {event_key}")
                deferred_task = DeferredTask(self, event_key)
                self.deferred_messages[event_key] = (message_object, deferred_task)
                self.handler.postDelayed(deferred_task, self.deferral_timeout_ms)
            return

        if event_key in self.deferred_messages:
            _, deferred_task = self.deferred_messages[event_key]
            self.handler.removeCallbacks(deferred_task)
            del self.deferred_messages[event_key]
        
        self._process_and_send(message_object, event_key)

    def _process_timed_out_message(self, event_key):
        """Processes a deferred message, re-fetching it from cache to ensure data is fresh."""
        if event_key in self.deferred_messages:
            log(f"[{self.id}] Processing deferred message after timeout. Key: {event_key}")
            message_object, _ = self.deferred_messages[event_key]
            final_message_object = message_object
            try:
                original_message = message_object.messageOwner
                if not original_message.out and hasattr(get_messages_controller(), 'getMessage'):
                    cached_message_obj = get_messages_controller().getMessage(original_message.dialog_id, original_message.id)
                    if cached_message_obj:
                        final_message_object = cached_message_obj
                        log(f"[{self.id}] Successfully re-fetched message from cache.")
            except Exception as e:
                log(f"[{self.id}] Could not re-fetch message from cache, proceeding with original object. Error: {e}")
            self._process_and_send(final_message_object, event_key)
            del self.deferred_messages[event_key]

    def _process_album(self, grouped_id):
        """Processes a buffered album after the timeout."""
        log(f"[{self.id}] Processing album {grouped_id} after timeout.")
        album_data = self.album_buffer.pop(grouped_id, None)
        if not album_data or not album_data['messages']:
            return
        
        first_message_obj = album_data['messages'][0]
        first_message = first_message_obj.messageOwner
        source_chat_id = self._get_id_from_peer(first_message.peer_id)
        rule = self.forwarding_rules.get(source_chat_id)
        if not rule:
            return

        album_key = (self._get_id_from_peer(first_message.from_id), source_chat_id, grouped_id)
        current_time = time.time()
        while self.processed_keys and current_time - self.processed_keys[0][1] > self.deduplication_window_seconds:
            self.processed_keys.popleft()
        if any(key == album_key for key, ts in self.processed_keys):
            return
        self.processed_keys.append((album_key, time.time()))
        self._send_album(album_data['messages'], rule)

    def _normalize_message_text(self, text):
        """Normalizes message text using Unicode normalization."""
        if not text:
            return ""
        return unicodedata.normalize("NFKC", text)

    def _get_unread_boundary(self, chat_id):
        """Retrieves the maximum of the Telegram-tracked read ID and plugin's internal last_seen_inbox_id."""
        try:
            # Get Telegram's read position
            dialog = get_messages_controller().getDialog(chat_id)
            telegram_read_id = getattr(dialog, 'read_inbox_max_id', 0) if dialog else 0
            
            # Get plugin's internal tracking
            internal_tracking_key = f"last_seen_{chat_id}"
            internal_read_id = int(self.get_setting(internal_tracking_key, "0"))
            
            return max(telegram_read_id, internal_read_id)
        except Exception as e:
            log(f"[{self.id}] Error getting unread boundary: {e}")
            return 0

    def _update_last_seen_id(self, chat_id, message_id):
        """Updates the internal storage for the chat's last processed ID."""
        try:
            internal_tracking_key = f"last_seen_{chat_id}"
            current_max = int(self.get_setting(internal_tracking_key, "0"))
            if message_id > current_max:
                self.set_setting(internal_tracking_key, str(message_id))
                log(f"[{self.id}] Updated last_seen_id for chat {chat_id} to {message_id}")
        except Exception as e:
            log(f"[{self.id}] Error updating last_seen_id: {e}")

    def _check_message_text_criteria(self, message_text, rule):
        """Checks if message passes text-based filters including blacklist and keyword matching."""
        if not message_text:
            return True
        
        normalized_text = self._normalize_message_text(message_text)
        
        # Check global blacklist
        if self.global_blacklist_words:
            blacklist_items = [word.strip().lower() for word in self.global_blacklist_words.split(',') if word.strip()]
            for blacklist_word in blacklist_items:
                if blacklist_word in normalized_text.lower():
                    log(f"[{self.id}] Message blocked by global blacklist word: {blacklist_word}")
                    return False
        
        # Check text filters: local regex and/or global keyword preset
        local_regex = rule.get("text_filter_regex", "")
        use_global_keywords = rule.get("use_global_keywords", False)
        
        # Evaluate local regex match if regex exists
        regex_match = False
        if local_regex:
            try:
                regex_match = bool(re.search(local_regex, normalized_text))
            except Exception as e:
                log(f"[{self.id}] Regex error: {e}")
        
        # Evaluate global keyword (regex) match if enabled and preset exists
        keyword_match = False
        if use_global_keywords and self.global_keyword_preset:
            try:
                # Treat global keyword preset as regex pattern, same as local regex
                keyword_match = bool(re.search(self.global_keyword_preset, normalized_text))
            except Exception as e:
                log(f"[{self.id}] Global keyword regex error: {e}")
        
        # Apply filtering logic based on configuration
        if use_global_keywords and self.global_keyword_preset:
            # When global keywords enabled: require (keyword match OR regex match)
            if not (keyword_match or regex_match):
                log(f"[{self.id}] Message did not match global keyword or local regex.")
                return False
        elif local_regex:
            # When no global keywords: rely solely on local regex if present
            if not regex_match:
                log(f"[{self.id}] Message did not match local regex filter.")
                return False
        
        return True

    def _apply_text_replacement(self, text, rule):
        """Applies text replacement regex to message text."""
        replacement_pattern = rule.get("text_replacement", "")
        if not replacement_pattern or not text:
            return text
        
        try:
            # Parse s/pattern/replacement/ format
            # Use a more robust approach: find first unescaped '/' after 's/'
            # then find the second unescaped '/' to properly handle slashes in replacement
            if replacement_pattern.startswith('s/'):
                parts = replacement_pattern[2:]  # Remove 's/'
                
                # Find the delimiter between pattern and replacement
                # Look for the first '/' that isn't escaped
                pattern_end = -1
                i = 0
                while i < len(parts):
                    if parts[i] == '/' and (i == 0 or parts[i-1] != '\\'):
                        pattern_end = i
                        break
                    i += 1
                
                if pattern_end > 0 and pattern_end < len(parts) - 1:
                    pattern = parts[:pattern_end]
                    remainder = parts[pattern_end + 1:]
                    
                    # Find the closing '/'
                    replacement_end = -1
                    i = 0
                    while i < len(remainder):
                        if remainder[i] == '/' and (i == 0 or remainder[i-1] != '\\'):
                            replacement_end = i
                            break
                        i += 1
                    
                    if replacement_end >= 0:
                        replacement = remainder[:replacement_end]
                        return re.sub(pattern, replacement, text)
        except Exception as e:
            log(f"[{self.id}] Text replacement error: {e}")
        
        return text

    def _is_message_allowed_by_filters(self, message_object, rule):
        """Checks if a message should be forwarded based on the rule's media filters."""
        filters = rule.get("filters", {})
        if not filters:
            return True
        if message_object.isPhoto(): return filters.get("photos", True)
        if message_object.isSticker(): return filters.get("stickers", True)
        if message_object.isVoice(): return filters.get("voice", True)
        if message_object.isRoundVideo(): return filters.get("video_messages", True)
        if message_object.isGif(): return filters.get("gifs", True)
        if message_object.isMusic(): return filters.get("audio", True)
        if message_object.isVideo(): return filters.get("videos", True)
        if message_object.isDocument(): return filters.get("documents", True)
        return filters.get("text", True)

    def _process_and_send(self, message_object, event_key):
        """Final processing stage that applies all filters and sends the message."""
        current_time = time.time()
        while self.processed_keys and current_time - self.processed_keys[0][1] > self.deduplication_window_seconds:
            self.processed_keys.popleft()
        if any(key == event_key for key, ts in self.processed_keys):
            return
        
        message = message_object.messageOwner
        source_chat_id = self._get_id_from_peer(message.peer_id)
        rule = self.forwarding_rules.get(source_chat_id)
        if not rule:
            return

        if not self._is_message_allowed_by_filters(message_object, rule):
            return

        is_text_based = not message.media or isinstance(message.media, (TLRPC.TL_messageMediaEmpty, TLRPC.TL_messageMediaWebPage))
        if is_text_based:
            if not (self.min_msg_length <= len(message.message or "") <= self.max_msg_length):
                return
            
            # Check text-based criteria (blacklist, keywords)
            if not self._check_message_text_criteria(message.message, rule):
                return

        self.processed_keys.append((event_key, time.time()))
        self._send_forwarded_message(message_object, rule)
        
        # Update last seen ID after successful forward
        self._update_last_seen_id(source_chat_id, message.id)
    
    def _get_java_len(self, py_string: str) -> int:
        """
        Calculates the length of a Python string using Java's UTF-16 length method.
        This is crucial for creating accurate entities for text containing emojis.
        """
        if not py_string:
            return 0
        return JavaString(py_string).length()

    def _add_user_entities(self, entities: ArrayList, text: str, user_entity: TLRPC.TL_user, display_name: str):
        """
        A helper method to add both Bold and TextUrl entities for a given user.
        This creates a clickable, bold, colored link for a user's name.
        """
        if not all([entities is not None, text, user_entity, display_name]):
            return
        
        try:
            offset = text.rfind(display_name)
            if offset == -1:
                return

            length = self._get_java_len(display_name)
            
            url_entity = TLRPC.TL_messageEntityTextUrl()
            url_entity.url = f"tg://user?id={user_entity.id}"
            url_entity.offset = offset
            url_entity.length = length
            entities.add(url_entity)

            bold_entity = TLRPC.TL_messageEntityBold()
            bold_entity.offset = offset
            bold_entity.length = length
            entities.add(bold_entity)
        except Exception as e:
            log(f"[{self.id}] Failed to add user entities for {display_name}: {e}")

    def _build_reply_quote(self, message_object):
        """
        Builds a native-style visual quote block for a replied-to message.
        This function constructs the text and formatting entities needed to mimic
        Telegram's reply quoting UI, handling emojis, code blocks, and other
        edge cases.
        """
        replied_message_obj = message_object.replyMessageObject
        if not replied_message_obj or not replied_message_obj.messageOwner:
            return None, None
        
        replied_message = replied_message_obj.messageOwner
        author_id = self._get_id_from_peer(replied_message.from_id)
        author_entity = self._get_chat_entity(author_id)
        author_name = self._get_entity_name(author_entity)
        original_fwd_tag, _ = self._get_original_author_details(replied_message.fwd_from)

        quote_snippet = ""
        if replied_message_obj.isPhoto():
            quote_snippet = "Photo"
        elif replied_message_obj.isVideo():
            quote_snippet = "Video"
        elif replied_message_obj.isVoice():
            quote_snippet = "Voice Message"
        elif replied_message_obj.isSticker():
            quote_snippet = str(replied_message_obj.messageText) if replied_message_obj.messageText else "Sticker"
        elif replied_message and replied_message.message:
            raw_text = replied_message.message
            quote_snippet = re.sub(r'[\s\r\n]+', ' ', raw_text).strip()
        else:
            quote_snippet = "Media"

        if self._get_java_len(quote_snippet) > 44:
            quote_snippet = quote_snippet[:44].strip() + "..."
                
        if original_fwd_tag:
            quote_snippet += f" (from {original_fwd_tag})"

        quote_text = f"{author_name}\n\u200b{quote_snippet}"
        entities = ArrayList()
        
        if isinstance(author_entity, TLRPC.TL_user):
            self._add_user_entities(entities, quote_text, author_entity, author_name)
        else:
            bold_entity = TLRPC.TL_messageEntityBold()
            bold_entity.offset = 0
            bold_entity.length = self._get_java_len(author_name)
            entities.add(bold_entity)

        quote_entity = TLRPC.TL_messageEntityBlockquote()
        quote_entity.offset = 0
        quote_entity.length = self._get_java_len(quote_text)
        entities.add(quote_entity)

        return quote_text, entities

    def _send_album(self, message_objects, rule):
        """Constructs and sends an album, filtering each item and attaching a header/quote to the first."""
        if not message_objects:
            return
        
        to_peer_id = rule["destination"]
        drop_author = rule.get("drop_author", True)
        quote_replies = rule.get("quote_replies", True)
        filters = rule.get("filters", {})

        try:
            req = TLRPC.TL_messages_sendMultiMedia()
            req.peer = get_messages_controller().getInputPeer(to_peer_id)
            multi_media_list = ArrayList()

            album_caption = ""
            album_entities = None
            text_allowed = filters.get("text", True)
            if text_allowed:
                for msg_obj in message_objects:
                    if msg_obj.messageOwner and msg_obj.messageOwner.message:
                        album_caption = msg_obj.messageOwner.message
                        album_entities = msg_obj.messageOwner.entities
                        break

            first_message_obj = message_objects[0]
            first_message = first_message_obj.messageOwner
            
            prefix_text, prefix_entities = "", ArrayList()
            if not drop_author:
                source_entity = self._get_chat_entity(self._get_id_from_peer(first_message.peer_id))
                author_entity = self._get_chat_entity(self._get_id_from_peer(first_message.from_id))
                if source_entity:
                    header_text, header_entities = self._build_forward_header(first_message, source_entity, author_entity)
                    if header_text:
                        prefix_text += header_text
                    if header_entities:
                        prefix_entities.addAll(header_entities)
            
            if quote_replies:
                quote_text, quote_entities = self._build_reply_quote(first_message_obj)
                if quote_text:
                    if prefix_text: prefix_text += "\n\n"
                    if quote_entities:
                        for i in range(quote_entities.size()):
                            entity = quote_entities.get(i)
                            entity.offset += len(prefix_text)
                        prefix_entities.addAll(quote_entities)
                    prefix_text += quote_text
            
            header_attached = False
            for original_msg_obj in message_objects:
                current_msg_obj = original_msg_obj
                if not self._is_media_complete(original_msg_obj.messageOwner):
                    try:
                        original_message = original_msg_obj.messageOwner
                        if hasattr(get_messages_controller(), 'getMessage'):
                            cached_message_obj = get_messages_controller().getMessage(original_message.dialog_id, original_message.id)
                            if cached_message_obj and self._is_media_complete(cached_message_obj.messageOwner):
                                current_msg_obj = cached_message_obj
                                log(f"[{self.id}] Refreshed incomplete album part {original_message.id} from cache.")
                    except Exception as e:
                        log(f"[{self.id}] Could not refresh album part from cache. Error: {e}")

                if not self._is_message_allowed_by_filters(current_msg_obj, rule):
                    continue
                
                input_media = self._get_input_media(current_msg_obj)
                if not input_media:
                    continue

                single_media = TLRPC.TL_inputSingleMedia()
                single_media.media = input_media
                single_media.random_id = random.getrandbits(63)

                if not header_attached:
                    final_caption = f"{prefix_text}\n\n{album_caption}".strip()
                    final_entities = self._prepare_final_entities(prefix_text, prefix_entities, album_entities)
                    single_media.message = final_caption
                    if final_entities and not final_entities.isEmpty():
                        single_media.entities = final_entities
                        single_media.flags |= 1
                    header_attached = True
                else:
                    single_media.message = ""
                multi_media_list.add(single_media)

            if not multi_media_list.isEmpty():
                req.multi_media = multi_media_list
                send_request(req, RequestCallback(lambda r, e: None))
        except Exception:
            log(f"[{self.id}] ERROR in _send_album: {traceback.format_exc()}")

    def _send_forwarded_message(self, message_object, rule):
        """Constructs and sends a single message."""
        message = message_object.messageOwner
        if not message: return
        
        to_peer_id = rule["destination"]
        drop_author = rule.get("drop_author", True)
        quote_replies = rule.get("quote_replies", True)
        filters = rule.get("filters", {})
        text_allowed = filters.get("text", True)

        try:
            input_media = self._get_input_media(message_object)
            original_text = (message.message or "") if text_allowed else ""
            
            # Apply text replacement if configured
            original_text = self._apply_text_replacement(original_text, rule)
            
            original_entities = message.entities if text_allowed else None

            prefix_text, prefix_entities = "", ArrayList()
            if not drop_author:
                source_entity = self._get_chat_entity(self._get_id_from_peer(message.peer_id))
                author_entity = self._get_chat_entity(self._get_id_from_peer(message.from_id))
                if source_entity:
                    header_text, header_entities = self._build_forward_header(message, source_entity, author_entity)
                    if header_text:
                        prefix_text += header_text
                    if header_entities:
                        prefix_entities.addAll(header_entities)
            
            if quote_replies:
                quote_text, quote_entities = self._build_reply_quote(message_object)
                if quote_text:
                    if prefix_text: prefix_text += "\n\n"
                    if quote_entities:
                        for i in range(quote_entities.size()):
                            entity = quote_entities.get(i)
                            entity.offset += len(prefix_text)
                        prefix_entities.addAll(quote_entities)
                    prefix_text += quote_text
            
            message_text = f"{prefix_text}\n\n{original_text}".strip()
            entities = self._prepare_final_entities(prefix_text, prefix_entities, original_entities)

            req = None
            if input_media:
                req = TLRPC.TL_messages_sendMedia()
                req.media = input_media
                req.message = message_text
            elif message_text.strip():
                req = TLRPC.TL_messages_sendMessage()
                req.message = message_text
            
            if req:
                req.peer = get_messages_controller().getInputPeer(to_peer_id)
                req.random_id = random.getrandbits(63)
                if entities and not entities.isEmpty():
                    req.entities = entities
                    req.flags |= 8
                send_request(req, RequestCallback(lambda r, e: None))
        except Exception:
            log(f"[{self.id}] ERROR in _send_forwarded_message: {traceback.format_exc()}")

    def _get_input_media(self, message_object):
        """Safely extracts forwardable media from a message object."""
        media = getattr(message_object.messageOwner, "media", None)
        if not media: return None
        try:
            if isinstance(media, TLRPC.TL_messageMediaPhoto) and hasattr(media, "photo"):
                photo = media.photo
                input_media = TLRPC.TL_inputMediaPhoto();
                input_media.id = TLRPC.TL_inputPhoto()
                input_media.id.id, input_media.id.access_hash = photo.id, photo.access_hash
                input_media.id.file_reference = photo.file_reference or bytearray(0)
                return input_media
            if isinstance(media, TLRPC.TL_messageMediaDocument) and hasattr(media, "document"):
                doc = media.document
                input_media = TLRPC.TL_inputMediaDocument();
                input_media.id = TLRPC.TL_inputDocument()
                input_media.id.id, input_media.id.access_hash = doc.id, doc.access_hash
                input_media.id.file_reference = doc.file_reference or bytearray(0)
                return input_media
        except Exception:
            log(f"[{self.id}] Failed to get input media: {traceback.format_exc()}")
        return None

    def create_settings(self) -> list:
        """Builds the plugin's settings page UI."""
        self._load_configurable_settings()
        self._load_forwarding_rules()
        settings_ui = [
            Header(text="General Settings"),
            Input(key="min_msg_length", text="Minimum Message Length", default=str(DEFAULT_SETTINGS["min_msg_length"]), subtext="For text-only messages."),
            Input(key="max_msg_length", text="Maximum Message Length", default=str(DEFAULT_SETTINGS["max_msg_length"]), subtext="For text-only messages."),
            Input(key="deferral_timeout_ms", text="Media Deferral Timeout (ms)", default=str(DEFAULT_SETTINGS["deferral_timeout_ms"]), subtext="Safety net for slow media downloads. Increase if files fail to send."),
            Input(key="album_timeout_ms", text="Album Buffering Timeout (ms)", default=str(DEFAULT_SETTINGS["album_timeout_ms"]), subtext="How long to wait for all media in an album before sending."),
            Input(key="deduplication_window_seconds", text="Deduplication Window (Seconds)", default=str(DEFAULT_SETTINGS["deduplication_window_seconds"]), subtext="Time window to ignore duplicate events."),
            Input(key="antispam_delay_seconds", text="Anti-Spam Delay (Seconds)", default=str(DEFAULT_SETTINGS["antispam_delay_seconds"]), subtext="Minimum time between forwards from the same user. 0 to disable."),
            Input(key="sequential_delay_seconds", text="Sequential Processing Delay (Seconds)", default=str(DEFAULT_SETTINGS["sequential_delay_seconds"]), subtext="Delay between processing items in the worker queue."),
            Divider(),
            Header(text="Global Presets"),
            Input(key="global_keyword_preset", text="Global Keyword Preset", default="", subtext="Regex pattern that messages must match when enabled in rules."),
            Input(key="global_blacklist_words", text="Global Blacklist Words", default="", subtext="Comma-separated words to block. Messages containing any will be dropped."),
            Divider(),
            Header(text="Queue Control"),
            Text(text="Clear Pending Queue", icon="msg_delete", accent=True, on_click=lambda v: run_on_ui_thread(lambda: self._clear_pending_queue())),
            Text(text="Process All Unread", icon="msg_unread", accent=True, on_click=lambda v: run_on_ui_thread(lambda: self._batch_process_all_unread())),
            Text(text="Process All History", icon="msg_calendar", accent=True, on_click=lambda v: run_on_ui_thread(lambda: self._show_history_days_dialog())),
            Divider(),
            Header(text="Active Forwarding Rules")
        ]
        if not self.forwarding_rules:
            settings_ui.append(Text(text="No rules configured. Set one from any chat's menu.", icon="msg_info"))
        else:
            sorted_rules = sorted(self.forwarding_rules.items(), key=lambda item: self._get_chat_name(item[0]).lower())
            for source_id, rule_data in sorted_rules:
                source_name = self._get_chat_name(source_id)
                dest_name = self._get_chat_name(rule_data.get("destination", 0)) if rule_data.get("destination") else "Not Set"
                style = "(Copy)" if rule_data.get("drop_author", True) else "(Forward)"
                settings_ui.append(Text(
                    text=f"From: {source_name}\nTo: {dest_name} {style}",
                    icon="msg_edit",
                    on_click=lambda v, sid=source_id: self._show_rule_action_dialog(sid)
                ))
        settings_ui.append(Divider())
        settings_ui.extend([
            Divider(),
            Header(text="Support the Developer"),
            Text(text="TON", icon="msg_ton", accent=True, on_click=lambda view: run_on_ui_thread(lambda: self._copy_to_clipboard(self.TON_ADDRESS, "TON"))),
            Text(text="USDT (TRC20)", icon="msg_copy", accent=True, on_click=lambda view: run_on_ui_thread(lambda: self._copy_to_clipboard(self.USDT_ADDRESS, "USDT"))),
            Divider(),
            Text(text="Disclaimer & FAQ", icon="msg_help", accent=True, on_click=lambda v: run_on_ui_thread(lambda: self._show_faq_dialog())),
        ])
        return settings_ui

    def _show_faq_dialog(self):
        """Builds and displays the FAQ and Disclaimer in a themed, scrollable dialog."""
        activity = get_last_fragment().getParentActivity()
        if not activity: return
        try:
            builder = AlertDialogBuilder(activity)
            builder.set_title("Disclaimer & FAQ")
            margin_dp = 20
            margin_px = int(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, margin_dp, activity.getResources().getDisplayMetrics()))

            scroller = ScrollView(activity)
            layout = LinearLayout(activity)
            layout.setOrientation(LinearLayout.VERTICAL)
            layout.setPadding(margin_px, margin_px // 2, margin_px, margin_px // 2)

            faq_text_view = TextView(activity)
            
            def process_inline_markdown(text):
                text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text) # Links
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text) # Bold
                text = re.sub(r'__(.*?)__', r'<u>\1</u>', text) # Underline
                text = re.sub(r'~~(.*?)~~', r'<s>\1</s>', text) # Strikethrough
                text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text) # Italics
                text = re.sub(r'`(.*?)`', r'<tt>\1</tt>', text) # Monospace
                return text

            accent_color_hex = f"#{Theme.getColor(Theme.key_dialogTextLink) & 0xFFFFFF:06x}"
            spoiler_color_hex = f"#{Theme.getColor(Theme.key_windowBackgroundGray) & 0xFFFFFF:06x}"
            
            html_lines = []
            for line in FAQ_TEXT.strip().split('\n'):
                stripped_line = line.strip()
                if not stripped_line:
                    html_lines.append('')
                    continue
                if stripped_line == '---':
                    html_lines.append(f"<p align='center'><font color='{accent_color_hex}'>•&nbsp;•&nbsp;•</font></p>")
                    continue
                
                content_spoilers_processed = re.sub(r'\|\|(.*?)\|\|', rf'<font style="background-color:{spoiler_color_hex};color:{spoiler_color_hex};">&nbsp;\1&nbsp;</font>', stripped_line)
                
                if stripped_line.startswith('* '):
                    content_final = process_inline_markdown(content_spoilers_processed[2:])
                    html_lines.append(f"&nbsp;&nbsp;•&nbsp;&nbsp;{content_final}")
                elif re.match(r'^\*\*(.*)\*\*$', stripped_line):
                    content = stripped_line.replace('**', '').strip()
                    html_lines.append(f"<h4><font color='{accent_color_hex}'>{content}</font></h4>")
                else:
                    html_lines.append(process_inline_markdown(content_spoilers_processed))
            
            html_text = '<br>'.join(html_lines)
            html_text = re.sub(r'(<br>){2,}', '<br>', html_text)
            html_text = html_text.replace('<br><p', '<p').replace('</p><br>', '</p>')
            html_text = html_text.replace('<br><h4', '<br><br><h4').strip()

            if hasattr(Html, 'FROM_HTML_MODE_LEGACY'):
                faq_text_view.setText(Html.fromHtml(html_text, Html.FROM_HTML_MODE_LEGACY))
            else:
                faq_text_view.setText(Html.fromHtml(html_text))
            
            faq_text_view.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            faq_text_view.setMovementMethod(LinkMovementMethod.getInstance())
            faq_text_view.setLinkTextColor(Theme.getColor(Theme.key_dialogTextLink))
            faq_text_view.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15)
            faq_text_view.setLineSpacing(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, 2.0, activity.getResources().getDisplayMetrics()), 1.0)
            
            layout.addView(faq_text_view)
            scroller.addView(layout)
            builder.set_view(scroller)
            builder.set_positive_button("Close", None)
            builder.show()
        except Exception:
            log(f"[{self.id}] ERROR showing FAQ dialog: {traceback.format_exc()}")

    def _load_forwarding_rules(self):
        """Loads forwarding rules from persistent storage."""
        try:
            rules_str = self.get_setting(FORWARDING_RULES_KEY, "{}")
            self.forwarding_rules = {int(k): v for k, v in json.loads(rules_str).items()}
        except Exception:
            self.forwarding_rules = {}

    def _save_forwarding_rules(self):
        """Saves the current forwarding rules to persistent storage."""
        self.set_setting(FORWARDING_RULES_KEY, json.dumps({str(k): v for k, v in self.forwarding_rules.items()}))
        self._load_forwarding_rules()

    def _copy_to_clipboard(self, text_to_copy: str, label: str):
        """Copies text to the clipboard and shows a toast notification."""
        activity = get_last_fragment().getParentActivity()
        if not activity: return
        try:
            clipboard = activity.getSystemService(Context.CLIPBOARD_SERVICE)
            clip = ClipData.newPlainText(label, text_to_copy)
            clipboard.setPrimaryClip(clip)
            Toast.makeText(activity, f"{label} address copied to clipboard!", Toast.LENGTH_SHORT).show()
        except Exception:
            log(f"[{self.id}] Failed to copy to clipboard: {traceback.format_exc()}")

    def _get_id_from_peer(self, peer):
        """Extracts a standard numerical ID from a TLRPC Peer object."""
        if not peer: return 0
        if isinstance(peer, TLRPC.TL_peerChannel): return -peer.channel_id
        if isinstance(peer, TLRPC.TL_peerChat): return -peer.chat_id
        if isinstance(peer, TLRPC.TL_peerUser): return peer.user_id
        return 0

    def _get_id_for_storage(self, entity):
        """Gets the correct ID for storing in rules (negative for chats/channels)."""
        if not entity: return 0
        return -entity.id if not isinstance(entity, TLRPC.TL_user) else entity.id

    def _get_chat_entity_from_input_id(self, input_id: int):
        """Retrieves a user or chat object from a numerical ID by checking local cache."""
        if input_id == 0: return None
        abs_id = abs(input_id)
        controller = get_messages_controller()
        entity = controller.getChat(abs_id)
        if entity: return entity
        if input_id > 0: return controller.getUser(input_id)
        return None

    def _sanitize_chat_id_for_request(self, input_id: int) -> int:
        """Converts a user-provided ID into a server-compatible short ID for channel/supergroup lookups."""
        id_str = str(abs(input_id))
        if id_str.startswith("100") and len(id_str) > 9:
            try:
                return int(id_str[3:])
            except (ValueError, IndexError):
                pass
        return abs(input_id)

    def _get_chat_entity(self, dialog_id):
        """A robust way to get a chat entity from a dialog_id."""
        if not isinstance(dialog_id, int):
            try: dialog_id = int(dialog_id)
            except (ValueError, TypeError): return None
        return get_messages_controller().getUser(dialog_id) if dialog_id > 0 else get_messages_controller().getChat(abs(dialog_id))

    def _get_entity_name(self, entity):
        """Gets a display-friendly name for a user, chat, or channel entity."""
        if not entity: return "Unknown"
        if hasattr(entity, 'title'): return entity.title
        if hasattr(entity, 'first_name'):
            name = f"{entity.first_name or ''} {entity.last_name or ''}".strip()
            return name if name else f"ID: {entity.id}"
        return f"ID: {getattr(entity, 'id', 'N/A')}"

    def _get_entity_tag(self, entity):
        """Gets an @username tag or falls back to the entity name."""
        if not entity: return "Unknown"
        if hasattr(entity, 'username') and entity.username:
            return f"@{entity.username}"
        return self._get_entity_name(entity)

    def _get_chat_name(self, chat_id):
        """A convenience function to get a chat name directly from its ID."""
        return self._get_entity_name(self._get_chat_entity(int(chat_id)))

    def _get_original_author_details(self, fwd_header):
        """Helper to extract original author details from a fwd_header."""
        if not fwd_header: return None, None
        original_author_name = None
        original_author_entity = None
        original_author_id = self._get_id_from_peer(getattr(fwd_header, 'from_id', None))
        if original_author_id:
            original_author_entity = self._get_chat_entity(original_author_id)
        if original_author_entity:
            original_author_name = self._get_entity_name(original_author_entity)
        elif hasattr(fwd_header, 'from_name') and fwd_header.from_name:
            original_author_name = fwd_header.from_name
        return original_author_name, original_author_entity

    def _prepare_final_entities(self, prefix_text, prefix_entities, original_entities):
        """Combines prefix entities (headers/quotes) and original message entities, adjusting offsets."""
        final_entities = ArrayList()
        if prefix_entities:
            final_entities.addAll(prefix_entities)
        
        if original_entities and not original_entities.isEmpty():
            offset_shift = self._get_java_len(prefix_text) + 2 if prefix_text else 0
            for i in range(original_entities.size()):
                old = original_entities.get(i)
                new = type(old)();
                new.offset, new.length = old.offset + offset_shift, old.length
                if hasattr(old, 'url'): new.url = old.url
                if hasattr(old, 'user_id'): new.user_id = old.user_id
                final_entities.add(new)
        return final_entities

    def _build_forward_header(self, message, source_entity, author_entity):
        """Constructs the 'Forwarded from...' text and its interactive entities."""
        is_channel = isinstance(source_entity, TLRPC.TL_channel) and not getattr(source_entity, 'megagroup', False)
        is_group = isinstance(source_entity, TLRPC.TL_chat) or (isinstance(source_entity, TLRPC.TL_channel) and getattr(source_entity, 'megagroup', True))
        
        if is_channel:
            return self._build_channel_header(message, source_entity)
        if is_group:
            return self._build_group_header(message, source_entity, author_entity)
        
        me = get_user_config().getCurrentUser()
        sender, receiver = (author_entity, source_entity) if message.out else (author_entity, me)
        return self._build_private_header(message, sender, receiver)

    def _build_channel_header(self, message, channel):
        """Builds the header for forwards from a channel, creating a clickable link."""
        name = self._get_entity_name(channel)
        entities = ArrayList()
        original_author_name, _ = self._get_original_author_details(message.fwd_from)
        text = f"Forwarded from {name}"
        if original_author_name:
            text += f" (fwd_from {original_author_name})"
        
        link = TLRPC.TL_messageEntityTextUrl();
        link.offset, link.length = text.find(name), self._get_java_len(name)
        msg_id = message.fwd_from.channel_post if message.fwd_from and message.fwd_from.channel_post else message.id
        link.url = f"https://t.me/{channel.username}/{msg_id}" if channel.username else f"https://t.me/c/{channel.id}/{msg_id}"
        entities.add(link)
        return text, entities

    def _build_group_header(self, message, group, author):
        """Builds the header for forwards from a group, with mentions and links."""
        group_name = self._get_entity_name(group)
        author_name = self._get_entity_name(author)
        entities = ArrayList()
        original_author_name, original_author_entity = self._get_original_author_details(message.fwd_from)
        text = f"Forwarded from {group_name} (by {author_name})"
        if original_author_name:
            text += f" fwd_from {original_author_name}"

        if isinstance(group, TLRPC.TL_channel):
            msg_id = message.id
            group_link = f"https://t.me/{group.username}/{msg_id}" if group.username else f"https://t.me/c/{group.id}/{msg_id}"
            link_entity = TLRPC.TL_messageEntityTextUrl();
            link_entity.offset, link_entity.length, link_entity.url = text.find(group_name), self._get_java_len(group_name), group_link
            entities.add(link_entity)
        else:
            bold = TLRPC.TL_messageEntityBold();
            bold.offset, bold.length = text.find(group_name), self._get_java_len(group_name)
            entities.add(bold)

        if author and isinstance(author, TLRPC.TL_user):
            self._add_user_entities(entities, text, author, author_name)
        
        if original_author_entity and isinstance(original_author_entity, TLRPC.TL_user):
            self._add_user_entities(entities, text, original_author_entity, original_author_name)
            
        return text, entities

    def _build_private_header(self, message, sender, receiver):
        """Builds the header for private chats, mentioning users where possible."""
        sender_name = self._get_entity_name(sender)
        receiver_name = self._get_entity_name(receiver)
        entities = ArrayList()
        original_author_name, original_author_entity = self._get_original_author_details(message.fwd_from)
        text = f"Forwarded from {sender_name} to {receiver_name}"
        if original_author_name:
            text += f" (original fwd_from {original_author_name})"

        for entity, name in [(sender, sender_name), (receiver, receiver_name), (original_author_entity, original_author_name)]:
            if entity and isinstance(entity, TLRPC.TL_user):
                self._add_user_entities(entities, text, entity, name)
                
        return text, entities

    def _add_chat_menu_item(self):
        """Adds the 'Auto Forward' item to the chat menu."""
        self.add_menu_item(MenuItemData(
            menu_type=MenuItemType.CHAT_ACTION_MENU,
            text="Auto Forward...",
            icon="msg_forward",
            on_click=self._on_menu_item_click
        ))

    def _on_menu_item_click(self, context):
        """Handles the click event for the chat menu item."""
        current_chat_id = context.get("dialog_id")
        if not current_chat_id: return
        current_chat_id = int(current_chat_id)
        
        if current_chat_id in self.forwarding_rules:
            run_on_ui_thread(lambda: self._show_rule_action_dialog(current_chat_id))
        else:
            source_name = self._get_chat_name(current_chat_id)
            run_on_ui_thread(lambda: self._show_destination_input_dialog(current_chat_id, source_name))

    def _show_rule_action_dialog(self, source_id):
        """Shows a dialog to either modify or delete a rule."""
        activity = get_last_fragment().getParentActivity()
        if not activity: return
        builder = AlertDialogBuilder(activity)
        builder.set_title("Manage Rule")
        builder.set_message(f"What would you like to do with the rule for '{self._get_chat_name(source_id)}'?")
        builder.set_positive_button("Modify", lambda b, w: self._launch_modification_dialog(source_id))
        builder.set_neutral_button("Cancel", lambda b, w: b.dismiss())
        builder.set_negative_button("Delete", lambda b, w: self._delete_rule_with_confirmation(source_id))
        run_on_ui_thread(lambda: builder.show())

    def _launch_modification_dialog(self, source_id):
        """Fetches existing rule data and launches the setup dialog to modify it."""
        rule_data = self.forwarding_rules.get(source_id)
        if not rule_data:
            BulletinHelper.show_error("Could not find rule to modify.")
            return
        source_name = self._get_chat_name(source_id)
        run_on_ui_thread(lambda: self._show_destination_input_dialog(source_id, source_name, existing_rule=rule_data))

    def _show_destination_input_dialog(self, source_id, source_name, existing_rule=None):
        """Displays the main dialog to set up or modify a forwarding rule."""
        activity = get_last_fragment().getParentActivity()
        if not activity: return
        try:
            builder = AlertDialogBuilder(activity)
            title = f"Modify Rule for '{source_name}'" if existing_rule else f"Set Destination for '{source_name}'"
            builder.set_title(title)
            
            margin_dp = 20
            margin_px = int(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, margin_dp, activity.getResources().getDisplayMetrics()))
            
            main_layout = LinearLayout(activity)
            main_layout.setOrientation(LinearLayout.VERTICAL)
            main_layout.setPadding(margin_px, margin_px // 2, margin_px, margin_px // 4)
            
            input_field = EditText(activity)
            input_field_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            input_field_params.setMargins(margin_px, margin_px // 2, margin_px, 0)
            input_field.setHint("Link, @username, or ID")
            input_field.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            input_field.setHintTextColor(Theme.getColor(Theme.key_dialogTextHint))
            input_field.setLayoutParams(input_field_params)
            main_layout.addView(input_field)
            
            checkbox_tint_list = ColorStateList([[-16842912], [16842912]], [Theme.getColor(Theme.key_checkbox), Theme.getColor(Theme.key_checkboxCheck)])
            
            checkbox_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            checkbox_params.setMargins(margin_px, 0, margin_px, 0)
    
            drop_author_checkbox = CheckBox(activity)
            drop_author_checkbox.setText("Remove Original Author (Copy)")
            drop_author_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            drop_author_checkbox.setButtonTintList(checkbox_tint_list)
            drop_author_checkbox.setLayoutParams(checkbox_params)
            main_layout.addView(drop_author_checkbox)
    
            quote_replies_checkbox = CheckBox(activity)
            quote_replies_checkbox.setText("Quote Replies")
            quote_replies_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            quote_replies_checkbox.setButtonTintList(checkbox_tint_list)
            quote_replies_checkbox.setLayoutParams(checkbox_params)
            main_layout.addView(quote_replies_checkbox)
            
            divider_height_px = int(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, 1, activity.getResources().getDisplayMetrics()))
            divider_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, divider_height_px)
            extra_left_margin_dp = 16 
            extra_left_margin_px = int(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, extra_left_margin_dp, activity.getResources().getDisplayMetrics()))
            
            # Define a balanced vertical margin for the dividers.
            vertical_margin_dp = 12
            vertical_margin_px = int(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, vertical_margin_dp, activity.getResources().getDisplayMetrics()))
            divider_params.setMargins(margin_px + extra_left_margin_px, vertical_margin_px, margin_px, vertical_margin_px)
    
            divider_one = View(activity)
            divider_one.setBackgroundColor(Theme.getColor(Theme.key_divider))
            divider_one.setLayoutParams(divider_params)
            main_layout.addView(divider_one)
    
            # --- Author Type Checkboxes ---
            author_header_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            author_header_params.setMargins(margin_px, 0, margin_px, 0)
            author_header = TextView(activity)
            author_header.setText("Forward messages from:")
            author_header.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            author_header.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16)
            author_header.setLayoutParams(author_header_params)
            main_layout.addView(author_header)
    
            forward_users_checkbox = CheckBox(activity)
            forward_users_checkbox.setText("Users")
            forward_users_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            forward_users_checkbox.setButtonTintList(checkbox_tint_list)
            forward_users_checkbox.setLayoutParams(checkbox_params)
            main_layout.addView(forward_users_checkbox)
            
            forward_bots_checkbox = CheckBox(activity)
            forward_bots_checkbox.setText("Bots")
            forward_bots_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            forward_bots_checkbox.setButtonTintList(checkbox_tint_list)
            forward_bots_checkbox.setLayoutParams(checkbox_params)
            main_layout.addView(forward_bots_checkbox)
    
            forward_outgoing_checkbox = CheckBox(activity)
            forward_outgoing_checkbox.setText("Outgoing Messages")
            forward_outgoing_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            forward_outgoing_checkbox.setButtonTintList(checkbox_tint_list)
            forward_outgoing_checkbox.setLayoutParams(checkbox_params)
            main_layout.addView(forward_outgoing_checkbox)
            
            divider_two = View(activity)
            divider_two.setBackgroundColor(Theme.getColor(Theme.key_divider))
            divider_two.setLayoutParams(divider_params)
            main_layout.addView(divider_two)
            
            # --- Content Filter Section ---
            filter_header_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            filter_header_params.setMargins(margin_px, 0, margin_px, 0)
            filter_header = TextView(activity)
            filter_header.setText("Content to forward:")
            filter_header.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            filter_header.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16)
            filter_header.setLayoutParams(filter_header_params)
            main_layout.addView(filter_header)
            
            filter_checkboxes = {}
            for key, label in FILTER_TYPES.items():
                cb = CheckBox(activity)
                cb.setText(label)
                cb.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
                cb.setButtonTintList(checkbox_tint_list)
                cb.setLayoutParams(checkbox_params)
                main_layout.addView(cb)
                filter_checkboxes[key] = cb
    
            # --- Advanced Filtering Section ---
            divider_three = View(activity)
            divider_three.setBackgroundColor(Theme.getColor(Theme.key_divider))
            divider_three.setLayoutParams(divider_params)
            main_layout.addView(divider_three)
            
            advanced_header = TextView(activity)
            advanced_header.setText("Advanced Filtering:")
            advanced_header.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            advanced_header.setTextSize(TypedValue.COMPLEX_UNIT_SP, 16)
            advanced_header.setLayoutParams(author_header_params)
            main_layout.addView(advanced_header)
            
            # Author Filter
            author_filter_field = EditText(activity)
            author_filter_field.setHint("Author Filter (IDs/Usernames, comma-separated)")
            author_filter_field.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            author_filter_field.setHintTextColor(Theme.getColor(Theme.key_dialogTextHint))
            author_filter_field.setLayoutParams(input_field_params)
            main_layout.addView(author_filter_field)
            
            # Text Replacement
            text_replacement_field = EditText(activity)
            text_replacement_field.setHint("Text Replacement (e.g., s/old/new/)")
            text_replacement_field.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            text_replacement_field.setHintTextColor(Theme.getColor(Theme.key_dialogTextHint))
            text_replacement_field.setLayoutParams(input_field_params)
            main_layout.addView(text_replacement_field)
            
            # Use Global Keywords Checkbox
            use_global_keywords_checkbox = CheckBox(activity)
            use_global_keywords_checkbox.setText("Use Global Keyword Preset")
            use_global_keywords_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            use_global_keywords_checkbox.setButtonTintList(checkbox_tint_list)
            use_global_keywords_checkbox.setLayoutParams(checkbox_params)
            main_layout.addView(use_global_keywords_checkbox)
            
            # Batch Ignore Checkbox
            batch_ignore_checkbox = CheckBox(activity)
            batch_ignore_checkbox.setText("Exclude from Global Batch Tools")
            batch_ignore_checkbox.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            batch_ignore_checkbox.setButtonTintList(checkbox_tint_list)
            batch_ignore_checkbox.setLayoutParams(checkbox_params)
            main_layout.addView(batch_ignore_checkbox)
            
            # Set by Replying Button (add as a text button)
            set_by_reply_text = TextView(activity)
            set_by_reply_text.setText("📍 Set Destination by Replying")
            set_by_reply_text.setTextColor(Theme.getColor(Theme.key_dialogTextLink))
            set_by_reply_text.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14)
            set_by_reply_text.setTypeface(Typeface.DEFAULT_BOLD)
            set_by_reply_text_params = LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            set_by_reply_text_params.setMargins(margin_px, margin_px // 2, margin_px, margin_px // 2)
            set_by_reply_text.setLayoutParams(set_by_reply_text_params)
            set_by_reply_text.setOnClickListener(lambda v: self._start_reply_listener(source_id, input_field))
            main_layout.addView(set_by_reply_text)
    
            if existing_rule:
                destination_id = existing_rule.get("destination", 0)
                dest_entity = self._get_chat_entity(destination_id)
                identifier_to_set = str(destination_id)
                if dest_entity and hasattr(dest_entity, 'username') and dest_entity.username:
                    identifier_to_set = f"@{dest_entity.username}"
                input_field.setText(identifier_to_set)
                
                drop_author_checkbox.setChecked(existing_rule.get("drop_author", False))
                quote_replies_checkbox.setChecked(existing_rule.get("quote_replies", True))
                
                forward_users_checkbox.setChecked(existing_rule.get("forward_users", True))
                forward_bots_checkbox.setChecked(existing_rule.get("forward_bots", True))
                forward_outgoing_checkbox.setChecked(existing_rule.get("forward_outgoing", True))
                
                current_filters = existing_rule.get("filters", {})
                for key, cb in filter_checkboxes.items():
                    cb.setChecked(current_filters.get(key, True))
                
                # Advanced fields
                author_filter_field.setText(existing_rule.get("author_filter", ""))
                text_replacement_field.setText(existing_rule.get("text_replacement", ""))
                use_global_keywords_checkbox.setChecked(existing_rule.get("use_global_keywords", False))
                batch_ignore_checkbox.setChecked(existing_rule.get("batch_ignore", False))
            else:
                drop_author_checkbox.setChecked(False)
                quote_replies_checkbox.setChecked(True)
                forward_users_checkbox.setChecked(True)
                forward_bots_checkbox.setChecked(True)
                forward_outgoing_checkbox.setChecked(True)
                for cb in filter_checkboxes.values():
                    cb.setChecked(True)
                use_global_keywords_checkbox.setChecked(False)
                batch_ignore_checkbox.setChecked(False)
    
            scroller = ScrollView(activity)
            scroller.addView(main_layout)
            builder.set_view(scroller)
            
            def on_set_click(b, w):
                filter_settings = {key: cb.isChecked() for key, cb in filter_checkboxes.items()}
                self._process_destination_input(
                    source_id,
                    source_name,
                    input_field.getText().toString(),
                    drop_author_checkbox.isChecked(),
                    quote_replies_checkbox.isChecked(),
                    forward_users_checkbox.isChecked(),
                    forward_bots_checkbox.isChecked(),
                    forward_outgoing_checkbox.isChecked(),
                    filter_settings,
                    author_filter_field.getText().toString(),
                    text_replacement_field.getText().toString(),
                    use_global_keywords_checkbox.isChecked(),
                    batch_ignore_checkbox.isChecked()
                )
            
            builder.set_positive_button("Set", on_set_click)
            builder.set_negative_button("Cancel", lambda b, w: b.dismiss())
            run_on_ui_thread(lambda: builder.show())
        except Exception:
            log(f"[{self.id}] ERROR showing rule setup dialog: {traceback.format_exc()}")

    def _process_destination_input(self, source_id, source_name, user_input, drop_author, quote_replies, forward_users, forward_bots, forward_outgoing, filter_settings, author_filter="", text_replacement="", use_global_keywords=False, batch_ignore=False):
        """Handles all destination types with a multi-step resolution logic."""
        cleaned_input = (user_input or "").strip()
        if not cleaned_input: return

        # A dictionary to pass all the rule settings neatly.
        rule_settings = {
            "drop_author": drop_author,
            "quote_replies": quote_replies,
            "forward_users": forward_users,
            "forward_bots": forward_bots,
            "forward_outgoing": forward_outgoing,
            "filter_settings": filter_settings,
            "author_filter": author_filter,
            "text_replacement": text_replacement,
            "use_global_keywords": use_global_keywords,
            "batch_ignore": batch_ignore
        }

        if "/joinchat/" in cleaned_input or "/+" in cleaned_input:
            self._resolve_as_invite_link(cleaned_input, source_id, source_name, rule_settings)
            return
        
        try:
            input_as_int = int(cleaned_input)
            cached_entity = self._get_chat_entity_from_input_id(input_as_int)
            if cached_entity:
                self._finalize_rule(source_id, source_name, self._get_id_for_storage(cached_entity), self._get_entity_name(cached_entity), rule_settings)
                return
            self._resolve_by_id_shotgun(input_as_int, source_id, source_name, rule_settings)
        except ValueError:
            self._resolve_as_username(cleaned_input, source_id, source_name, rule_settings)

    def _resolve_as_invite_link(self, cleaned_input, source_id, source_name, rule_settings):
        """Resolves a destination using a t.me/joinchat/... link."""
        try:
            hash_val = cleaned_input.split("/")[-1]
            req = TLRPC.TL_messages_checkChatInvite(); req.hash = hash_val
            
            def on_check_invite(response, error):
                if error or not response or not hasattr(response, 'chat'):
                    error_text = getattr(error, 'text', 'Invalid or expired link')
                    BulletinHelper.show_error(f"Failed to resolve link: {error_text}")
                    return
                dest_entity = response.chat
                if dest_entity:
                    get_messages_controller().putChat(dest_entity, False)
                    dest_id = self._get_id_for_storage(dest_entity)
                    self._finalize_rule(source_id, source_name, dest_id, self._get_entity_name(dest_entity), rule_settings)
            
            send_request(req, RequestCallback(on_check_invite))
        except Exception as e:
            log(f"[{self.id}] Failed to process invite link: {e}")

    def _resolve_by_id_shotgun(self, input_as_int, source_id, source_name, rule_settings):
        """Resolves a numeric ID that is not in the local cache by making a network request."""
        log(f"[{self.id}] ID {input_as_int} not in cache. Attempting network lookup.")
        
        def on_get_chats_complete(response, error):
            if error or not response or not hasattr(response, 'chats') or response.chats.isEmpty():
                error_text = getattr(error, 'text', 'Not found')
                BulletinHelper.show_error(f"Could not find chat by ID: {input_as_int}. Reason: {error_text}")
                return
            
            dest_entity = response.chats.get(0)
            if dest_entity:
                get_messages_controller().putChat(dest_entity, True)
                dest_id = self._get_id_for_storage(dest_entity)
                self._finalize_rule(source_id, source_name, dest_id, self._get_entity_name(dest_entity), rule_settings)
            else:
                BulletinHelper.show_error(f"Could not find chat by ID: {input_as_int}")

        req = TLRPC.TL_messages_getChats()
        id_list = ArrayList()
        possible_ids = HashSet()
        sanitized_short_id = self._sanitize_chat_id_for_request(input_as_int)
        possible_ids.add(sanitized_short_id)
        possible_ids.add(-sanitized_short_id)
        possible_ids.add(abs(input_as_int))
        possible_ids.add(-abs(input_as_int))
        id_list.addAll(possible_ids)
        req.id = id_list
        send_request(req, RequestCallback(on_get_chats_complete))

    def _resolve_as_username(self, username, source_id, source_name, rule_settings):
        """Resolver for public links and @usernames."""
        log(f"[{self.id}] Resolving '{username}' as a username/public link.")
        
        def on_resolve_complete(response, error):
            if error or not response:
                error_text = getattr(error, 'text', 'Not found')
                BulletinHelper.show_error(f"Could not resolve '{username}': {error_text}")
                return
            
            dest_entity = None
            if hasattr(response, 'chats') and response.chats and not response.chats.isEmpty():
                dest_entity = response.chats.get(0)
                get_messages_controller().putChats(response.chats, False)
            elif hasattr(response, 'users') and response.users and not response.users.isEmpty():
                dest_entity = response.users.get(0)
                get_messages_controller().putUsers(response.users, False)
            
            if dest_entity:
                dest_id = self._get_id_for_storage(dest_entity)
                self._finalize_rule(source_id, source_name, dest_id, self._get_entity_name(dest_entity), rule_settings)
            else:
                BulletinHelper.show_error(f"Could not resolve '{username}'.")
        
        try:
            req = TLRPC.TL_contacts_resolveUsername()
            req.username = username.replace("@", "").split("/")[-1]
            send_request(req, RequestCallback(on_resolve_complete))
        except Exception:
            log(f"[{self.id}] ERROR resolving username: {traceback.format_exc()}")

    def _finalize_rule(self, source_id, source_name, destination_id, dest_name, rule_settings):
        """Saves a fully resolved rule to storage and shows a success message."""
        if destination_id == 0:
            log(f"[{self.id}] Finalize rule called with invalid destination_id=0. Aborting.")
            BulletinHelper.show_error("Failed to save rule: Invalid destination chat resolved.")
            return
            
        rule_data = {
            "destination": destination_id,
            "enabled": True,
            "drop_author": rule_settings["drop_author"],
            "quote_replies": rule_settings["quote_replies"],
            "forward_users": rule_settings["forward_users"],
            "forward_bots": rule_settings["forward_bots"],
            "forward_outgoing": rule_settings["forward_outgoing"],
            "filters": rule_settings["filter_settings"],
            "author_filter": rule_settings.get("author_filter", ""),
            "text_replacement": rule_settings.get("text_replacement", ""),
            "use_global_keywords": rule_settings.get("use_global_keywords", False),
            "batch_ignore": rule_settings.get("batch_ignore", False)
        }
        self.forwarding_rules[source_id] = rule_data
        self._save_forwarding_rules()
        run_on_ui_thread(lambda: self._show_success_dialog(source_name, dest_name))

    def _show_success_dialog(self, source_name, dest_name):
        """Shows a success message after a rule is set."""
        activity = get_last_fragment().getParentActivity()
        if not activity: return
        builder = AlertDialogBuilder(activity)
        builder.set_title("Success!");
        builder.set_message(f"Rule for '{source_name}' set to '{dest_name}'.")
        builder.set_positive_button("OK", lambda b, w: b.dismiss())
        run_on_ui_thread(lambda: builder.show())

    def _delete_rule_with_confirmation(self, source_id):
        """Shows a confirmation dialog before deleting a rule."""
        activity = get_last_fragment().getParentActivity()
        if not activity: return
        try:
            builder = AlertDialogBuilder(activity)
            builder.set_title("Delete Rule?")
            builder.set_message(f"Are you sure you want to delete the rule for '{self._get_chat_name(source_id)}'?")
            builder.set_positive_button("Delete", lambda b, w: self._execute_delete(source_id));
            builder.set_negative_button("Cancel", None)
            builder.show()
        except Exception:
            log(f"[{self.id}] ERROR in delete confirmation: {traceback.format_exc()}")

    def _execute_delete(self, source_id):
        """Deletes a rule and refreshes the settings UI."""
        if source_id in self.forwarding_rules:
            del self.forwarding_rules[source_id]
            self._save_forwarding_rules()
            run_on_ui_thread(lambda: self._refresh_settings_ui())

    def _refresh_settings_ui(self):
        """Forces the settings page to rebuild its views to show changes."""
        try:
            last_fragment = get_last_fragment()
            if isinstance(last_fragment, PluginSettingsActivity) and hasattr(last_fragment, 'rebuildViews'):
                last_fragment.rebuildViews()
        except Exception:
            log(f"[{self.id}] ERROR during UI refresh: {traceback.format_exc()}")

    def _process_unread_messages(self, chat_id, rule):
        """Processes unread messages for a specific chat with pagination."""
        try:
            if rule.get("batch_ignore", False):
                log(f"[{self.id}] Skipping batch processing for chat {chat_id} (batch_ignore=True)")
                return
            
            boundary_id = self._get_unread_boundary(chat_id)
            log(f"[{self.id}] Processing unread messages for chat {chat_id} after ID {boundary_id}")
            
            # Implement pagination to fetch all unread messages
            def fetch_batch(offset_id, total_queued):
                req = TLRPC.TL_messages_getHistory()
                req.peer = get_messages_controller().getInputPeer(chat_id)
                req.offset_id = offset_id
                req.offset_date = 0
                req.add_offset = 0
                req.limit = 100  # Max per request
                req.max_id = 0
                req.min_id = boundary_id
                
                def on_history_received(response, error):
                    if error or not response:
                        log(f"[{self.id}] Error fetching history for {chat_id}: {error}")
                        return
                    
                    if not hasattr(response, 'messages') or not response.messages:
                        log(f"[{self.id}] Completed fetching unread messages for chat {chat_id}. Total: {total_queued}")
                        return
                    
                    messages_size = response.messages.size()
                    if messages_size == 0:
                        log(f"[{self.id}] Completed fetching unread messages for chat {chat_id}. Total: {total_queued}")
                        return
                    
                    # Process messages and find the minimum ID for next iteration
                    min_id_in_batch = None
                    count = 0
                    for i in range(messages_size):
                        message = response.messages.get(i)
                        if message.id > boundary_id:
                            message_obj = self._create_message_object_safely(message)
                            if message_obj:
                                self.processing_queue.put(message_obj)
                                count += 1
                        
                        # Track minimum ID for pagination
                        if min_id_in_batch is None or message.id < min_id_in_batch:
                            min_id_in_batch = message.id
                    
                    new_total = total_queued + count
                    log(f"[{self.id}] Queued {count} unread messages from chat {chat_id} (batch), total so far: {new_total}")
                    
                    # If we got a full batch, there might be more messages
                    if messages_size >= 100 and min_id_in_batch and min_id_in_batch > boundary_id:
                        # Fetch next batch using the minimum ID as offset
                        fetch_batch(min_id_in_batch, new_total)
                    else:
                        log(f"[{self.id}] Completed fetching unread messages for chat {chat_id}. Total: {new_total}")
                
                send_request(req, RequestCallback(on_history_received))
            
            # Start pagination from offset_id = 0 (most recent)
            fetch_batch(0, 0)
            
        except Exception as e:
            log(f"[{self.id}] Error in _process_unread_messages: {traceback.format_exc()}")

    def _should_fetch_next_batch(self, messages_size, oldest_date_in_batch, cutoff_time, min_id_in_batch):
        """Determines if we should fetch the next batch of messages during pagination."""
        # Continue if:
        # 1. We got a full batch (100 messages means there might be more)
        # 2. The oldest message in batch is still within our cutoff time (haven't exceeded time range)
        # 3. We have a valid offset ID to continue from
        return (messages_size >= 100 and 
                oldest_date_in_batch is not None and 
                oldest_date_in_batch >= cutoff_time and 
                min_id_in_batch is not None)

    def _process_historical_messages(self, chat_id, rule, days):
        """Processes historical messages for a specific chat going back N days with pagination."""
        try:
            if rule.get("batch_ignore", False):
                log(f"[{self.id}] Skipping batch processing for chat {chat_id} (batch_ignore=True)")
                return
            
            # Calculate the timestamp for N days ago (using UTC for Telegram compatibility)
            cutoff_time = int((datetime.datetime.utcnow() - datetime.timedelta(days=days)).timestamp())
            
            log(f"[{self.id}] Processing historical messages for chat {chat_id} from last {days} days")
            
            # Implement pagination to fetch all historical messages
            def fetch_batch(offset_id, total_queued):
                req = TLRPC.TL_messages_getHistory()
                req.peer = get_messages_controller().getInputPeer(chat_id)
                req.offset_id = offset_id
                req.offset_date = 0  # Use offset_id for pagination, not offset_date
                req.add_offset = 0
                req.limit = 100  # Max per request
                req.max_id = 0
                req.min_id = 0
                
                def on_history_received(response, error):
                    if error or not response:
                        log(f"[{self.id}] Error fetching history for {chat_id}: {error}")
                        return
                    
                    if not hasattr(response, 'messages') or not response.messages:
                        log(f"[{self.id}] Completed fetching historical messages for chat {chat_id}. Total: {total_queued}")
                        return
                    
                    messages_size = response.messages.size()
                    if messages_size == 0:
                        log(f"[{self.id}] Completed fetching historical messages for chat {chat_id}. Total: {total_queued}")
                        return
                    
                    # Process messages and find the minimum ID and oldest date in batch
                    min_id_in_batch = None
                    oldest_date_in_batch = None
                    count = 0
                    
                    for i in range(messages_size):
                        message = response.messages.get(i)
                        
                        # Check if message is within our time range
                        if message.date >= cutoff_time:
                            message_obj = self._create_message_object_safely(message)
                            if message_obj:
                                self.processing_queue.put(message_obj)
                                count += 1
                        
                        # Track minimum ID for pagination
                        if min_id_in_batch is None or message.id < min_id_in_batch:
                            min_id_in_batch = message.id
                        
                        # Track oldest date
                        if oldest_date_in_batch is None or message.date < oldest_date_in_batch:
                            oldest_date_in_batch = message.date
                    
                    new_total = total_queued + count
                    log(f"[{self.id}] Queued {count} historical messages from chat {chat_id} (batch), total so far: {new_total}")
                    
                    # Continue pagination if we should fetch more messages
                    if self._should_fetch_next_batch(messages_size, oldest_date_in_batch, cutoff_time, min_id_in_batch):
                        # Fetch next batch using the minimum ID as offset
                        fetch_batch(min_id_in_batch, new_total)
                    else:
                        log(f"[{self.id}] Completed fetching historical messages for chat {chat_id}. Total: {new_total}")
                
                send_request(req, RequestCallback(on_history_received))
            
            # Start pagination from offset_id = 0 (most recent)
            fetch_batch(0, 0)
            
        except Exception as e:
            log(f"[{self.id}] Error in _process_historical_messages: {traceback.format_exc()}")

    def _batch_process_all_unread(self):
        """Processes unread messages for all rules that allow batch processing."""
        def process_in_background():
            try:
                count = 0
                for chat_id, rule in self.forwarding_rules.items():
                    if rule.get("enabled", False) and not rule.get("batch_ignore", False):
                        self._process_unread_messages(chat_id, rule)
                        count += 1
                        time.sleep(0.5)  # Small delay between chats
                
                run_on_ui_thread(lambda: BulletinHelper.show_success(f"Queued unread processing for {count} chats"))
            except Exception as e:
                log(f"[{self.id}] Error in batch unread processing: {traceback.format_exc()}")
                error_msg = f"Batch processing error: {str(e)}"
                run_on_ui_thread(lambda msg=error_msg: BulletinHelper.show_error(msg))
        
        # Use exteraGram's recommended run_on_queue for background tasks
        run_on_queue(process_in_background)

    def _batch_process_all_history(self, days):
        """Processes historical messages for all rules that allow batch processing."""
        def process_in_background():
            try:
                count = 0
                for chat_id, rule in self.forwarding_rules.items():
                    if rule.get("enabled", False) and not rule.get("batch_ignore", False):
                        self._process_historical_messages(chat_id, rule, days)
                        count += 1
                        time.sleep(0.5)  # Small delay between chats
                
                run_on_ui_thread(lambda: BulletinHelper.show_success(f"Queued history processing for {count} chats ({days} days)"))
            except Exception as e:
                log(f"[{self.id}] Error in batch history processing: {traceback.format_exc()}")
                error_msg = f"Batch processing error: {str(e)}"
                run_on_ui_thread(lambda msg=error_msg: BulletinHelper.show_error(msg))
        
        # Use exteraGram's recommended run_on_queue for background tasks
        run_on_queue(process_in_background)

    def _clear_pending_queue(self):
        """Clears all pending items in the processing queue."""
        try:
            # Drain the queue properly without race conditions
            cleared_count = 0
            while True:
                try:
                    self.processing_queue.get_nowait()
                    cleared_count += 1
                except queue.Empty:
                    break
            run_on_ui_thread(lambda: BulletinHelper.show_success(f"Queue cleared ({cleared_count} items)"))
            log(f"[{self.id}] Processing queue cleared ({cleared_count} items).")
        except Exception as e:
            log(f"[{self.id}] Error clearing queue: {e}")
            error_msg = f"Error clearing queue: {str(e)}"
            run_on_ui_thread(lambda msg=error_msg: BulletinHelper.show_error(msg))

    def _show_history_days_dialog(self):
        """Shows a dialog to prompt for number of days for historical processing."""
        activity = get_last_fragment().getParentActivity()
        if not activity:
            return
        
        try:
            builder = AlertDialogBuilder(activity)
            builder.set_title("Process Historical Messages")
            builder.set_message("Enter the number of days to look back:")
            
            input_field = EditText(activity)
            input_field.setHint("Days (e.g., 7)")
            input_field.setInputType(InputType.TYPE_CLASS_NUMBER)
            input_field.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
            input_field.setHintTextColor(Theme.getColor(Theme.key_dialogTextHint))
            
            margin_dp = 20
            margin_px = int(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, margin_dp, activity.getResources().getDisplayMetrics()))
            
            container = FrameLayout(activity)
            container.setPadding(margin_px, margin_px // 2, margin_px, margin_px // 2)
            container.addView(input_field)
            
            builder.set_view(container)
            
            def on_ok_click(b, w):
                days_str = input_field.getText().toString().strip()
                try:
                    days = int(days_str)
                    if days > 0:
                        self._batch_process_all_history(days)
                    else:
                        BulletinHelper.show_error("Days must be positive")
                except ValueError:
                    BulletinHelper.show_error("Invalid number")
            
            builder.set_positive_button("OK", on_ok_click)
            builder.set_negative_button("Cancel", None)
            builder.show()
        except Exception:
            log(f"[{self.id}] ERROR showing history days dialog: {traceback.format_exc()}")

    def _start_reply_listener(self, source_id, input_field):
        """Starts listening for a reply to set the destination."""
        self.is_listening_for_reply = True
        self.reply_context = {'source_id': source_id, 'input_field': input_field}
        run_on_ui_thread(lambda: BulletinHelper.show_success("Now go to the destination chat and send 'set'"))