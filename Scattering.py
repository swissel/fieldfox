import pyvisa as visa

rm = visa.ResourceManager("/home/radio/keysight/iolibs/libktvisa32.so")

sa = rm.get_instrument("TCPIP0::169.254.24.71::inst0::INSTR")

# works within the NA program
s11 = sa.write("CALC:PAR:DEF S21")
s12 = sa.write("CALC:PAR:DEF S12")
s21 = sa.write("CALC:PAR:DEF S21")
s22 = sa.write("CALC:PAR:DEF S22")
print(f"s11: {s11}, s12: {s12}, s21: {s21}, s22: {s22}")
