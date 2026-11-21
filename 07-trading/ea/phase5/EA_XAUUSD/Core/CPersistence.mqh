
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — File Persistence Framework             |
//| File: Core/CPersistence.mqh                                       |
//| Purpose: Read/write critical state to disk.                       |
//|           position_state.txt — active trade (orphan recovery)     |
//|           daily_stats.txt    — daily P&L, trade count             |
//|           performance.txt    — rolling performance data           |
//| Phase: 1 — Core Framework                                         |
//+------------------------------------------------------------------+
#ifndef CPERSISTENCE_MQH
#define CPERSISTENCE_MQH
#include "../Include/Defines.mqh"
#include "CLogger.mqh"

//===================================================================
// PSEUDO-CODE DESIGN
//
// PROBLEM: EA crash or VPS reboot loses all in-memory state.
//   On restart: no open position data, no daily stats, nothing.
//
// SOLUTION: Write critical state to disk on every state change.
//   Three files:
//
//   1. position_state.txt
//      Written: every time trade state changes (open, partial, BE, etc.)
//      Read:    on EA init to detect orphaned positions
//      Deleted: when trade closes cleanly
//      Content: TradeState struct serialised as INI-style key=value
//      Rule:    NEVER delete this file while position is open
//
//   2. daily_stats.txt
//      Written: after every trade close + at day rollover (00:01 GMT)
//      Read:    on EA init to restore today's trade count, P&L
//      Content: DailyStats struct
//      Rule:    If date doesn't match today, treat as yesterday and reset
//
//   3. heartbeat.txt
//      Written: every 60 seconds via OnTimer
//      Content: timestamp, equity, state — single line, overwritten
//      NOT READ back — used by external monitoring only
//
// File format: simple key=value pairs, one per line.
// No XML, no JSON — keep it readable and crash-resilient.
// A partial write leaves the previous complete version readable.
//===================================================================

#define POSITION_FILE   "EA_XAUUSD_position.txt"
#define DAILY_FILE      "EA_XAUUSD_daily.txt"
#define HEARTBEAT_FILE  "EA_XAUUSD_heartbeat.txt"
#define DAYS_FILE       "EA_XAUUSD_days.txt"        // A336: per-day midnight snapshots

class CPersistence
{
private:
   bool m_initialized;

   //--- Write a key=value pair to an open file handle
   void WriteKV(int handle, string key, string value)
   {
      FileWriteString(handle, key + "=" + value + "\n");
   }

   //--- Read all key=value pairs from file into a string array
   //    Returns number of pairs read
   int ReadKVFile(string filename, string &keys[], string &vals[])
   {
      if(!FileIsExist(filename)) return 0;

      int handle = FileOpen(filename,
                            FILE_READ|FILE_TXT|FILE_SHARE_WRITE|FILE_ANSI,
                            '\n');
      if(handle == INVALID_HANDLE) return 0;

      ArrayResize(keys, 0);
      ArrayResize(vals, 0);
      int count = 0;

      while(!FileIsEnding(handle))
      {
         string line = FileReadString(handle);
         StringTrimRight(line);
         StringTrimLeft(line);
         if(StringLen(line) == 0) continue;

         int sep = StringFind(line, "=");
         if(sep < 1) continue;

         ArrayResize(keys, count + 1);
         ArrayResize(vals, count + 1);
         keys[count] = StringSubstr(line, 0, sep);
         vals[count] = StringSubstr(line, sep + 1);
         count++;
      }
      FileClose(handle);
      return count;
   }

   //--- Find value for key in loaded KV pairs
   string GetKV(string &keys[], string &vals[], string key,
                string default_val = "")
   {
      for(int i = 0; i < ArraySize(keys); i++)
         if(keys[i] == key) return vals[i];
      return default_val;
   }

public:
   // Writes are synchronous (each Write* opens+closes). Flush is a no-op
   // provided for API symmetry with Logger.Flush().
   void Flush() { }

   CPersistence() : m_initialized(false) {}

