"""Turn the robot's journal into a compact timeline of what it did. Reads `journalctl -o json`
lines on stdin (rover.service events and rover-deploy records); prints one row per thing that
matters, with the wall-clock time:

  mode changes, explore steps, bench modes, guard states, deadman stops, faults, overruns,
  starts, stops, deploys; runs of identical drive commands folded into one row; health only when
  something is off (power flags, ping errors, slow ticks), plus a summary at the end.

Used by `tools/bench timeline [--since 15m]`.
"""
import json
import sys
from datetime import datetime

SLOW_TICK_MS = 5.0


def wall(entry):
    return datetime.fromtimestamp(int(entry["__REALTIME_TIMESTAMP"]) / 1e6).strftime("%H:%M:%S.%f")[:-4]


def describe(e):
    ev = e.get("event")
    if ev == "start":
        return f"service start  commit {str(e.get('commit', ''))[:7]}"
    if ev == "stop":
        return "service stop"
    if ev == "settings":
        return "settings " + " ".join(f"{k}={v:g}" for k, v in e.items() if k not in ("t", "event"))
    if ev == "deploy":
        return f"DEPLOY {str(e.get('commit', ''))[:7]} from {e.get('from')}"
    if ev == "mode_change":
        return f"mode {e.get('from')} -> {e.get('to')}  ({e.get('source')})"
    if ev == "explore":
        extra = {k: v for k, v in e.items() if k not in ("t", "event", "state")}
        return f"  explore {e.get('state')}" + (f"  {extra}" if extra else "")
    if ev == "bench_mode":
        if e.get("mode"):
            return f"bench mode {e['mode']} for {e.get('seconds')} s"
        return f"bench mode {e.get('ended')} ended ({e.get('reason')})"
    if ev == "obstacle_limit":
        d = e.get("distance")
        return f"  guard {e.get('state')}" + (f" at {d * 100:.0f} cm" if d is not None else "") + \
            f", forward limit {e.get('limit'):.2f}"
    if ev == "deadman_stop":
        return "  deadman stop (commands stopped)"
    if ev == "fault":
        return f"FAULT {e.get('error')}"
    if ev == "tick_overrun":
        return f"tick overrun {e.get('elapsed', 0) * 1000:.1f} ms"
    return None


def main():
    rows, drive, health = [], None, []
    for line in sys.stdin:
        try:
            entry = json.loads(line)
            e = json.loads(entry.get("MESSAGE", ""))
        except (ValueError, TypeError):
            continue
        if not isinstance(e, dict):
            continue
        when = wall(entry)
        if e.get("event") == "drive":
            key = (e.get("left"), e.get("right"), e.get("source"))
            if drive and drive["key"] == key and e.get("t", 0) - drive["last"] < 0.5:
                drive["n"], drive["last"] = drive["n"] + 1, e.get("t", 0)
                continue
            if drive:
                rows.append(drive_row(drive))
            drive = {"key": key, "when": when, "n": 1, "first": e.get("t", 0), "last": e.get("t", 0)}
            continue
        if e.get("event") == "health":
            health.append(e)
            off = []
            if e.get("throttle_flags"):
                off.append("POWER " + ",".join(e["throttle_flags"]))
            if e.get("ping_errors"):
                flip = f", flip p50/max {e.get('flip_us_p50')}/{e.get('flip_us_max')} us" if e.get("flip_us_max") else ""
                off.append(f"ping errors {e['ping_errors']} of {e.get('pings')}{flip}")
            if (e.get("tick_ms_max") or 0) > SLOW_TICK_MS:
                off.append(f"slow tick {e['tick_ms_max']} ms")
            if off:
                rows.append((when, "  health: " + "; ".join(off)))
            continue
        text = describe(e)
        if text:
            if drive:
                rows.append(drive_row(drive))
                drive = None
            rows.append((when, text))
    if drive:
        rows.append(drive_row(drive))
    for when, text in rows:
        print(f"{when}  {text}")
    if health:
        temps = [h["cpu_temp"] for h in health if h.get("cpu_temp") is not None]
        flags = sorted({f for h in health for f in h.get("throttle_flags") or []})
        p99 = max((h.get("tick_ms_p99") or 0) for h in health)
        pings = sum(h.get("pings") or 0 for h in health)
        errs = sum(sum((h.get("ping_errors") or {}).values()) for h in health)
        print(f"-- health over {len(health) * 5} s: cpu {min(temps):.0f}-{max(temps):.0f} C, "
              f"power {'FLAGS ' + ','.join(flags) if flags else 'ok'}, tick p99 max {p99} ms, "
              f"pings {pings} with {errs} errors ({100 * errs / max(pings, 1):.1f}%)")
    if not rows:
        print("no robot events in that window")


def drive_row(d):
    left, right, source = d["key"]
    span = d["last"] - d["first"]
    return d["when"], f"drive {left} {right} ({source})" + (f" x{d['n']} over {span:.1f} s" if d["n"] > 1 else "")


if __name__ == "__main__":
    main()
