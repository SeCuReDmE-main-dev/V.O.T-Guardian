from e2b import Sandbox

sb = Sandbox.create("vot-guardian-cpu-min")
try:
    attrs = dir(sb)
    print("HAS process:", hasattr(sb, "process"))
    print("HAS commands:", hasattr(sb, "commands"))
    print("HAS exec:", hasattr(sb, "exec"))
    print("HAS run:", hasattr(sb, "run"))
    print("ATTRS:", [a for a in attrs if not a.startswith("_")][:100])
finally:
    sb.kill()
