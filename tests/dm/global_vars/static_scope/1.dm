
var/gvar = 3

/obj
    var/static/osvar = gvar

/proc/sproc()
    var/static/psvar = gvar
    LOG("psvar", psvar)

/proc/main()
    var/obj/o = new
    LOG("osvar", o.osvar)
    return