   bool Init()
   {
      m_initialized = true;
      Logger.Info("PERSIST", "File persistence layer initialized",
         StringFormat("position=%s daily=%s heartbeat=%s",
                      POSITION_FILE, DAILY_FILE, HEARTBEAT_FILE));
      return true;
   }

   //=== POSITION STATE ===

   //--- Write current trade state to disk (call on every state change)
   bool WritePosition(const TradeState &ts)
   {
      int h = FileOpen(POSITION_FILE,
                       FILE_WRITE|FILE_TXT|FILE_SHARE_READ|FILE_ANSI,
                       '\n');
      if(h == INVALID_HANDLE)
      {
         Logger.Error("PERSIST", "Cannot write position_state file");
         return false;
      }

      WriteKV(h, "ticket",        IntegerToString(ts.ticket));
      WriteKV(h, "direction",     IntegerToString((int)ts.direction));
      WriteKV(h, "lot_size",      DoubleToString(ts.lot_size, 2));
      WriteKV(h, "entry_price",   DoubleToString(ts.entry_price, 5));
      WriteKV(h, "sl_price",      DoubleToString(ts.sl_price, 5));
      WriteKV(h, "sl_original",   DoubleToString(ts.sl_original, 5));
      WriteKV(h, "sl_pips",       DoubleToString(ts.sl_pips, 1));
      WriteKV(h, "tp1_price",     DoubleToString(ts.tp1_price, 5));
      WriteKV(h, "tp2_price",     DoubleToString(ts.tp2_price, 5));
      WriteKV(h, "partial_done",  IntegerToString(ts.partial_done ? 1 : 0));
      WriteKV(h, "trail_active",  IntegerToString(ts.trail_active ? 1 : 0));
      WriteKV(h, "at_breakeven",  IntegerToString(ts.at_breakeven ? 1 : 0));
      WriteKV(h, "open_time",     IntegerToString(ts.open_time));
      WriteKV(h, "score",         IntegerToString(ts.score));
      WriteKV(h, "regime",        IntegerToString((int)ts.regime));
      WriteKV(h, "session",       IntegerToString((int)ts.session));
      WriteKV(h, "write_time",    IntegerToString(TimeCurrent()));

      FileClose(h);
      return true;
   }

   //--- Read position state back from disk
   //    Returns false if file doesn't exist or is corrupted
   bool ReadPosition(TradeState &ts)
   {
      if(!FileIsExist(POSITION_FILE)) return false;

      string keys[], vals[];
      int n = ReadKVFile(POSITION_FILE, keys, vals);
      if(n < 10)
      {
         Logger.Warn("PERSIST", "Position file corrupt or incomplete",
                     StringFormat("pairs_found=%d", n));
         return false;
      }

      ts.ticket       = (ulong)StringToInteger(GetKV(keys,vals,"ticket","0"));
      ts.direction    = (TRADE_DIR)(int)StringToInteger(GetKV(keys,vals,"direction","0"));
      ts.lot_size     = StringToDouble(GetKV(keys,vals,"lot_size","0"));
      ts.entry_price  = StringToDouble(GetKV(keys,vals,"entry_price","0"));
      ts.sl_price     = StringToDouble(GetKV(keys,vals,"sl_price","0"));
      ts.sl_original  = StringToDouble(GetKV(keys,vals,"sl_original","0"));
      ts.sl_pips      = StringToDouble(GetKV(keys,vals,"sl_pips","0"));
      ts.tp1_price    = StringToDouble(GetKV(keys,vals,"tp1_price","0"));
      ts.tp2_price    = StringToDouble(GetKV(keys,vals,"tp2_price","0"));
      ts.partial_done = (GetKV(keys,vals,"partial_done","0") == "1");
      ts.trail_active = (GetKV(keys,vals,"trail_active","0") == "1");
      ts.at_breakeven = (GetKV(keys,vals,"at_breakeven","0") == "1");
      ts.open_time    = (datetime)StringToInteger(GetKV(keys,vals,"open_time","0"));
      ts.score        = (int)StringToInteger(GetKV(keys,vals,"score","0"));
      ts.regime       = (REGIME_STATE)(int)StringToInteger(GetKV(keys,vals,"regime","0"));
      ts.session      = (SESSION_STATE)(int)StringToInteger(GetKV(keys,vals,"session","0"));

      // Validate minimum viable data
      if(ts.ticket == 0 || ts.entry_price <= 0 || ts.sl_price <= 0)
      {
         Logger.Warn("PERSIST", "Position file has zero/invalid critical fields");
         return false;
      }

      Logger.Info("PERSIST", "Position state restored from disk",
         StringFormat("ticket=%llu entry=%.5f sl=%.5f",
                      ts.ticket, ts.entry_price, ts.sl_price));
      return true;
   }

