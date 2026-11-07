import sys
p=sys.argv[1]
s=open(p).read()
s=s.replace("Player player = mob.level().getNearestPlayer(mob, 24.0);","if (Boolean.getBoolean(\"towntest.watched\")) return true;\n\t\tPlayer player = mob.level().getNearestPlayer(mob, 24.0);",1)
s=s.replace("	private void arrive() {","	public static int forced, climbs;\n\n	private void arrive() {\n		forced++;",1)
s=s.replace("	private boolean climbOut() {\n","	private boolean climbOut() {\n		climbs++;\n",1)
open(p,'w').write(s)
