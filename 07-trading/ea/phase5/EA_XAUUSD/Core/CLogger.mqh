
//+------------------------------------------------------------------+
//| XAUUSD Institutional EA — Logger                                  |
//| File: Core/CLogger.mqh                                            |
//| Purpose: All logging across all modules — severity hierarchy,     |
//|           file write, CSV trade export, log rotation              |
//| Phase: 1 — Core Framework                                         |
//+------------------------------------------------------------------+
#ifndef CLOGGER_MQH
#define CLOGGER_MQH
#include "../Include/Defines.mqh"

//===================================================================
// PSEUDO-CODE DESIGN
//
// Every module calls Logger.Write(level, module_name, message, kvpairs)
// Logger decides whether to write based on minimum active level.
// TRACE and DEBUG are compile-time disabled in production.
// CRITICAL level triggers Print() to MT5 Experts tab AND alert.
// FATAL level triggers Print() + halts EA.
//
// Two output streams:
//   1. EA_XAUUSD_log.txt — all events with severity + timestamp
//   2. trade_log.csv     — one row per completed trade (16 columns)
//
// Log rotation at LOG_FILE_MAX_BYTES (10MB).
// Keeps LOG_FILE_KEEP_COUNT (5) rotated files.
//
// File handles held open during EA lifetime — not opened/closed
// per line (would be extremely slow on a 1-tick EA).
// OnDeinit() flushes and closes all handles.
//===================================================================

class CLogger
{
private:
   //--- State
   LOG_LEVEL         m_min_level;
   bool              m_production_mode;
   string            m_log_filename;
   string            m_csv_filename;
   int               m_log_handle;
   int               m_csv_handle;
   bool              m_initialized;
   long              m_log_bytes_written;

   //--- Internal helpers
   string LevelString(LOG_LEVEL level)
   {
      switch(level)
      {
         case LOG_TRACE:    return "[TRACE]   ";
         case LOG_DEBUG:    return "[DEBUG]   ";
         case LOG_INFO:     return "[INFO]    ";
         case LOG_WARN:     return "[WARN]    ";
         case LOG_ERROR:    return "[ERROR]   ";
         case LOG_CRITICAL: return "[CRITICAL]";
         case LOG_FATAL:    return "[FATAL]   ";
         default:           return "[UNKNOWN] ";
      }
   }

   string Timestamp()
   {
      // Format: YYYY.MM.DD HH:MM:SS
      MqlDateTime dt;
      TimeToStruct(TimeCurrent(), dt);
      return StringFormat("%04d.%02d.%02d %02d:%02d:%02d",
         dt.year, dt.mon, dt.day, dt.hour, dt.min, dt.sec);
   }

   bool OpenHandles()
   {
      // PSEUDO-CODE:
      // Try to open or create both log files.
      // Log file: append mode (SEEK_END) — accumulate events.
      // CSV file: if new, write header row first.
      // If either handle fails: Print() to Experts tab as fallback.

      // audit 27 Nov: FILE_READ added - FILE_WRITE alone truncates, so every restart wiped the log
      m_log_handle = FileOpen(m_log_filename,
                              FILE_READ|FILE_WRITE|FILE_TXT|FILE_SHARE_READ|FILE_ANSI,
                              '\n');
      if(m_log_handle == INVALID_HANDLE)
      {
         Print("[LOGGER INIT FAIL] Cannot open log file: ", m_log_filename);
         return false;
      }

      // Seek to end for append behavior
      FileSeek(m_log_handle, 0, SEEK_END);

      // CSV file
      bool csv_new = !FileIsExist(m_csv_filename);
      m_csv_handle = FileOpen(m_csv_filename,
                              FILE_READ|FILE_WRITE|FILE_CSV|FILE_SHARE_READ|FILE_ANSI,   // audit 27 Nov: keep old trades
                              ',');
      if(m_csv_handle == INVALID_HANDLE)
      {
         Print("[LOGGER INIT FAIL] Cannot open CSV file: ", m_csv_filename);
         FileClose(m_log_handle);
         m_log_handle = INVALID_HANDLE;
         return false;
      }

      FileSeek(m_csv_handle, 0, SEEK_END);

      // Write CSV header if file is new
      if(csv_new)
         WriteCsvHeader();

      return true;
   }

