public void robotInit {
	NetworkTableInstance inst = NetworkTableInstance.getDefault();
	NetworkTable table = inst.getTable("Shuffleboard")
	rotationFirst = table.getEntry("rot1")
	forwardDrive = table.getEntry("fwd")
	rotationSecond = table.getEntry("rot2")
}