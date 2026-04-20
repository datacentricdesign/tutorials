// ─────────────────────────────────────────────────────────────────────────────
// Sedentary Detector — Data Foundry Script
//
// Triggered automatically on each incoming OOCSI message from the eSense
// browser page. Checks whether the most recent windows form an unbroken
// "still" streak long enough to warrant a reminder, and if so sends one
// trigger event to the actuator channel.
//
// Pipeline:
//   eSense (BLE) → browser → OOCSI → [this script] → OOCSI → ESP32
// ─────────────────────────────────────────────────────────────────────────────

// ── Configuration ─────────────────────────────────────────────────────────────
// Fill these in to match your Data Foundry project settings.

const ACTUATOR_CHANNEL = 'your-esp32-channel';   // must match oocsi_actuator_channel in settings.py

// activity_score (std dev of accel magnitude, in g) below which a window
// is classified as "still". Calibrate after watching a few minutes of data.
const STILL_THRESHOLD  = 0.02;

// Number of consecutive still windows that trigger the alert.
// With the default browser window of 2 s: 150 × 2 s = 5 minutes.
const STILL_TO_TRIGGER = 150;

// ── Script body ───────────────────────────────────────────────────────────────
// Everything below runs once per incoming message. `data` holds the fields
// of the current OOCSI event (activity_score, samples, device_id, …).

// Skip windows with too few samples — BLE dropout or a cut-short window.
if (data.samples < 10) return;

// Retrieve the last STILL_TO_TRIGGER stored windows from the IoT dataset.
// The current event may not be stored yet, so it is counted separately below.
// Events are returned most-recent-first.
var recent = DF.eventData.get('', STILL_TO_TRIGGER);

// Count the unbroken "still" streak ending at the current window.
var streak = (data.activity_score < STILL_THRESHOLD) ? 1 : 0;

if (streak > 0) {
  for (var i = 0; i < recent.length; i++) {
    if (recent[i].activity_score < STILL_THRESHOLD && recent[i].samples >= 10) {
      streak++;
    } else {
      break;  // streak is broken — stop counting
    }
  }
}

DF.print('Still streak: ' + streak + ' windows (' + (streak * 2) + ' s)');

// Trigger exactly when the streak first reaches the threshold.
// Using === rather than >= means the alert fires once at the crossing point.
// If the person stays still, streak grows beyond STILL_TO_TRIGGER and the
// condition is no longer true — no re-firing. Once movement breaks the streak,
// the detector re-arms automatically: the next crossing will fire again.
if (streak === STILL_TO_TRIGGER) {
  DF.oocsi(ACTUATOR_CHANNEL, {
    event:   'sedentary_alert',
    still_s: streak * 2,
  });
  DF.print('Alert sent after ' + (streak * 2) + ' s of stillness.');
}
