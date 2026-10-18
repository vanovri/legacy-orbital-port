C     1960S LEGACY FORTRAN ORBITAL / BALLISTIC RK4 SOLVER
C     USES GLOBAL COMMON BLOCKS, IMPLICIT TYPING, AND ARITHMETIC GOTO
      PROGRAM ORBIT66
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      COMMON /PARAM/ GM, DT, NSTEPS
      COMMON /STATE/ X, Y, VX, VY
      
      GM = 3.986004418D14
      DT = 1.0D0
      NSTEPS = 1000
      
C     INITIAL LEO STATE (METERS AND M/S)
      X = 6.778137D6
      Y = 0.0D0
      VX = 0.0D0
      VY = 7.6686D3
      
      I = 0
   10 IF (I .GE. NSTEPS) GOTO 20
      CALL RK4STP
      I = I + 1
      GOTO 10
      
   20 WRITE(*,100) X, Y, VX, VY
  100 FORMAT(4(E22.15, 1X))
      STOP
      END

      SUBROUTINE ACCEL(PX, PY, AX, AY)
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      COMMON /PARAM/ GM, DT, NSTEPS
      R2 = PX*PX + PY*PY
      R3 = R2 * DSQRT(R2)
      AX = -GM * PX / R3
      AY = -GM * PY / R3
      RETURN
      END

      SUBROUTINE RK4STP
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      COMMON /PARAM/ GM, DT, NSTEPS
      COMMON /STATE/ X, Y, VX, VY
      
      CALL ACCEL(X, Y, AX1, AY1)
      K1X = VX
      K1Y = VY
      K1VX = AX1
      K1VY = AY1
      
      CALL ACCEL(X + 0.5D0*DT*K1X, Y + 0.5D0*DT*K1Y, AX2, AY2)
      K2X = VX + 0.5D0*DT*K1VX
      K2Y = VY + 0.5D0*DT*K1VY
      K2VX = AX2
      K2VY = AY2
      
      CALL ACCEL(X + 0.5D0*DT*K2X, Y + 0.5D0*DT*K2Y, AX3, AY3)
      K3X = VX + 0.5D0*DT*K2VX
      K3Y = VY + 0.5D0*DT*K2VY
      K3VX = AX3
      K3VY = AY3
      
      CALL ACCEL(X + DT*K3X, Y + DT*K3Y, AX4, AY4)
      K4X = VX + DT*K3VX
      K4Y = VY + DT*K3VY
      K4VX = AX4
      K4VY = AY4
      
      X  = X  + (DT/6.0D0)*(K1X  + 2.0D0*K2X  + 2.0D0*K3X  + K4X)
      Y  = Y  + (DT/6.0D0)*(K1Y  + 2.0D0*K2Y  + 2.0D0*K3Y  + K4Y)
      VX = VX + (DT/6.0D0)*(K1VX + 2.0D0*K2VX + 2.0D0*K3VX + K4VX)
      VY = VY + (DT/6.0D0)*(K1VY + 2.0D0*K2VY + 2.0D0*K3VY + K4VY)
      RETURN
      END
