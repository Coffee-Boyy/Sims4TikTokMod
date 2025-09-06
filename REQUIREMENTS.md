Got it ✅ — here’s a **structured requirements document** you can drop into your AI-assisted code editor to scaffold the TikTok Sims 4 Interaction Mod MVP. It captures scope, components, and implementation notes at the right level of detail for an LLM-driven coding workflow.

---

# 📄 Requirements Document: TikTok Sims 4 Interaction Mod (MVP)

## 1. Overview

The goal is to create a **Sims 4 mod** that enables TikTok Live viewers to influence in-game events through gifts. A separate **bridge service** listens for TikTok Live events and communicates them to the Sims 4 mod over localhost. The mod maps these events to in-game actions (buffs, simoleons, object breakage, etc.), with clear player feedback.

---

## 2. System Architecture

```
TikTok Live → Bridge Service (Python/Node) → WebSocket/HTTP → Sims 4 Mod (S4CL-based)
```

### 2.1 Components

1. **Bridge Service**

   * External process.
   * Connects to TikTok Live.
   * Normalizes gift events → JSON.
   * Publishes events over WebSocket or HTTP (localhost).
2. **Sims 4 Mod (`sims_tik_tok_mod`)**

   * Written in Python 3.7, packaged as `.ts4script`.
   * Depends on **Sims 4 Community Library (S4CL)**.
   * Responsibilities:

     * Connect to bridge service.
     * Parse incoming JSON events.
     * Map events to in-game actions.
     * Display notifications for user feedback.

---

## 3. Functional Requirements

### 3.1 Bridge Service

* **Inputs**:

  * TikTok Live gift events (e.g., via TikTokLiveConnector library).
* **Outputs**:

  * JSON payloads sent to mod.
* **Payload schema**:

  ```json
  {
    "user": "string",        // TikTok username
    "gift": "string",        // Gift name e.g. "rose"
    "value": "int",          // Number of gifts
    "timestamp": "string"    // ISO 8601 datetime
  }
  ```
* **Protocol**:

  * WebSocket (`ws://localhost:8765`) or HTTP POST to `http://localhost:8765/event`.

---

### 3.2 Sims 4 Mod

#### 3.2.1 Listener

* Starts on game load.
* Connects to `localhost:8765`.
* Runs background thread to receive JSON events.
* Queues events internally for dispatch.

#### 3.2.2 Action Dispatcher

* Maps `gift` field to in-game actions.
* MVP mapping:

  * **Rose** → +§500 to active household funds.
  * **Heart** → Apply “Happy” buff for 4h to active Sim.
  * **GG** → Break one random household object.
* Extensible via dictionary configuration.

#### 3.2.3 Effects

* **Funds**:

  * Use `CommonHouseholdUtils.add_funds(household, amount)`.
* **Buffs**:

  * Use `CommonBuffUtils.add_buff(sim, buff_id, buff_reason)`.
  * Example: `Buff_Happy_High` for happiness.
* **Object breakage**:

  * Use `CommonObjectUtils.break_object(target_object)` on a random household object.

#### 3.2.4 Notifications

* Every event triggers an in-game popup:

  * Title: `"TikTok Event"`
  * Text: `"CoffeeFan123 sent a Rose 🌹 (+§500)"`
  * Implement via `CommonBasicNotification`.

---

## 4. Non-Functional Requirements

* **Performance**: Listener must not block the game loop. Use threading/async.
* **Stability**: If bridge service is unavailable, mod should fail silently (no crashes).
* **Security**: Only accept localhost connections.
* **Scalability**: Gift-action mappings should be easy to extend later.
* **User Safety**: Rate-limit actions (e.g., 1 action per 2 seconds, cap of 10 actions per minute).

---

## 5. Directory Structure

```
Mods/
  Sims4CommunityLib/
    Sims4CommunityLib.ts4script
  SimsTikTokMod/
    SimsTikTokMod.ts4script
      sims_tik_tok_mod/
        __init__.py
        modinfo.py
        listener.py
        dispatcher.py
        actions/
          funds.py
          buffs.py
          objects.py
        notifications/
          notifier.py
```

---

## 6. Example Code Stubs

### 6.1 Dispatcher Mapping

```python
ACTION_MAP = {
    "rose": lambda user, value: FundsActions.add_money(500 * value, user),
    "heart": lambda user, value: BuffActions.add_happy_buff(duration=240, user=user),
    "gg": lambda user, value: ObjectActions.break_random_object(user=user)
}
```

### 6.2 Notification Example

```python
from sims4communitylib.notifications.common_basic_notification import CommonBasicNotification

def notify(user: str, gift: str, effect: str):
    CommonBasicNotification(
        title="TikTok Event",
        description=f"{user} sent {gift}! {effect}"
    ).show()
```

---

## 7. Milestones (MVP)

1. **Bridge Service**:

   * Connect to TikTok.
   * Publish JSON events to localhost.
2. **Sims Mod Skeleton**:

   * Load mod.
   * Log “Hello World”.
3. **Listener**:

   * Connect to bridge service.
   * Print incoming events to log.
4. **Dispatcher**:

   * Implement Rose → +§500.
   * Implement Heart → Happy buff.
   * Implement GG → Break object.
5. **Notifications**:

   * Show per-event confirmation in-game.
6. **Safety Rails**:

   * Add cooldown/rate limits.

---

## 8. Future Enhancements (beyond MVP)

* Config-driven action mapping (JSON file).
* Persistent progression (store viewer stats).
* Angel/Gremlin dual-meter system.
* In-game UI panel for live meters.
* AI-driven narrator (TTS reactions).
* Multi-household support.

---

Would you like me to **flesh this into a starter repo** (bridge script + mod skeleton with listener/dispatcher files already wired), so you can just feed it to your AI editor and start iterating?
