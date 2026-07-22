@sensor(target=the_job)
def logs_then_skips(context):
    context.log.info("Logging from a sensor!")
    return dg.SkipReason("Nothing to do")

