

//# issue 682

#define ISDEF 1
#ifdef ISDEF
#define LOG_DEF 1
#else
# define LOG_DEF 0
#endif

/proc/main()
  LOG("a", LOG_DEF)