   void WriteCsvHeader()
   {
      // 16 columns matching trade_log.csv specification
      string header = "ticket,open_time,close_time,direction,lot,entry_price,"
                      "sl_price,tp1_price,tp2_price,close_price,pnl,"
                      "rr_achieved,score,regime,session,duration_min,close_reason";
      FileWriteString(m_csv_handle, header + "\n");
   }

   void RotateLog()
   {
      // PSEUDO-CODE:
      // 1. Close current handle.
      // 2. Rename current file to EA_XAUUSD_log_YYYYMMDD_HHMMSS.txt
      // 3. Delete oldest rotated file if count >= LOG_FILE_KEEP_COUNT
      // 4. Re-open fresh log file.
      FileClose(m_log_handle);
      m_log_handle = INVALID_HANDLE;

      MqlDateTime dt;
      TimeToStruct(TimeCurrent(), dt);
      string archived = StringFormat("EA_XAUUSD_log_%04d%02d%02d_%02d%02d%02d.txt",
                                     dt.year, dt.mon, dt.day,
                                     dt.hour, dt.min, dt.sec);
      // audit 27 Nov: keep the full log as the archive (FileMove), then start a new file.
      //    If the move fails, the reopen below (no FILE_READ) truncates as before.
      if(!FileMove(m_log_filename, 0, archived, FILE_REWRITE))
         Print("[LOGGER] archive move failed err=", GetLastError(), " - log truncated");
      m_log_bytes_written = 0;

      m_log_handle = FileOpen(m_log_filename,
                              FILE_WRITE|FILE_TXT|FILE_SHARE_READ|FILE_ANSI,
                              '\n');
      if(m_log_handle != INVALID_HANDLE)
         FileSeek(m_log_handle, 0, SEEK_END);
      else
         Print("[LOGGER] Rotation failed — log writes will go to Experts tab only");
   }

public:
   //--- Constructor
   CLogger() :
      m_min_level(LOG_INFO),
      m_production_mode(true),
      m_log_filename("EA_XAUUSD_log.txt"),
      m_csv_filename("EA_XAUUSD_trades.csv"),
      m_log_handle(INVALID_HANDLE),
      m_csv_handle(INVALID_HANDLE),
      m_initialized(false),
      m_log_bytes_written(0)
   {}

   //--- Destructor
   ~CLogger()
   {
      Shutdown();
   }

   //--- Initialize with configuration
   bool Init(bool production_mode, LOG_LEVEL min_level = LOG_INFO)
   {
      m_production_mode = production_mode;
      m_min_level       = production_mode ? LOG_INFO : LOG_DEBUG;
      if(min_level > m_min_level)
         m_min_level = min_level;

      if(!OpenHandles())
         return false;

      m_initialized = true;

      // Write boot banner
      Write(LOG_INFO, "LOGGER", "=== EA BOOT ===",
            StringFormat("version=%s build=%s symbol=%s",
                         EA_VERSION, EA_BUILD_DATE, EA_SYMBOL));
      return true;
   }

   //--- Core write method
   //    module: "ENTRY", "GUARD", "EQUITY", etc.
   //    message: human-readable description
   //    context: key=value pairs for machine parsing
   void Write(LOG_LEVEL level, string module, string message,
              string context = "")
   {
      // PSEUDO-CODE:
      // 1. Check if level passes minimum threshold.
      //    In production: TRACE and DEBUG are compiled out via #ifndef.
      //    At runtime: levels below m_min_level are skipped.
      // 2. Format: [LEVEL] [timestamp] [MODULE] message {context}
      // 3. Write to file (if handle valid).
      // 4. Always Print() for CRITICAL and above.
      // 5. Rotate log if size threshold exceeded.

      #ifndef DEBUG_MODE
         if(level <= LOG_DEBUG) return;
      #endif
      if(level < m_min_level) return;

      string ts   = Timestamp();
      string lvl  = LevelString(level);
      string line = StringFormat("%s %s [%-12s] %s", lvl, ts, module, message);
      if(context != "")
         line += "  {" + context + "}";

      // Write to file
      if(m_log_handle != INVALID_HANDLE)
      {
         int bytes = (int)FileWriteString(m_log_handle, line + "\n");
         m_log_bytes_written += bytes;

         // Check rotation threshold
         if(m_log_bytes_written >= LOG_FILE_MAX_BYTES)
            RotateLog();
      }

      // CRITICAL and above always go to MT5 Experts tab
      if(level >= LOG_CRITICAL)
      {
         Print(line);
         // TODO Phase 8: Dashboard alert integration
      }
   }