   //--- Delete position file (call after clean close)
   void ClearPosition()
   {
      if(FileIsExist(POSITION_FILE))
      {
         FileDelete(POSITION_FILE);
         Logger.Info("PERSIST", "Position state file cleared");
      }
   }

   //=== DAILY STATS ===

   bool WriteDaily(const DailyStatsData &ds)
   {
      int h = FileOpen(DAILY_FILE,
                       FILE_WRITE|FILE_TXT|FILE_SHARE_READ|FILE_ANSI,
                       '\n');
      if(h == INVALID_HANDLE)
      {
         Logger.Error("PERSIST", "Cannot write daily_stats file");
         return false;
      }

      WriteKV(h, "reset_date",    IntegerToString(ds.reset_date));
      WriteKV(h, "open_equity",   DoubleToString(ds.open_equity, 2));     // day base (A336)
      WriteKV(h, "start_balance", DoubleToString(ds.start_balance, 2));   // A336
      WriteKV(h, "forced_limit",  IntegerToString(ds.forced_limit ? 1 : 0)); // A336
      WriteKV(h, "closed_pnl",    DoubleToString(ds.closed_pnl, 2));
      WriteKV(h, "peak_equity",   DoubleToString(ds.peak_equity, 2));
      WriteKV(h, "min_equity",    DoubleToString(ds.min_equity, 2));
      WriteKV(h, "trade_count",   IntegerToString(ds.trade_count));
      WriteKV(h, "wins",          IntegerToString(ds.wins));
      WriteKV(h, "losses",        IntegerToString(ds.losses));
      WriteKV(h, "consec_losses", IntegerToString(ds.consec_losses));
      WriteKV(h, "last_close",    IntegerToString(ds.last_close_time));

      FileClose(h);
      return true;
   }

   //--- Read daily stats — if date doesn't match today, return false
   //    (caller should then reset to fresh DailyStats)
   bool ReadDaily(DailyStatsData &ds)
   {
      if(!FileIsExist(DAILY_FILE)) return false;

      string keys[], vals[];
      int n = ReadKVFile(DAILY_FILE, keys, vals);
      if(n < 5) return false;

      ds.reset_date     = (datetime)StringToInteger(GetKV(keys,vals,"reset_date","0"));
      ds.open_equity    = StringToDouble(GetKV(keys,vals,"open_equity","0"));
      ds.start_balance  = StringToDouble(GetKV(keys,vals,"start_balance","0"));
      ds.forced_limit   = (GetKV(keys,vals,"forced_limit","0") == "1");
      ds.closed_pnl     = StringToDouble(GetKV(keys,vals,"closed_pnl","0"));
      ds.peak_equity    = StringToDouble(GetKV(keys,vals,"peak_equity","0"));
      ds.min_equity     = StringToDouble(GetKV(keys,vals,"min_equity","0"));
      ds.trade_count    = (int)StringToInteger(GetKV(keys,vals,"trade_count","0"));
      ds.wins           = (int)StringToInteger(GetKV(keys,vals,"wins","0"));
      ds.losses         = (int)StringToInteger(GetKV(keys,vals,"losses","0"));
      ds.consec_losses  = (int)StringToInteger(GetKV(keys,vals,"consec_losses","0"));
      ds.last_close_time = (datetime)StringToInteger(GetKV(keys,vals,"last_close","0"));

      // A336 (#1): the file's reset_date is a SERVER date, so compare with the SERVER date
      //            (TimeGMT() here threw the file away for 2-3 h after every server midnight)
      MqlDateTime today, file_date;
      TimeToStruct(TimeTradeServer(), today);
      TimeToStruct(ds.reset_date, file_date);

      bool same_day = (today.year == file_date.year &&
                       today.mon  == file_date.mon  &&
                       today.day  == file_date.day);

      if(!same_day)
      {
         Logger.Info("PERSIST", "Daily stats file is from previous day — will reset");
         return false; // Trigger fresh day
      }

      Logger.Info("PERSIST", "Daily stats restored",
         StringFormat("trades=%d closed_pnl=%.2f", ds.trade_count, ds.closed_pnl));
      return true;
   }

