(CNC Regtangle Test File)

G21                            (Units in MM) 
G90                                     (Absolute positioning)
G94                                     (Units per minute feed rate mode)

G01 F200                 (Move to starting position)
G01 Z10
G00 X-1 Y1
M03 S10000.0                    (Start motor)
G01 Z1.0                                (Move to dwell height)

G01 F60                (Approach material)
G01 Z0.0
G01 F120.0                      (Draw rectangle)
G01 X21
G01 Y-21
G01 X-1
G01 Y1

G01 F200
G01 Z10                 (Exit material)
M05                                     (Stop motor)
(Test complete, EOF)