   //--- Convenience wrappers for each level
   void Info(string module, string msg, string ctx = "")
      { Write(LOG_INFO,    module, msg, ctx); }
   void Warn(string module, string msg, string ctx = "")
      { Write(LOG_WARN,    module, msg, ctx); }
   void Error(string module, string msg, string ctx = "")
      { Write(LOG_ERROR,   module, msg, ctx); }
   void Critical(string module, string msg, string ctx = "")
      { Write(LOG_CRITICAL, module, msg, ctx); }
   void Fatal(string module, string msg, string ctx = "")
      { Write(LOG_FATAL,   module, msg, ctx); }
   void Debug(string module, string msg, string ctx = "")
      { Write(LOG_DEBUG,   module, msg, ctx); }

   //--- Write completed trade to CSV
   //    Called once when a trade closes (from TradeManager)
   void WriteTrade(
      ulong     ticket,
      datetime  open_time,
      datetime  close_time,
      TRADE_DIR direction,
      double    lot,
      double    entry_price,
      double    sl_price,
      double    tp1_price,
      double    tp2_price,
      double    close_price,
      double    pnl,
      double    rr_achieved,
      int       score_x10,
      REGIME_STATE regime,
      SESSION_STATE session,
      int       duration_min,
      CLOSE_REASON close_reason)
   {
      if(m_csv_handle == INVALID_HANDLE) return;

      string dir_str    = (direction == DIR_LONG) ? "BUY" : "SELL";
      string regime_str = EnumToString(regime);
      string sess_str   = EnumToString(session);
      string reason_str = EnumToString(close_reason);

      string row = StringFormat(
         "%llu,%s,%s,%s,%.2f,%.5f,%.5f,%.5f,%.5f,%.5f,%.2f,%.2f,%.1f,%s,%s,%d,%s",
         ticket,
         TimeToString(open_time, TIME_DATE|TIME_MINUTES|TIME_SECONDS),
         TimeToString(close_time, TIME_DATE|TIME_MINUTES|TIME_SECONDS),
         dir_str,
         lot,
         entry_price,
         sl_price,
         tp1_price,
         tp2_price,
         close_price,
         pnl,
         rr_achieved,
         (double)score_x10 / 10.0,
         regime_str,
         sess_str,
         duration_min,
         reason_str
      );

      FileWriteString(m_csv_handle, row + "\n");

      // Also write to main log at INFO level
      Write(LOG_INFO, "TRADE_LOG",
            StringFormat("Trade closed %s pnl=%.2f rr=%.2f reason=%s",
                         dir_str, pnl, rr_achieved, reason_str),
            StringFormat("ticket=%llu duration_min=%d score=%.1f",
                         ticket, duration_min, (double)score_x10/10.0));
   }

   //--- Flush all pending writes (call from OnDeinit)
   void Flush()
   {
      if(m_log_handle != INVALID_HANDLE) FileFlush(m_log_handle);
      if(m_csv_handle != INVALID_HANDLE) FileFlush(m_csv_handle);
   }

   //--- Clean shutdown
   void Shutdown()
   {
      if(!m_initialized) return;
      Write(LOG_INFO, "LOGGER", "=== EA SHUTDOWN ===");
      Flush();
      if(m_log_handle != INVALID_HANDLE)
      {
         FileClose(m_log_handle);
         m_log_handle = INVALID_HANDLE;
      }
      if(m_csv_handle != INVALID_HANDLE)
      {
         FileClose(m_csv_handle);
         m_csv_handle = INVALID_HANDLE;
      }
      m_initialized = false;
   }

   //--- Check if logger is operational
   bool IsReady() const { return m_initialized; }
};

//--- Global singleton instance (accessed by all modules)
CLogger Logger;

#endif // CLOGGER_MQH