   //=== A336 (#13): PER-DAY MIDNIGHT SNAPSHOTS (official The5%ers profitable-day formula) ===
   //    One line per closed server day: day=<date>;<start_balance>;<end_balance>;<end_equity>
   //    Appended at each server-midnight rollover. Equity at midnight cannot be rebuilt from
   //    history, so it is recorded live.
   bool AppendDaySnapshot(datetime day, double start_bal, double end_bal, double end_eq)
   {
      int h = FileOpen(DAYS_FILE, FILE_READ|FILE_WRITE|FILE_TXT|FILE_SHARE_READ|FILE_ANSI, '\n');
      if(h == INVALID_HANDLE)
      {
         Logger.Error("PERSIST", "Cannot open day snapshot file");
         return false;
      }
      FileSeek(h, 0, SEEK_END);
      FileWriteString(h, StringFormat("day=%I64d;%.2f;%.2f;%.2f\n", (long)day, start_bal, end_bal, end_eq));
      FileClose(h);
      return true;
   }

   //--- Returns the number of snapshots read (arrays oldest first, as written)
   int ReadDaySnapshots(datetime &days[], double &start_bal[], double &end_bal[], double &end_eq[])
   {
      ArrayResize(days, 0); ArrayResize(start_bal, 0); ArrayResize(end_bal, 0); ArrayResize(end_eq, 0);
      string keys[], vals[];
      int n = ReadKVFile(DAYS_FILE, keys, vals);
      int m = 0;
      ushort sep = StringGetCharacter(";", 0);
      for(int i = 0; i < n; i++)
      {
         if(keys[i] != "day") continue;
         string parts[];
         if(StringSplit(vals[i], sep, parts) != 4) continue;
         datetime d = (datetime)StringToInteger(parts[0]);
         if(d <= 0) continue;
         ArrayResize(days, m + 1); ArrayResize(start_bal, m + 1); ArrayResize(end_bal, m + 1); ArrayResize(end_eq, m + 1);
         days[m]      = d;
         start_bal[m] = StringToDouble(parts[1]);
         end_bal[m]   = StringToDouble(parts[2]);
         end_eq[m]    = StringToDouble(parts[3]);
         m++;
      }
      return m;
   }

   //=== HEARTBEAT ===
   //    Called every 60 seconds — lightweight, single line overwrite

   void WriteHeartbeat(EA_STATE state, double equity, SUSPEND_REASON suspend)
   {
      int h = FileOpen(HEARTBEAT_FILE,
                       FILE_WRITE|FILE_TXT|FILE_SHARE_READ|FILE_ANSI,
                       '\n');
      if(h == INVALID_HANDLE) return;

      string line = StringFormat("ALIVE state=%s equity=%.2f "
                                 "suspend=%s time=%s",
                                 EnumToString(state),
                                 equity,
                                 EnumToString(suspend),
                                 TimeToString(TimeCurrent(),
                                              TIME_DATE|TIME_SECONDS));
      FileWriteString(h, line + "\n");
      FileClose(h);
   }

   bool IsReady() const { return m_initialized; }
};

//--- Global singleton
CPersistence Persistence;

#endif // CPERSISTENCE_MQH
